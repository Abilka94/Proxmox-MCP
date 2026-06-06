# MCP-Proxmox

AI Infrastructure Operator for Proxmox VE, exposed as a Model Context Protocol
(MCP) server.

Status: local Phase 1A bootstrap. The project skeleton is in place; runtime
MCP tools are implemented in later Phase 1A tasks.

## Documentation

- [Documentation index](docs/README.md)
- [Architecture](docs/architecture/ARCHITECTURE.md)
- [Phase 1A reports](docs/phase-1a/reports/)

## Development

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m mypy src
```

The first runnable MCP stdio server lands in T-104 after config, policy, and
registry scaffolding are implemented.
