# vsphere-mcp

MCP (Model Context Protocol) server for VMware vSphere / vCenter operations.

Operate your vSphere infrastructure from Claude Code using natural language.

> **Note**: All development and testing is performed against [vcsim](https://github.com/vmware/govmomi/tree/main/vcsim) (vCenter Server Simulator). No commercial vSphere environment is required or affected.

## Features

- **list_vms** - List all virtual machines (filter by host/cluster)
- **get_vm_info** - Get detailed VM information (CPU, memory, disks, NICs, storage)
- **list_hosts** - List all ESXi hosts (filter by cluster)

More tools coming soon (power operations, snapshots, vMotion, etc.)

## Quick Start

### 1. Start vcsim

```bash
docker compose up -d
```

### 2. Install

```bash
uv pip install -e .
```

### 3. Register with Claude Code

```bash
claude mcp add --transport stdio vsphere-mcp \
  --env VSPHERE_HOST=localhost \
  --env VSPHERE_PORT=8989 \
  --env VSPHERE_USER=user \
  --env VSPHERE_PASSWORD=pass \
  --env VSPHERE_IGNORE_SSL=true \
  -- uv run vsphere-mcp
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VSPHERE_HOST` | `localhost` | vCenter/ESXi hostname |
| `VSPHERE_PORT` | `443` | API port |
| `VSPHERE_USER` | `administrator@vsphere.local` | Username |
| `VSPHERE_PASSWORD` | (empty) | Password |
| `VSPHERE_IGNORE_SSL` | `false` | Skip SSL certificate verification |

## Development

### Run tests (requires vcsim running)

```bash
docker compose up -d
uv run pytest -v
```

### Lint

```bash
uv run ruff check src/ tests/
```

## License

Apache License 2.0
