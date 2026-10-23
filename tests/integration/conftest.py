"""Shared fixtures for qhardcharger integration tests.

The Hardcharger server is started as a managed subprocess via the
[`hardcharger`](https://pypi.org/project/hardcharger/) PyPI package — no
Docker required. ``hardcharger.Server(...)`` auto-picks a free port so
the test server can coexist with a developer's local Hardcharger on the
default 31337/31338 without any port juggling.

Pure-Python tests (no QGIS, no native deps) live in ``tests/unit``;
this directory is exclusively for tests that talk to a real server.
"""

from __future__ import annotations

import datetime
import os
import sys
from pathlib import Path
from typing import Iterator

import pytest


HARDCHARGER_USERNAME = "hardcharger_user"
HARDCHARGER_PASSWORD = "hardcharger_password"


def _generate_self_signed_tls_cert(out_dir: Path) -> tuple[Path, Path]:
    """Mint a self-signed RSA cert + key for ``localhost`` so the
    Hardcharger test server's Warp SQL endpoint is reachable over
    ``grpc+tls://``."""
    from cryptography import x509  # noqa: PLC0415
    from cryptography.hazmat.primitives import hashes, serialization  # noqa: PLC0415
    from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: PLC0415
    from cryptography.x509.oid import NameOID  # noqa: PLC0415

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path = out_dir / "tls_cert.pem"
    key_path = out_dir / "tls_key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    return cert_path, key_path


@pytest.fixture(scope="session")
def hardcharger_server(tmp_path_factory) -> Iterator:
    """Start a Hardcharger server as a managed subprocess for the session."""
    hardcharger = pytest.importorskip(
        "hardcharger",
        reason="install `pip install hardcharger` to run integration tests",
    )

    tls_dir = tmp_path_factory.mktemp("tls")
    tls_dir.chmod(0o700)
    tls_cert, tls_key = _generate_self_signed_tls_cert(tls_dir)

    with hardcharger.Server(
        username=HARDCHARGER_USERNAME,
        password=HARDCHARGER_PASSWORD,
        tls_cert=tls_cert,
        tls_key=tls_key,
    ) as srv:
        yield srv


@pytest.fixture(scope="session")
def hardcharger_host(hardcharger_server) -> str:
    return hardcharger_server.host


@pytest.fixture(scope="session")
def hardcharger_port(hardcharger_server) -> int:
    return hardcharger_server.port


@pytest.fixture(scope="session")
def hardcharger_credentials() -> dict:
    """Username / password / TLS skip flag the test server is configured with."""
    return {
        "username": HARDCHARGER_USERNAME,
        "password": HARDCHARGER_PASSWORD,
        "tls_skip_verify": True,
    }


@pytest.fixture(scope="session")
def hardcharger_conn_config(
    hardcharger_host: str,
    hardcharger_port: int,
    hardcharger_credentials: dict,
):
    """A ready-to-use ``HardchargerConnConfig`` against the test server."""
    # Install qgis stubs before importing the wrapper (it pulls in qgis.core
    # at module top level, which won't exist on a CI box without QGIS).
    _tests_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if _tests_root not in sys.path:
        sys.path.insert(0, _tests_root)
    from _stubs import install as _install_stubs

    _install_stubs()

    from qhardcharger.provider.hardcharger_wrapper import HardchargerConnConfig

    return HardchargerConnConfig(
        host=hardcharger_host,
        port=hardcharger_port,
        use_tls=True,
        tls_skip_verify=hardcharger_credentials["tls_skip_verify"],
        username=hardcharger_credentials["username"],
        password=hardcharger_credentials["password"],
        auth_type="password",
    )
