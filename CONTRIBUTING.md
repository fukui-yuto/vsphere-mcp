# Contributing to vsphere-mcp

Thank you for your interest in contributing to vsphere-mcp!

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker (for vcsim)

### Getting Started

1. Clone the repository:

```bash
git clone https://github.com/fukui-yuto/vsphere-mcp.git
cd vsphere-mcp
```

2. Start vcsim (vCenter Server Simulator):

```bash
docker compose up -d
```

3. Create a virtual environment and install dependencies:

```bash
uv venv
uv pip install -e .
uv pip install pytest pytest-asyncio ruff mypy
```

4. Run the tests:

```bash
uv run pytest tests/ -v
```

## Project Structure

```
src/vsphere_mcp/
  server.py           # MCP server entry point
  config.py           # Settings via environment variables
  client.py           # vSphere connection client (lazy-init)
  logging.py          # Structured logging (structlog)
  tools/
    _base.py          # require_confirm decorator
    inventory.py      # Read-only tools (list_*, get_*, search_*)
    power.py          # Power operations (on/off/shutdown/reboot)
    snapshot.py       # Snapshot management (create/revert/remove)
    migration.py      # vMotion
    lifecycle.py      # VM delete
  utils/
    property_collector.py  # Efficient vSphere property retrieval
tests/
  conftest.py         # vcsim connection fixture
  test_*.py           # Test modules
```

## Adding a New Tool

1. Decide the category: inventory (read-only) or operation (destructive).

2. For **read-only tools**, add to `tools/inventory.py`:
   - Define property constants (e.g., `MY_NEW_PROPS = [...]`)
   - Create a formatter function (e.g., `_format_my_object(data)`)
   - Register the tool inside `register_inventory_tools()`

3. For **destructive tools**, add to the appropriate module or create a new one:
   - Use the `@require_confirm(danger_level="...")` decorator
   - Danger levels: `low`, `medium`, `high`, `critical`
   - Use `_find_vm_with_props()` from `power.py` for VM lookups

4. Register in `server.py` if creating a new module.

5. Write tests in `tests/test_*.py`.

## Code Style

- **Formatter/Linter**: [ruff](https://docs.astral.sh/ruff/)
- **Type Checking**: mypy (strict mode)
- Line length: 120 characters

```bash
# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/

# Type check
uv run mypy src/
```

## Testing Guidelines

- All tests run against vcsim (no real vCenter required)
- Use PropertyCollector (`collect_properties`) for retrieving vSphere objects
- Direct property access on managed object references does not work with vcsim; always use PropertyCollector
- Test classes should be scoped per module with shared fixtures

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation only
- `test:` adding/updating tests
- `refactor:` code change that neither fixes a bug nor adds a feature
- `chore:` build process or auxiliary tool changes

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all tests pass and linting is clean
4. Open a PR with a clear description

## Reporting Issues

Please use [GitHub Issues](https://github.com/fukui-yuto/vsphere-mcp/issues) and include:

- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- vcsim or real vCenter (and version)
