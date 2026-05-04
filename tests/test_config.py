import os
from pathlib import Path

import pytest

from vsphere_mcp.config import VSphereSettings


@pytest.fixture(autouse=True)
def _clear_vsphere_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove all VSPHERE_* env vars so pydantic-settings doesn't pick them up."""
    for key in list(os.environ):
        if key.startswith("VSPHERE_"):
            monkeypatch.delenv(key)


class TestVSphereSettings:
    def test_defaults(self) -> None:
        settings = VSphereSettings(
            host="localhost",
            port=443,
            user="admin",
            password="test",
        )
        assert settings.host == "localhost"
        assert settings.port == 443
        assert settings.ignore_ssl is False

    def test_password_file(self, tmp_path: Path) -> None:
        pw_file = tmp_path / "password.txt"
        pw_file.write_text("secret-password\n")
        settings = VSphereSettings(
            host="localhost",
            password_file=str(pw_file),
        )
        assert settings.password == "secret-password"

    def test_password_file_not_found(self) -> None:
        with pytest.raises(Exception):
            VSphereSettings(
                host="localhost",
                password_file="/nonexistent/path/password.txt",
            )

    def test_password_takes_precedence(self, tmp_path: Path) -> None:
        pw_file = tmp_path / "password.txt"
        pw_file.write_text("file-password\n")
        settings = VSphereSettings(
            host="localhost",
            password="direct-password",
            password_file=str(pw_file),
        )
        assert settings.password == "direct-password"
