# T104 Implementation Report

**Дата:** 2026-06-04  
**Задача:** T-104 — Minimal MCP stdio Server

## Созданные файлы

- `src/mcp_proxmox/mcp/registry/tools.py`
- `src/mcp_proxmox/mcp/handlers/server.py`
- `src/mcp_proxmox/mcp/transport/stdio.py`
- `tests/unit/test_mcp_server.py`

## Изменённые файлы

- `src/mcp_proxmox/__main__.py`
- `src/mcp_proxmox/mcp/registry/__init__.py`
- `src/mcp_proxmox/mcp/handlers/__init__.py`
- `src/mcp_proxmox/mcp/transport/__init__.py`

## Что реализовано

1. Минимальный запускаемый MCP-сервер.

- Entry point `python -m mcp_proxmox` больше не является bootstrap-заглушкой.
- Процесс читает MCP-сообщения из `stdio` с `Content-Length` framing.
- Процесс пишет JSON-RPC/MCP ответы обратно в `stdout`.

2. Принятый transport из ADR-0002.

- Реализован `stdio` transport.
- Использован LSP-style framing, совместимый с MCP over stdio.

3. Интеграция с существующими подсистемами.

- `config`: `__main__.py` загружает конфигурацию через `load_config()`.
- `logging`: сервер настраивает logging в `stderr`, чтобы не загрязнять protocol `stdout`.
- `policy`: `PolicyEngine` используется при `tools/call`.

4. Минимальный Tool Registry.

- Реализованы `ToolDefinition` и `ToolRegistry`.
- Реализован `create_default_registry(config)`.

5. Минимальный READ tool.

- Реализован `server_info`.
- Tool имеет tier `READ`.
- Tool доступен через `tools/list`.
- Tool вызывается через `tools/call`.

## Что именно умеет сервер

Реализованные методы:

- `initialize`
- `notifications/initialized`
- `ping`
- `tools/list`
- `tools/call`

Текущий tool:

- `server_info`

Возвращаемые данные `server_info`:

- `server_name`
- `server_version`
- `transport`
- `policy_mode`
- `connection_id`
- `available_tools`

## Что проверено

Проверено автоматическими тестами:

- direct handler tests для `initialize`, `tools/list`, `tools/call`
- subprocess test реального процесса `python -m mcp_proxmox`
- stdio framing и чтение нескольких запросов подряд

Текущий результат проверки:

- `unittest`: `16 tests OK`
- `compileall`: OK

Subprocess test подтверждает:

1. процесс стартует;
2. принимает `initialize`;
3. принимает `tools/list`;
4. принимает `tools/call` для `server_info`;
5. возвращает корректные MCP-совместимые ответы.

## Какие требования T-104 выполнены

| Требование | Статус | Комментарий |
|------------|--------|-------------|
| Минимальный запускаемый MCP-сервер | выполнено | есть рабочий stdio process |
| Использовать transport из ADR-0002 | выполнено | используется stdio |
| Интегрировать config | выполнено | config загружается при старте |
| Интегрировать logging | выполнено | logging уходит в stderr |
| Интегрировать policy | выполнено | policy применяется на tool call |
| Реализовать minimal Tool Registry | выполнено | registry и tool metadata есть |
| Реализовать хотя бы один READ tool | выполнено | `server_info` |

## Что осталось для T-105

T-105 — Session context:

- отдельный `session_id`
- явная session model
- actor placeholder
- connection/session context propagation через handlers
- формальное использование session context внутри MCP слоя, а не только correlation logging

Сейчас вместо этого есть только минимальный `correlation_id`, привязанный к request id.

## Что осталось для T-102

T-102 — PVE HTTP client:

- auth header для `PVEAPIToken`
- async HTTP client
- TLS / `verify_ssl`
- retry logic
- `PveApiError`
- базовые PVE models
- unit tests клиента

Сейчас `server_info` не ходит в Proxmox и не использует `pve/`.

## Ограничения текущей реализации

- Реализация сделана без внешнего `mcp` SDK, потому что он недоступен в текущем окружении.
- Реализован минимальный MCP subset, достаточный для первого рабочего stdio-процесса.
- Open WebUI compatibility не проверялась against live instance в этом окружении, но subprocess test подтверждает рабочий MCP stdio exchange.
