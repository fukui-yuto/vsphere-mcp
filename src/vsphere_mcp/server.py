import argparse

from mcp.server.fastmcp import FastMCP

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.config import VSphereSettings
from vsphere_mcp.logging import setup_logging
from vsphere_mcp.tools.advanced_settings import register_advanced_settings_tools
from vsphere_mcp.tools.batch import register_batch_tools
from vsphere_mcp.tools.cluster_config import register_cluster_config_tools
from vsphere_mcp.tools.datastore_browser import register_datastore_browser_tools
from vsphere_mcp.tools.events import register_event_tools
from vsphere_mcp.tools.folders import register_folder_tools
from vsphere_mcp.tools.guest import register_guest_tools
from vsphere_mcp.tools.host import register_host_tools
from vsphere_mcp.tools.host_config import register_host_config_tools
from vsphere_mcp.tools.inventory import register_inventory_tools
from vsphere_mcp.tools.lifecycle import register_lifecycle_tools
from vsphere_mcp.tools.migration import register_migration_tools
from vsphere_mcp.tools.performance import register_performance_tools
from vsphere_mcp.tools.power import register_power_tools
from vsphere_mcp.tools.resources import register_resource_tools
from vsphere_mcp.tools.snapshot import register_snapshot_tools
from vsphere_mcp.tools.storage import register_storage_tools
from vsphere_mcp.tools.tags import register_tag_tools
from vsphere_mcp.tools.vcenter_admin import register_vcenter_admin_tools
from vsphere_mcp.tools.vm_devices import register_vm_device_tools

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
