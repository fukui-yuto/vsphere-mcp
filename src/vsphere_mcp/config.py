from pydantic_settings import BaseSettings


class VSphereSettings(BaseSettings):
    model_config = {"env_prefix": "VSPHERE_"}

    host: str = "localhost"
    port: int = 443
    user: str = "administrator@vsphere.local"
    password: str = ""
    ignore_ssl: bool = False
