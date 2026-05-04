# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2025-05-04

### Added

#### Information Retrieval Tools (read-only, no confirmation required)
- `list_vms` - List all virtual machines with optional host/cluster filter
- `get_vm_info` - Get detailed VM information (CPU, memory, disks, NICs, storage)
- `list_hosts` - List all ESXi hosts with optional cluster filter
- `get_host_info` - Get detailed ESXi host information
- `list_datacenters` - List all datacenters
- `list_clusters` - List all clusters with optional datacenter filter
- `list_datastores` - List all datastores with capacity info
- `list_networks` - List all networks (port groups)
- `list_snapshots` - List all snapshots for a VM (tree structure)
- `get_cluster_health` - Get cluster health summary with host details
- `search_vms` - Search VMs by name (case-insensitive)

#### Operation Tools (confirmation required)
- `power_on_vm` - Power on a VM (low risk)
- `power_off_vm` - Force power off a VM (medium risk)
- `shutdown_vm` - Graceful guest OS shutdown (medium risk)
- `reboot_vm` - Guest OS reboot (medium risk)
- `create_snapshot` - Create a VM snapshot (medium risk)
- `revert_snapshot` - Revert to a named snapshot (high risk)
- `remove_snapshot` - Remove a snapshot (high risk)
- `migrate_vm` - vMotion to another host (high risk)
- `delete_vm` - Permanently delete a VM (critical risk)

#### Infrastructure
- MCP server with stdio transport (FastMCP)
- Lazy-initialized vSphere connection client
- PropertyCollector-based efficient property retrieval
- `require_confirm` decorator for destructive operation safety
- Environment variable configuration (pydantic-settings)
- Structured JSON logging (structlog)
- vcsim Docker Compose for local development
- GitHub Actions CI with vcsim
- 22 automated tests
