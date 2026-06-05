# ADR-0001: Язык реализации MCP-сервера

**Статус:** accepted  
**Дата:** 2026-06-03  
**Авторы:** команда MCP-Proxmox  
**Зависит от:** [ADR-0005](0005-ai-proxmox-operator-positioning.md)

## Контекст

Перед Phase 1A необходимо зафиксировать язык и toolchain. ARCHITECTURE §4 описывает структуру `src/` языко-агностично. Кандидаты: **Python 3.12+** и **TypeScript (Node 20+)**.

Критерии:

- официальная поддержка MCP (stdio);
- async HTTP к N нодам PVE;
- SQLite в Phase 2 (Knowledge);
- низкий time-to-MVP для OSS;
- contract/integration тесты.

## Решение

Принять **Python 3.12+** как язык реализации v1.

| Аспект | Выбор |
|--------|--------|
| Package layout | `src/mcp_proxmox/` (src layout) |
| Build | `pyproject.toml` (PEP 621), `hatchling` или `uv` |
| Typing | Pydantic v2 + mypy strict на `src/` |
| Async | `asyncio` + `httpx` |
| MCP | официальный Python SDK `mcp` |

## Обоснование

1. **Time-to-Phase-1A:** быстрый прототип stdio MCP и httpx fan-out.  
2. **Roadmap:** скрипты `generate_tool_catalog.py`, `validate_config.py` естественны в Python.  
3. **Phase 2 Memory:** SQLite — нативная экосистема.  
4. **OSS audience:** администраторы PVE часто знакомы с Python.  
5. **Архитектура не меняется:** границы модулей из ARCHITECTURE сохраняются.

## Отклонённая альтернатива: TypeScript

- Сильный MCP SDK и типизация.  
- Выше стоимость сборки/релиза; дублирование tooling для scripts.  
- Остаётся запасным вариантом только при блокере Python MCP SDK (на момент 2026-06 — не выявлен).

## Последствия

### Положительные

- Единый стек от 1A до Memory/traverse.  
- `pyproject.toml` как manifest зависимостей.

### Отрицательные

- GIL не критичен при I/O-bound PVE API.  
- Single-binary deploy сложнее, чем у Go — mitigated Docker.

### Нейтральные

- ADR-0002 (transport) остаётся независимым.

## Требования к репозиторию (при принятии)

- Python `>=3.12,<3.14`  
- `ruff` + `mypy` + `pytest` в dev  
- CI matrix: Linux (primary), optional Windows для dev

## Связанные документы

- [IMPLEMENTATION_PACKAGE.md](../implementation/IMPLEMENTATION_PACKAGE.md)  
- [IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md) — T-000, T-004

## Статус принятия

Принято для Phase 1A; T-000 закрыт.
