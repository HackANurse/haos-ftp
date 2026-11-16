"""Transport policy tests that do not require a Home Assistant installation."""

import importlib.util
import asyncio
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
