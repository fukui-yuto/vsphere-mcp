import argparse

from mcp.server.fastmcp import FastMCP

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.config import VSphereSettings
from vsphere_mcp.logging import setup_logging
from vsphere_mcp.tools.advanced_settings import register_advanced_settings_tools
from vsphere_mcp.tools.alarm import register_alarm_tools
from vsphere_mcp.tools.batch import register_batch_tools
from vsphere_mcp.tools.cluster_config import register_cluster_config_tools
from vsphere_mcp.tools.content_library import register_content_library_tools
from vsphere_mcp.tools.customization import register_customization_tools
from vsphere_mcp.tools.datacenter import register_datacenter_tools
from vsphere_mcp.tools.datastore_browser import register_datastore_browser_tools
from vsphere_mcp.tools.events import register_event_tools
from vsphere_mcp.tools.folders import register_folder_tools
from vsphere_mcp.tools.guest import register_guest_tools
from vsphere_mcp.tools.host import register_host_tools
from vsphere_mcp.tools.host_config import register_host_config_tools
from vsphere_mcp.tools.inventory import register_inventory_tools
from vsphere_mcp.tools.lifecycle import register_lifecycle_tools
from vsphere_mcp.tools.migration import register_migration_tools
from vsphere_mcp.tools.networking import register_networking_tools
from vsphere_mcp.tools.performance import register_performance_tools
from vsphere_mcp.tools.power import register_power_tools
from vsphere_mcp.tools.resources import register_resource_tools
from vsphere_mcp.tools.snapshot import register_snapshot_tools
from vsphere_mcp.tools.storage import register_storage_tools
from vsphere_mcp.tools.tags import register_tag_tools
from vsphere_mcp.tools.vcenter_admin import register_vcenter_admin_tools
from vsphere_mcp.tools.vm_devices import register_vm_device_tools
from vsphere_mcp.tools.vsphere_tags import register_vsphere_tag_tools
from vsphere_mcp.tools.vapp import register_vapp_tools
from vsphere_mcp.tools.scheduled_tasks import register_scheduled_task_tools
from vsphere_mcp.tools.host_profile import register_host_profile_tools
from vsphere_mcp.tools.license import register_license_tools
from vsphere_mcp.tools.fault_tolerance import register_ft_tools
from vsphere_mcp.tools.vlcm import register_vlcm_tools
from vsphere_mcp.tools.encryption import register_encryption_tools
from vsphere_mcp.tools.ovf import register_ovf_tools
from vsphere_mcp.tools.content_library_ext import register_content_library_ext_tools
from vsphere_mcp.tools.vcenter_services import register_vcenter_services_tools
from vsphere_mcp.tools.nioc import register_nioc_tools
from vsphere_mcp.tools.instant_clone import register_instant_clone_tools
from vsphere_mcp.tools.pci_passthrough import register_pci_passthrough_tools
from vsphere_mcp.tools.dvs_advanced import register_dvs_advanced_tools
from vsphere_mcp.tools.iscsi_config import register_iscsi_config_tools
from vsphere_mcp.tools.tanzu import register_tanzu_tools
from vsphere_mcp.tools.vm_monitoring import register_vm_monitoring_tools
from vsphere_mcp.tools.datastore_ext import register_datastore_ext_tools
from vsphere_mcp.tools.storage_policy import register_storage_policy_tools
from vsphere_mcp.tools.vsan import register_vsan_tools
from vsphere_mcp.tools.certificate import register_certificate_tools

setup_logging()

settings = VSphereSettings()
client = VSphereClient(settings)

mcp = FastMCP(
    "vsphere-mcp",
    description="MCP server for VMware vSphere / vCenter operations",
)

register_inventory_tools(mcp, client)
register_power_tools(mcp, client)
register_snapshot_tools(mcp, client)
register_migration_tools(mcp, client)
register_lifecycle_tools(mcp, client)
register_resource_tools(mcp, client)
register_host_tools(mcp, client)
register_host_config_tools(mcp, client)
register_performance_tools(mcp, client)
register_event_tools(mcp, client)
register_storage_tools(mcp, client)
register_batch_tools(mcp, client)
register_guest_tools(mcp, client)
register_tag_tools(mcp, client)
register_advanced_settings_tools(mcp, client)
register_vcenter_admin_tools(mcp, client)
register_cluster_config_tools(mcp, client)
register_vm_device_tools(mcp, client)
register_folder_tools(mcp, client)
register_datastore_browser_tools(mcp, client)
register_networking_tools(mcp, client)
register_datacenter_tools(mcp, client)
register_customization_tools(mcp, client)
register_alarm_tools(mcp, client)
register_vsphere_tag_tools(mcp, client)
register_content_library_tools(mcp, client)
register_vapp_tools(mcp, client)
register_scheduled_task_tools(mcp, client)
register_host_profile_tools(mcp, client)
register_license_tools(mcp, client)
register_ft_tools(mcp, client)
register_vlcm_tools(mcp, client)
register_encryption_tools(mcp, client)
register_ovf_tools(mcp, client)
register_content_library_ext_tools(mcp, client)
register_vcenter_services_tools(mcp, client)
register_nioc_tools(mcp, client)
register_instant_clone_tools(mcp, client)
register_pci_passthrough_tools(mcp, client)
register_dvs_advanced_tools(mcp, client)
register_iscsi_config_tools(mcp, client)
register_tanzu_tools(mcp, client)
register_vm_monitoring_tools(mcp, client)
register_datastore_ext_tools(mcp, client)
register_storage_policy_tools(mcp, client)
register_vsan_tools(mcp, client)
register_certificate_tools(mcp, client)


def main() -> None:
    parser = argparse.ArgumentParser(description="vsphere-mcp server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Transport protocol")
    parser.add_argument("--port", type=int, default=8080, help="Port for SSE transport")
    parser.add_argument(
        "--metrics-port", type=int, default=None, help="Port for Prometheus metrics (disabled by default)"
    )
    args = parser.parse_args()

    if args.metrics_port:
        from vsphere_mcp.metrics import start_metrics_server

        start_metrics_server(args.metrics_port)

    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
