from __future__ import annotations

import ssl
import time

from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim, vmodl

from vsphere_mcp.config import VSphereSettings
from vsphere_mcp.logging import get_logger

logger = get_logger(__name__)

MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_DELAY_SEC = 2


class VSphereConnectionError(Exception):
    """Raised when connection to vSphere fails."""


class VSphereAuthenticationError(VSphereConnectionError):
    """Raised when authentication to vSphere fails."""


class VSphereSSLError(VSphereConnectionError):
    """Raised when SSL certificate verification fails."""


class VSphereClient:
    """Lazy-initialized vSphere connection client with auto-reconnect."""

    def __init__(self, settings: VSphereSettings) -> None:
        self._settings = settings
        self._si: vim.ServiceInstance | None = None

    @property
    def si(self) -> vim.ServiceInstance:
        if self._si is None:
            self._connect()
        elif not self._is_connected():
            logger.info("session_expired_reconnecting")
            self._reconnect()
        return self._si  # type: ignore[return-value]

    @property
    def content(self) -> vim.ServiceInstanceContent:
        return self.si.RetrieveContent()

    def _is_connected(self) -> bool:
        try:
            self._si.RetrieveContent()  # type: ignore[union-attr]
            return True
        except Exception:
            return False

    def _connect(self) -> None:
        logger.info("connecting_to_vsphere", host=self._settings.host, port=self._settings.port)
        ssl_context = None
        if self._settings.ignore_ssl:
            ssl_context = ssl._create_unverified_context()
        try:
            self._si = SmartConnect(
                host=self._settings.host,
                user=self._settings.user,
                pwd=self._settings.password,
                port=self._settings.port,
                sslContext=ssl_context,
            )
        except vim.fault.InvalidLogin as e:
            raise VSphereAuthenticationError(
                f"Authentication failed for user '{self._settings.user}' "
                f"on {self._settings.host}:{self._settings.port}: {e.msg}"
            ) from e
        except ssl.SSLError as e:
            raise VSphereSSLError(
                f"SSL certificate verification failed for {self._settings.host}:{self._settings.port}. "
                f"Set VSPHERE_IGNORE_SSL=true for self-signed certificates: {e}"
            ) from e
        except (OSError, ConnectionRefusedError, TimeoutError) as e:
            raise VSphereConnectionError(
                f"Cannot reach vSphere at {self._settings.host}:{self._settings.port}: {e}"
            ) from e
        except vmodl.MethodFault as e:
            raise VSphereConnectionError(f"vSphere API error during connection: {e.msg}") from e
        logger.info("connected_to_vsphere", server=self.content.about.fullName)

    def _reconnect(self) -> None:
        for attempt in range(1, MAX_RECONNECT_ATTEMPTS + 1):
            try:
                self.disconnect()
                self._connect()
                return
            except VSphereConnectionError:
                if attempt == MAX_RECONNECT_ATTEMPTS:
                    raise
                logger.warning(
                    "reconnect_failed_retrying",
                    attempt=attempt,
                    max_attempts=MAX_RECONNECT_ATTEMPTS,
                )
                time.sleep(RECONNECT_DELAY_SEC)

    def disconnect(self) -> None:
        if self._si is not None:
            try:
                Disconnect(self._si)
            except Exception:
                pass
            self._si = None

    def get_container_view(self, obj_type: list[type], root: vim.ManagedEntity | None = None) -> vim.view.ContainerView:
        root_folder = root if root is not None else self.content.rootFolder
        return self.content.viewManager.CreateContainerView(root_folder, obj_type, recursive=True)
