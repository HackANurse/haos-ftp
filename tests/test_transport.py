"""Transport policy tests that do not require a Home Assistant installation."""

import importlib.util
import asyncio
import threading
from ftplib import error_perm
from pathlib import Path
from unittest.mock import patch

import pytest


SPEC = importlib.util.spec_from_file_location(
    "ftp_helpers", Path(__file__).parents[1] / "custom_components/ftp/helpers.py"
)
helpers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helpers)


class FakeFTP:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []

    def connect(self, host, port):
        self.calls.append(("connect", host, port))

    def auth(self):
        self.calls.append(("auth",))

    def prot_p(self):
        self.calls.append(("prot_p",))

    def login(self, username, password):
        self.calls.append(("login", username, password))

    def set_pasv(self, value):
        self.calls.append(("set_pasv", value))

    def close(self):
        self.calls.append(("close",))


def test_plain_active_uses_active_data_mode_and_charset():
    with patch.object(helpers, "FTP", FakeFTP):
        ftp = helpers.create_ftp(
            "example.org", 21, "user", "secret", "plain", "active", "latin-1", "1.2"
        )
    assert ftp.kwargs["encoding"] == "latin-1"
    assert ("set_pasv", False) in ftp.calls
    assert ("auth",) not in ftp.calls


@pytest.mark.parametrize("mode", ["explicit_required", "implicit"])
def test_required_tls_encrypts_control_and_data(mode):
    with (
        patch.object(helpers, "FTP_TLS", FakeFTP),
        patch.object(helpers, "ImplicitFTP_TLS", FakeFTP),
    ):
        ftp = helpers.create_ftp(
            "example.org", 21, "user", "secret", mode, "passive", "utf-8", "1.3"
        )
    assert ("prot_p",) in ftp.calls
    assert ("set_pasv", True) in ftp.calls
    assert (("auth",) in ftp.calls) is (mode == "explicit_required")
    assert ftp.kwargs["context"].minimum_version == helpers.ssl.TLSVersion.TLSv1_3


def test_optional_tls_does_not_fallback_on_certificate_failure():
    class BrokenFTP(FakeFTP):
        def auth(self):
            raise helpers.ssl.SSLCertVerificationError("untrusted")

    with patch.object(helpers, "FTP_TLS", BrokenFTP):
        with pytest.raises(helpers.ssl.SSLCertVerificationError):
            helpers.create_ftp(
                "example.org",
                21,
                "user",
                "secret",
                "explicit_optional",
                "passive",
                "utf-8",
                "1.2",
            )


def test_optional_tls_falls_back_only_when_auth_is_unsupported():
    class UnsupportedFTP(FakeFTP):
        def auth(self):
            raise error_perm("502 AUTH not implemented")

    with (
        patch.object(helpers, "FTP_TLS", UnsupportedFTP),
        patch.object(helpers, "FTP", FakeFTP),
    ):
        ftp = helpers.create_ftp(
            "example.org",
            21,
            "user",
            "secret",
            "explicit_optional",
            "passive",
            "utf-8",
            "1.2",
        )
    assert ("login", "user", "secret") in ftp.calls
    assert ("prot_p",) not in ftp.calls


def test_upload_reports_transferred_bytes():
    class Transport:
        def storbinary(self, command, file, blocksize, callback):
            assert command == "STOR /backup.tar"
            while block := file.read(blocksize):
                callback(block)

    reports = []

    async def run():
        async with helpers._UploadStream(
            Transport(), "/backup.tar", lambda **data: reports.append(data)
        ) as stream:
            await stream.write(b"a" * 5)
            await stream.write(b"b" * 7)

    asyncio.run(run())
    assert reports[-1] == {"bytes_uploaded": 12}


def test_upload_starts_before_the_source_stream_finishes():
    started = threading.Event()
    received = bytearray()

    class Transport:
        def storbinary(self, command, file, blocksize, callback):
            started.set()
            while block := file.read(blocksize):
                received.extend(block)
                callback(block)

    async def run():
        async with helpers._UploadStream(Transport(), "/backup.tar") as stream:
            await stream.write(b"first")
            assert started.is_set(), "FTP upload waited for the entire backup to be buffered"
            await stream.write(b"second")

    asyncio.run(run())
    assert received == b"firstsecond"


def test_upload_reports_transport_failure_while_source_is_streaming():
    class Transport:
        def storbinary(self, command, file, blocksize, callback):
            raise OSError("connection closed")

    async def run():
        async with helpers._UploadStream(Transport(), "/backup.tar") as stream:
            for _ in range(20):
                await stream.write(b"x" * 256)

    with pytest.raises(OSError, match="connection closed"):
        asyncio.run(asyncio.wait_for(run(), timeout=2))


