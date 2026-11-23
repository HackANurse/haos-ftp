"""FTP and FTPS transport for backup files."""

from __future__ import annotations

import asyncio
import socket
import ssl
import tempfile
from ftplib import FTP, FTP_TLS, all_errors, error_perm
from functools import partial
from pathlib import Path, PurePosixPath

CHUNK_SIZE = 256 * 1024


class CertificateConfigurationError(OSError):
    """The configured certificate files cannot be used."""


class ImplicitFTP_TLS(FTP_TLS):
    """Negotiate TLS before reading the FTP welcome message."""

    def __init__(self, *args, tls_server_name="", **kwargs):
        super().__init__(*args, **kwargs)
        self.tls_server_name = tls_server_name

    def connect(self, host="", port=0, timeout=-999, source_address=None):
        if host:
            self.host = host
        if port:
            self.port = port
        if timeout != -999:
            self.timeout = timeout
        if source_address is not None:
            self.source_address = source_address
        self.sock = socket.create_connection(
            (self.host, self.port), self.timeout, source_address=self.source_address
        )
        self.sock = self.context.wrap_socket(
            self.sock, server_hostname=self.tls_server_name or self.host
        )
        if self.tls_server_name:
            self.host = self.tls_server_name
        self.af = self.sock.family
        self.file = self.sock.makefile("r", encoding=self.encoding)
        self.welcome = self.getresp()
        return self.welcome

    def auth(self):
        return None


def tls_context(
    version: str,
    ca_file: str = "",
    client_cert: str = "",
    client_key: str = "",
    client_key_password: str = "",
) -> ssl.SSLContext:
    if bool(client_cert) != bool(client_key):
        raise CertificateConfigurationError(
            "Client certificate and private key must both be configured"
        )
    if client_key_password and not client_key:
        raise CertificateConfigurationError(
            "A private key is required when a key password is configured"
        )
    for filename in (ca_file, client_cert, client_key):
        if filename and not Path(filename).is_absolute():
            raise CertificateConfigurationError("Certificate paths must be absolute")
    context = ssl.create_default_context()
    versions = {"1.2": ssl.TLSVersion.TLSv1_2, "1.3": ssl.TLSVersion.TLSv1_3}
    context.minimum_version = versions[version]
    try:
        if ca_file:
            context.load_verify_locations(cafile=ca_file)
        if client_cert:
            context.load_cert_chain(
                certfile=client_cert,
                keyfile=client_key,
                password=client_key_password or None,
            )
    except (OSError, ssl.SSLError) as err:
        raise CertificateConfigurationError(
            "Could not load the configured TLS certificate files"
        ) from err
    return context


def create_ftp(
    host: str,
    port: int,
    username: str,
    password: str,
    protocol: str,
    transfer_mode: str,
    charset: str,
    tls_version: str,
    ca_file: str = "",
    client_cert: str = "",
    client_key: str = "",
    client_key_password: str = "",
    tls_server_name: str = "",
):
    """Open a connection and apply the chosen security and transfer settings."""
    if protocol not in {"plain", "explicit_optional", "explicit_required", "implicit"}:
        raise ValueError(f"Unsupported protocol: {protocol}")
    if transfer_mode not in {"passive", "active"}:
        raise ValueError(f"Unsupported transfer mode: {transfer_mode}")
    if protocol == "plain" and any(
        (ca_file, client_cert, client_key, client_key_password, tls_server_name)
    ):
        raise CertificateConfigurationError("Certificate settings require an FTPS protocol")
    cls = ImplicitFTP_TLS if protocol == "implicit" else FTP if protocol == "plain" else FTP_TLS
    kwargs = {"timeout": 30, "encoding": charset}
    if cls is not FTP:
        kwargs["context"] = tls_context(
            tls_version, ca_file, client_cert, client_key, client_key_password
        )
    if protocol == "implicit":
        kwargs["tls_server_name"] = tls_server_name
    ftp = cls(**kwargs)
    try:
        ftp.connect(host, port)
        if tls_server_name and protocol != "implicit":
            ftp.host = tls_server_name
        protected = protocol == "implicit"
        if protocol in {"explicit_optional", "explicit_required"}:
            try:
                ftp.auth()
                protected = True
            except error_perm as err:
                if (
                    protocol != "explicit_optional"
                    or any((ca_file, client_cert, client_key, client_key_password, tls_server_name))
                    or not str(err).startswith(("500", "502", "504"))
                ):
                    raise
                ftp.close()
                ftp = FTP(timeout=30, encoding=charset)
                ftp.connect(host, port)
        ftp.login(username or "anonymous", password or "")
        if protected:
            ftp.prot_p()
        ftp.set_pasv(transfer_mode == "passive")
        return ftp
    except Exception:
        ftp.close()
        raise


