# vsphere-mcp

MCP (Model Context Protocol) server for VMware vSphere / vCenter operations.

Operate your vSphere infrastructure from Claude Code using natural language.

> **Note**: All development and testing is performed against [vcsim](https://github.com/vmware/govmomi/tree/main/vcsim) (vCenter Server Simulator). No commercial vSphere environment is required or affected.

## Features

### Information Retrieval (12 tools, read-only)

| Tool | Description |
|---|---|
| `test_connection` | Test vSphere connection and return server info |
| `list_vms` | List all VMs (filter by host/cluster, pagination with limit/offset) |
| `get_vm_info` | Detailed VM info (CPU, memory, disks, NICs, storage, tools) |
| `list_hosts` | List ESXi hosts (filter by cluster) |
| `get_host_info` | Detailed ESXi host info |
| `list_datacenters` | List all datacenters |
| `list_clusters` | List clusters (filter by datacenter) |
| `list_datastores` | List datastores with capacity/usage |
| `list_networks` | List networks (port groups) |
| `list_snapshots` | List VM snapshots (tree structure) |
| `get_cluster_health` | Cluster health summary with host details |
| `search_vms` | Search VMs by name (case-insensitive) |

### Operations (16 tools, confirmation required)

All destructive operations require `confirm=True` to execute. Without it, the tool returns a confirmation prompt with the danger level.

| Tool | Description | Danger Level |
|---|---|---|
| `power_on_vm` | Power on a VM | Low |
| `power_off_vm` | Force power off (hard stop) | Medium |
| `shutdown_vm` | Graceful guest OS shutdown | Medium |
| `reboot_vm` | Guest OS reboot | Medium |
| `create_snapshot` | Create VM snapshot | Medium |
| `set_vm_resources` | Change CPU and/or memory | Medium |
| `add_disk` | Add a new virtual disk | Medium |
| `add_nic` | Add a new network adapter | Medium |
| `revert_snapshot` | Revert to a snapshot | High |
| `remove_snapshot` | Delete a snapshot | High |
| `migrate_vm` | vMotion to another host | High |
| `clone_vm` | Clone an existing VM | High |
| `deploy_from_template` | Deploy a new VM from a template | High |
| `enter_maintenance_mode` | Put ESXi host into maintenance mode | High |
| `exit_maintenance_mode` | Take ESXi host out of maintenance mode | High |
| `delete_vm` | Permanently delete a VM | Critical |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended)
- Docker (for local development with vcsim)

### 1. Start vcsim (for development)

```bash
docker compose up -d
```

This starts a vCenter Server Simulator on port 8989 with pre-provisioned datacenters, clusters, hosts, VMs, and datastores.

### 2. Install

```bash
# From PyPI (when published)
uv pip install vsphere-mcp

# From source
git clone https://github.com/fukui-yuto/vsphere-mcp.git
cd vsphere-mcp
uv venv
uv pip install -e .
```

### 3. Register with Claude Code

#### For local development (vcsim)

```bash
claude mcp add --transport stdio vsphere-mcp \
  --env VSPHERE_HOST=localhost \
  --env VSPHERE_PORT=8989 \
  --env VSPHERE_USER=user \
  --env VSPHERE_PASSWORD=pass \
  --env VSPHERE_IGNORE_SSL=true \
  -- uv run vsphere-mcp
```

#### For production vCenter

```bash
claude mcp add --transport stdio vsphere-mcp \
  --env VSPHERE_HOST=vcenter.example.com \
  --env VSPHERE_PORT=443 \
  --env VSPHERE_USER=administrator@vsphere.local \
  --env VSPHERE_PASSWORD=your-password \
  -- uv run vsphere-mcp
```

#### Using a password file (recommended for production)

```bash
claude mcp add --transport stdio vsphere-mcp \
  --env VSPHERE_HOST=vcenter.example.com \
  --env VSPHERE_PORT=443 \
  --env VSPHERE_USER=administrator@vsphere.local \
  --env VSPHERE_PASSWORD_FILE=/run/secrets/vsphere_password \
  -- uv run vsphere-mcp
```

### 4. Use from Claude Code

Once registered, you can use natural language:

```
> Show me all VMs in the cluster

> What's the status of VM "web-server-01"?

> Power on the VM "dev-test-01" (confirm=True)

> List all datastores and their free space

> Create a snapshot of "db-server" called "before-upgrade"

> Clone "web-01" as "web-01-staging"

> Add a 50GB disk to "app-server"
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VSPHERE_HOST` | `localhost` | vCenter/ESXi hostname or IP |
| `VSPHERE_PORT` | `443` | vSphere API port |
| `VSPHERE_USER` | `administrator@vsphere.local` | Username |
| `VSPHERE_PASSWORD` | (empty) | Password |
| `VSPHERE_PASSWORD_FILE` | (empty) | Path to a file containing the password (alternative to `VSPHERE_PASSWORD`) |
| `VSPHERE_IGNORE_SSL` | `false` | Skip SSL certificate verification |

