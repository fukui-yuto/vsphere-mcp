from __future__ import annotations

import ssl

from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim

from vsphere_mcp.config import VSphereSettings
from vsphere_mcp.logging import get_logger

logger = get_logger(__name__)


class VSphereClient:
    """Lazy-initialized vSphere connection client."""

    def __init__(self, settings: VSphereSettings) -> None:
        self._settings = settings
        self._si: vim.ServiceInstance | None = None

    @property
    def si(self) -> vim.ServiceInstance:
        if self._si is None:
            self._connect()
        return self._si  # type: ignore[return-value]

    @property
    def content(self) -> vim.ServiceInstanceContent:
        return self.si.RetrieveContent()

    def _connect(self) -> None:
        logger.info("connecting_to_vsphere", host=self._settings.host, port=self._settings.port)
        ssl_context = None
        if self._settings.ignore_ssl:
            ssl_context = ssl._create_unverified_context()
        self._si = SmartConnect(
            host=self._settings.host,
            user=self._settings.user,
            pwd=self._settings.password,
            port=self._settings.port,
            sslContext=ssl_context,
        )
        logger.info("connected_to_vsphere", server=self.content.about.fullName)

    def disconnect(self) -> None:
        if self._si is not None:
            Disconnect(self._si)
            self._si = None

    def get_container_view(self, obj_type: list[type], root: vim.ManagedEntity | None = None) -> vim.view.ContainerView:
        root_folder = root if root is not None else self.content.rootFolder
        return self.content.viewManager.CreateContainerView(root_folder, obj_type, recursive=True)

    def find_vm_by_name(self, name: str) -> vim.VirtualMachine | None:
        view = self.get_container_view([vim.VirtualMachine])
        try:
            for vm in view.view:
                if vm.name == name:
                    return vm
        finally:
            view.Destroy()
        return None

    def find_host_by_name(self, name: str) -> vim.HostSystem | None:
        view = self.get_container_view([vim.HostSystem])
        try:
            for host in view.view:
                if host.name == name:
                    return host
        finally:
            view.Destroy()
        return None