def test_upload_allows_server_time_to_finalize_large_transfer():
    class Socket:
        def __init__(self):
            self.timeout = 30

        def gettimeout(self):
            return self.timeout

        def settimeout(self, value):
            self.timeout = value

    class Transport:
        def __init__(self):
            self.sock = Socket()

        def storbinary(self, command, file, blocksize, callback):
            while block := file.read(blocksize):
                callback(block)
            assert self.sock.gettimeout() == helpers.UPLOAD_RESPONSE_TIMEOUT

    transport = Transport()

    async def run():
        async with helpers._UploadStream(transport, "/backup.tar") as stream:
            await stream.write(b"backup data")

    asyncio.run(run())
    assert transport.sock.gettimeout() == 30


def test_compatibility_listing_uses_nlst():
    class Transport:
        def nlst(self, path):
            return ["/backups/example.metadata.json"]

        def mlsd(self, path):
            raise AssertionError("MLSD should not be used")

    connection = helpers.FtpConnection(
        helpers.FtpClient(None, "example.org", 21, "", "", compatibility_mode=True)
    )
    connection.ftp = Transport()
    paths = asyncio.run(connection.list("/backups"))
    assert str(paths[0][0]) == "/backups/example.metadata.json"


def test_custom_ca_and_client_certificate_are_loaded():
    class Context:
        check_hostname = True
        verify_mode = helpers.ssl.CERT_REQUIRED

        def __init__(self):
            self.calls = []

        def load_verify_locations(self, cafile):
            self.calls.append(("ca", cafile))

        def load_cert_chain(self, certfile, keyfile, password):
            self.calls.append(("client", certfile, keyfile, password))

    context = Context()
    with patch.object(helpers.ssl, "create_default_context", return_value=context):
        result = helpers.tls_context(
            "1.2",
            "/config/ssl/ca.pem",
            "/config/ssl/client.pem",
            "/config/ssl/client.key",
            "secret",
        )
    assert result is context
    assert context.calls == [
        ("ca", "/config/ssl/ca.pem"),
        ("client", "/config/ssl/client.pem", "/config/ssl/client.key", "secret"),
    ]
    assert context.check_hostname and context.verify_mode == helpers.ssl.CERT_REQUIRED


def test_client_certificate_requires_private_key():
    with pytest.raises(helpers.CertificateConfigurationError):
        helpers.tls_context("1.2", "", "/config/ssl/client.pem", "", "")


def test_certificate_files_are_not_allowed_with_plain_ftp():
    with pytest.raises(helpers.CertificateConfigurationError):
        helpers.create_ftp(
            "example.org",
            21,
            "user",
            "secret",
            "plain",
            "passive",
            "utf-8",
            "1.2",
            "/config/ssl/ca.pem",
        )


def test_optional_tls_with_custom_ca_never_downgrades_to_plain():
    class UnsupportedFTP(FakeFTP):
        def auth(self):
            raise error_perm("502 AUTH not implemented")

    with (
        patch.object(helpers, "FTP_TLS", UnsupportedFTP),
        patch.object(helpers, "tls_context", return_value=object()),
        patch.object(helpers, "FTP", FakeFTP),
    ):
        with pytest.raises(error_perm):
            helpers.create_ftp(
                "example.org",
                21,
                "user",
                "secret",
                "explicit_optional",
                "passive",
                "utf-8",
                "1.2",
                "/config/ssl/ca.pem",
            )


def test_default_context_verifies_server_certificate_and_hostname():
    context = helpers.tls_context("1.2")
    assert context.verify_mode == helpers.ssl.CERT_REQUIRED
    assert context.check_hostname


def test_explicit_ftps_uses_certificate_name_while_connecting_to_official_host():
    class HostAwareFTP(FakeFTP):
        def connect(self, host, port):
            self.connected_host = host
            self.host = host

        def auth(self):
            self.tls_host = self.host

    with patch.object(helpers, "FTP_TLS", HostAwareFTP):
        ftp = helpers.create_ftp(
            "ftp.example.org",
            21,
            "user",
            "secret",
            "explicit_required",
            "passive",
            "utf-8",
            "1.2",
            tls_server_name="backend.example.org",
        )
    assert ftp.connected_host == "ftp.example.org"
    assert ftp.tls_host == "backend.example.org"
    assert ftp.kwargs["context"].check_hostname


def test_tls_server_name_cannot_be_used_with_plain_ftp():
    with pytest.raises(helpers.CertificateConfigurationError):
        helpers.create_ftp(
            "ftp.example.org",
            21,
            "user",
            "secret",
            "plain",
            "passive",
            "utf-8",
            "1.2",
            tls_server_name="backend.example.org",
        )


def test_missing_ca_file_is_a_certificate_configuration_error():
    with pytest.raises(helpers.CertificateConfigurationError):
        helpers.tls_context("1.2", "/config/ssl/missing-ca-for-test.pem")