class FtpConnection:
    def __init__(self, client: "FtpClient"):
        self.config = client
        self.ftp = None

    async def __aenter__(self):
        c = self.config
        self.ftp = await asyncio.to_thread(
            create_ftp,
            c.host,
            c.port,
            c.username,
            c.password,
            c.protocol,
            c.transfer_mode,
            c.charset,
            c.tls_version,
            c.ca_file,
            c.client_cert,
            c.client_key,
            c.client_key_password,
            c.tls_server_name,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.ftp:
            try:
                await asyncio.to_thread(self.ftp.quit)
            except all_errors:
                self.ftp.close()
            self.ftp = None

    async def is_dir(self, path: str) -> bool:
        def check():
            original = self.ftp.pwd()
            try:
                self.ftp.cwd(path)
                return True
            except all_errors:
                return False
            finally:
                self.ftp.cwd(original)

        return await asyncio.to_thread(check)

    async def exists(self, path: str) -> bool:
        if await self.is_dir(path):
            return True
        try:
            return await asyncio.to_thread(self.ftp.size, path) is not None
        except all_errors:
            return False

    async def make_directory(self, path: str) -> bool:
        await asyncio.to_thread(self.ftp.mkd, path)
        return True

    async def list(self, path: str):
        def listing():
            if self.config.compatibility_mode:
                names = self.ftp.nlst(path)
            else:
                names = [name for name, _ in self.ftp.mlsd(path)]
            return [(PurePosixPath(path) / PurePosixPath(name).name, {}) for name in names]

        return await asyncio.to_thread(listing)

    async def remove(self, path: str):
        await asyncio.to_thread(self.ftp.delete, path)

    def upload_stream(self, path: str, on_progress=None):
        return _UploadStream(self.ftp, path, on_progress)

    def download_stream(self, path: str):
        return _DownloadStream(self.ftp, path)


class _UploadStream:
    def __init__(self, ftp, path, on_progress=None):
        self.ftp, self.path = ftp, path
        self.on_progress = on_progress

    async def __aenter__(self):
        self.loop = asyncio.get_running_loop()
        self.blocks = asyncio.Queue(maxsize=8)
        self.started = asyncio.Event()

        class Reader:
            def __init__(reader_self):
                reader_self.pending = b""

            def read(reader_self, size):
                while not reader_self.pending:
                    block = asyncio.run_coroutine_threadsafe(self.blocks.get(), self.loop).result()
                    if block is None:
                        return b""
                    reader_self.pending = block
                result, reader_self.pending = (
                    reader_self.pending[:size],
                    reader_self.pending[size:],
                )
                return result

        def upload():
            self.loop.call_soon_threadsafe(self.started.set)
            count = 0

            def progress(block):
                nonlocal count
                count += len(block)
                if self.on_progress:
                    self.loop.call_soon_threadsafe(partial(self.on_progress, bytes_uploaded=count))

            self.ftp.storbinary(f"STOR {self.path}", Reader(), CHUNK_SIZE, progress)

        self.task = asyncio.create_task(asyncio.to_thread(upload))
        await self.started.wait()
        return self

    async def write(self, block: bytes):
        if self.task.done():
            await self.task
        pending_put = asyncio.create_task(self.blocks.put(block))
        done, _ = await asyncio.wait((pending_put, self.task), return_when=asyncio.FIRST_COMPLETED)
        if self.task in done:
            pending_put.cancel()
            await self.task
            raise OSError("FTP upload stopped before the backup stream finished")
        await pending_put

    async def __aexit__(self, exc_type, exc, tb):
        if not self.task.done():
            await self.blocks.put(None)
        if exc_type is None:
            await self.task
        else:
            try:
                await self.task
            except Exception:
                pass


class _DownloadStream:
    def __init__(self, ftp, path):
        self.ftp, self.path = ftp, path

    async def __aenter__(self):
        self.file = tempfile.TemporaryFile()
        try:
            await asyncio.to_thread(self.ftp.retrbinary, f"RETR {self.path}", self.file.write)
            await asyncio.to_thread(self.file.seek, 0)
        except Exception:
            self.file.close()
            raise
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.file.close()

    async def read(self):
        return await asyncio.to_thread(self.file.read)

    async def iter_by_block(self):
        while block := await asyncio.to_thread(self.file.read, CHUNK_SIZE):
            yield block


class FtpClient:
    def __init__(
        self,
        hass,
        host,
        port,
        username,
        password,
        protocol="plain",
        transfer_mode="passive",
        charset="utf-8",
        compatibility_mode=False,
        tls_version="1.2",
        ca_file="",
        client_cert="",
        client_key="",
        client_key_password="",
        tls_server_name="",
    ):
        self.hass, self.host, self.port = hass, host, int(port)
        self.username, self.password = username, password
        self.protocol, self.transfer_mode = protocol, transfer_mode
        self.charset, self.compatibility_mode = charset, compatibility_mode
        self.tls_version = tls_version
        self.ca_file = ca_file
        self.client_cert = client_cert
        self.client_key = client_key
        self.client_key_password = client_key_password
        self.tls_server_name = tls_server_name

    def connect(self) -> FtpConnection:
        return FtpConnection(self)

    def __str__(self):
        return f"{self.username}@{self.host}:{self.port}"


async def async_ensure_path_exists(client: FtpConnection, path: str) -> bool:
    """Create each missing directory in the remote path."""
    if await client.is_dir(path):
        return True
    current = "/" if path.startswith("/") else ""
    for part in PurePosixPath(path).parts:
        if part == "/":
            continue
        current = str(PurePosixPath(current) / part)
        if await client.exists(current):
            if not await client.is_dir(current):
                return False
        else:
            await client.make_directory(current)
    return True
