from __future__ import annotations

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings


class VSphereSettings(BaseSettings):
    model_config = {"env_prefix": "VSPHERE_"}

    host: str = "localhost"
    port: int = 443
    user: str = "administrator@vsphere.local"
    password: str = ""
    password_file: str = ""
    ignore_ssl: bool = False

    @model_validator(mode="after")
    def _load_password_file(self) -> "VSphereSettings":
        if self.password_file and not self.password:
            path = Path(self.password_file)
            if path.is_file():
                self.password = path.read_text().strip()
        return self