### SSL Configuration

SSL certificate verification is **enabled by default**. For self-signed certificates or development environments:

```bash
export VSPHERE_IGNORE_SSL=true
```

> **Warning**: Never disable SSL verification in production environments.

## Safety Design

### Confirmation System

All destructive operations use a two-step confirmation pattern:

1. **First call** (without `confirm=True`): Returns a preview with danger level
2. **Second call** (with `confirm=True`): Actually executes the operation

```
# First call - returns confirmation prompt
power_off_vm(vm_name="web-01")
# -> {"status": "confirmation_required", "danger_level": "medium", ...}

# Second call - executes
power_off_vm(vm_name="web-01", confirm=True)
# -> {"status": "success", "vm_name": "web-01", "operation": "power_off"}
```

### Danger Levels

| Level | Description | Examples |
|---|---|---|
| **Low** | Easily reversible | Power on |
| **Medium** | May cause brief disruption | Power off, shutdown, reboot, create snapshot, set resources, add disk/NIC |
| **High** | Significant impact, hard to reverse | Revert/remove snapshot, vMotion, clone, deploy from template, maintenance mode |
| **Critical** | Permanent data loss possible | Delete VM |

### Logging

All operations are logged in structured JSON format:

```json
{"event": "power_off_vm", "vm_name": "web-01", "level": "info", "timestamp": "2025-05-04T12:00:00Z"}
```

Credentials are never included in logs.

## Error Handling

Connection errors are classified into specific exception types for clear diagnostics:

| Error Type | Cause | Example Message |
|---|---|---|
| `VSphereAuthenticationError` | Invalid username or password | `Authentication failed for user 'admin' on vcenter:443` |
| `VSphereSSLError` | SSL certificate verification failure | `SSL certificate verification failed ... Set VSPHERE_IGNORE_SSL=true` |
| `VSphereConnectionError` | Host unreachable or connection refused | `Cannot reach vSphere at vcenter:443` |

The client automatically retries on transient connection failures (up to 3 attempts with a 2-second delay).

## Development

### Run tests (requires vcsim)

```bash
docker compose up -d
uv run pytest tests/ -v
```

### Lint and format

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

### Project structure

```
vsphere-mcp/
  pyproject.toml
  docker-compose.yml           # vcsim for local dev
  src/vsphere_mcp/
    server.py                  # MCP server entry point
    config.py                  # Environment variable settings
    client.py                  # vSphere connection (lazy-init, auto-reconnect)
    logging.py                 # Structured logging
    tools/
      _base.py                 # require_confirm / handle_tool_errors decorators
      inventory.py             # Read-only tools (12 tools)
      power.py                 # Power operations (4 tools)
      snapshot.py              # Snapshot management (3 tools)
      migration.py             # vMotion (1 tool)
      lifecycle.py             # VM clone / deploy / delete (3 tools)
      resources.py             # VM resource changes: CPU, memory, disk, NIC (3 tools)
      host.py                  # Host maintenance mode (2 tools)
    utils/
      property_collector.py    # Efficient vSphere property retrieval
  tests/                       # Integration tests against vcsim
  docs/
    CONTRIBUTING.md
    SECURITY.md
    CHANGELOG.md
  .github/workflows/ci.yml    # GitHub Actions CI
```

## Architecture

```
Claude Code
    |  stdio (default) or HTTP/SSE
    v
vsphere-mcp server (Python, FastMCP)
    |  pyVmomi (HTTPS)
    v
vCenter Server (production) or vcsim (development)
```

- **Transport**: stdio (default, simplest for local use) or SSE (for multi-client setups)
- **Connection**: Lazy-initialized on first tool call, auto-reconnect on session expiry
- **Property retrieval**: PropertyCollector for efficient batch queries
- **Safety**: All destructive operations gated by `require_confirm` decorator with danger levels
- **Error handling**: Typed exceptions (`VSphereAuthenticationError`, `VSphereSSLError`, `VSphereConnectionError`)

## Known Limitations

- **vcsim vs real vCenter**: Some API behaviors differ between vcsim and production vCenter. See [vcsim documentation](https://github.com/vmware/govmomi/tree/main/vcsim) for details.
- **Guest operations**: `shutdown_vm` and `reboot_vm` require VMware Tools installed in the guest OS.
- **vMotion**: Requires compatible hosts, shared storage, and proper networking in production.

## License

[Apache License 2.0](LICENSE)

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for development setup and guidelines.

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for security policy and reporting vulnerabilities.

## Changelog

See [docs/CHANGELOG.md](docs/CHANGELOG.md) for release history.
