from mcp.server.fastmcp import FastMCP

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.config import VSphereSettings
from vsphere_mcp.logging import setup_logging
from vsphere_mcp.tools.inventory import register_inventory_tools
from vsphere_mcp.tools.lifecycle import register_lifecycle_tools
from vsphere_mcp.tools.migration import register_migration_tools
from vsphere_mcp.tools.power import register_power_tools
from vsphere_mcp.tools.snapshot import register_snapshot_tools

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


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
