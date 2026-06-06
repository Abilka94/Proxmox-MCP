# Phase 1B — Task Domain Design

**Date:** 2026-06-06
**Status:** Design approved — Phase 1B.1 implementation ready

---

## 1. Как устроены задачи Proxmox

Proxmox VE выполняет длительные операции (создание VM, миграция, бэкап, удаление) как **асинхронные задачи**. При запуске такой операции API немедленно возвращает UPID — строковый идентификатор задачи. Клиент может:

- отслеживать статус выполнения через отдельный endpoint;
- получать лог задачи построчно;
- ожидать завершения (polling);
- отменить задачу.

Жизненный цикл задачи:

```
Queued → Running → Stopped (OK | error | cancelled)
```

Ключевые поля состояния:

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | `"running"` или `"stopped"` | Текущее состояние |
| `exitstatus` | `"OK"` или строка ошибки | Заполнен после завершения |

---

## 2. Что такое UPID

**UPID** (Unique Process IDentifier) — строка вида:

```
UPID:{node}:{pid}:{pstart}:{starttime}:{type}:{uid}
```

Формат внутренний для Proxmox, не документирован как стабильный API.

**Для всех фаз UPID обрабатывается как opaque string.**
- Запрещается парсить формат UPID
- Запрещается модифицировать его
- Запрещается извлекать поля из строки UPID для бизнес-логики
- Все task_* инструменты возвращают UPID в исходном виде

Цель: сохранить совместимость с будущим Job Store и Operator Layer.

Пример из ответа API:

```
"UPID:pve:000B2E5A:01234567:6789ABCD:qemcreate:root@pam:"
```

---

## 3. API Endpoints

### Task List

```
GET /cluster/tasks?{filter}
```

Возвращает список активных и завершённых задач по всему кластеру.

Параметры фильтрации:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `source` | str | Фильтр по ноде |
| `user` | str | Фильтр по пользователю |
| `vmid` | int | Фильтр по VMID |
| `type` | str | Фильтр по типу задачи (например `qemcreate`, `vzdump`) |
| `status` | str | Фильтр по статусу (`running`, `stopped`) |
| `start` | int | Начальный timestamp |
| `limit` | int | Максимум записей (default 50, maximum 500) |

**Лимиты (ADR-0009):** `default_limit = 50`, `maximum_limit = 500`. Не допускается неограниченный запрос задач.

### Task Status

```
GET /cluster/tasks/{upid}/status
```

Возвращает `{ "status": "running" | "stopped", "exitstatus": "OK" | error }`.

**Fallback** (если cluster endpoint недоступен):

```
GET /nodes/{node}/tasks/{upid}/status
```

### Task Log

```
GET /nodes/{node}/tasks/{upid}/log?start={line}
```

Параметры:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `start` | int | Номер строки, начиная с которой возвращать лог (0-indexed) |

Формат ответа — массив объектов:

```json
[
  { "t": "TASK ERROR: something failed" },
  { "n": 42, "t": " [...] 100%" }
]
```

| Поле | Тип | Описание |
|------|-----|----------|
| `t` | str | Текст строки лога |
| `n` | int | Номер строки (опционально) |

### Task Cancel

```
POST /nodes/{node}/tasks/{upid}/status/stop
```

Отменяет выполняющуюся задачу. В Phase 1B не реализуется — зарезервировано для Phase 1C (mutate-операции).

---

## 4. Доступные данные

### Task List Entry

| Поле | Тип | PVE Field | Описание |
|------|-----|-----------|----------|
| `upid` | str | `upid` | Идентификатор задачи |
| `node` | str | `node` | Нода выполнения |
| `user` | str | `user` | Инициатор задачи |
| `type` | str | `type` | Тип операции |
| `status` | str | `status` | `running` / `stopped` |
| `exitstatus` | str \| None | `exitstatus` | `OK` / сообщение ошибки |
| `starttime` | int \| None | `starttime` | Unix timestamp старта |
| `endtime` | int \| None | `endtime` | Unix timestamp завершения |
| `id` | str \| None | `id` | Идентификатор ресурса (опционально) |

### Task Status

| Поле | Тип | PVE Field | Описание |
|------|-----|-----------|----------|
| `status` | str | `status` | `running` / `stopped` |
| `exitstatus` | str \| None | `exitstatus` | `OK` / сообщение ошибки |

### Task Log Entry

| Поле | Тип | PVE Field | Описание |
|------|-----|-----------|----------|
| `text` | str | `t` | Содержимое строки лога |
| `lineno` | int \| None | `n` | Номер строки |

---

## 5. Предлагаемые Pydantic модели

Все модели наследуют `PveResponseModel` (использует `extra="ignore"`), размещаются в `pve/models/responses.py`.

```python
class TaskListEntry(PveResponseModel):
    """A single task entry from /cluster/tasks."""
    upid: str
    node: str | None = None
    user: str | None = None
    type: str | None = None
    status: str | None = None          # "running" | "stopped"
    exitstatus: str | None = None      # "OK" | error message
    starttime: int | None = None
    endtime: int | None = None
    id: str | None = None


class TaskStatus(PveResponseModel):
    """Task execution status from /cluster/tasks/{upid}/status."""
    status: str                        # "running" | "stopped"
    exitstatus: str | None = None


class TaskLogEntry(PveResponseModel):
    """A single log line from /nodes/{node}/tasks/{upid}/log."""
    t: str                             # log line text (mapped to "text" in domain)
    n: int | None = None               # line number (optional)
```

---

## 6. Новый Domain: tasks

Структура:

```
src/mcp_proxmox/domains/tasks/
  ├── __init__.py          # Экспорт: task_list, task_status, task_log
  ├── service.py           # Функции домена
```

### Domain Service Functions (Phase 1B.1)

```python
# task_list — получить список задач с фильтрацией
async def task_list(
    client: PveClient,
    *,
    node: str | None = None,
    user: str | None = None,
    vmid: int | None = None,
    type_filter: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    """Return recent tasks across the cluster, with optional filters."""

# task_status — получить статус задачи по UPID
async def task_status(
    client: PveClient,
    upid: str,
    *,
    node: str | None = None,
) -> dict[str, object]:
    """Return status for a specific task."""

# task_log — получить лог задачи
async def task_log(
    client: PveClient,
    upid: str,
    node: str,
    *,
    start: int | None = None,
) -> dict[str, object]:
    """Return log lines for a specific task."""
```

### Domain Service Functions (Phase 1B.2 — отложено)

```python
# task_wait — дождаться завершения задачи (polling) — отложено
# task_follow — следить за логом задачи в реальном времени — отложено
# task_cancel / task_stop — отложено до Phase 1C
```

---

## 7. MCP Tools — Phase 1B.1 (Core — текущая реализация)

### `task_list`

| Свойство | Значение |
|----------|----------|
| **Tier** | READ |
| **Parameters** | `node` (opt), `user` (opt), `vmid` (opt), `type` (opt), `status` (opt), `limit` (opt, default 50, max 500) |
| **Response** | `{ "count": N, "tasks": [...] }` |
| **PVE endpoint** | `GET /cluster/tasks?limit={limit}&{filters}` |

### `task_status`

| Свойство | Значение |
|----------|----------|
| **Tier** | READ |
| **Parameters** | `upid` (req), `node` (opt) |
| **Response** | `{ "upid": "...", "status": "running", "exitstatus": null }` |
| **PVE endpoint** | `GET /cluster/tasks/{upid}/status` → fallback `GET /nodes/{node}/tasks/{upid}/status` |

### `task_log`

| Свойство | Значение |
|----------|----------|
| **Tier** | READ |
| **Parameters** | `upid` (req), `node` (req), `start` (opt, номер строки) |
| **Response** | `{ "upid": "...", "lines": [...], "total_lines": N, "truncated": false }` |
| **PVE endpoint** | `GET /nodes/{node}/tasks/{upid}/log?start={start}` |

---

## 8. MCP Tools — Phase 1B.2 (Extended — отложено)

### `task_wait`

| Свойство | Значение |
|----------|----------|
| **Tier** | READ (де-факто read-only: только GET-запросы) |
| **Parameters** | `upid` (req), `node` (opt), `timeout` (opt, default 300s), `poll_interval` (opt, default 1.0s) |
| **Response** | `{ "upid": "...", "status": "stopped", "exitstatus": "OK", "completed": true, "wait_seconds": 3.2 }` |

Алгоритм:

```
1. Запросить task_status (cluster → node fallback)
2. Если status == "stopped" — вернуть результат
3. Иначе — sleep(poll_interval), повторить
4. При превышении timeout — вернуть { "completed": false, "error": "timeout" }
```

### `task_follow`

| Свойство | Значение |
|----------|----------|
| **Tier** | READ |
| **Parameters** | `upid` (req), `node` (req), `timeout` (opt, default 300s), `poll_interval` (opt, default 0.5s) |
| **Response** | Сводка: статус, все строки лога, время ожидания |

Алгоритм:

```
1. Запросить task_status (cluster → node fallback)
2. Запросить task_log с start=0
3. Если status == "stopped" — вернуть { status, exitstatus, log_lines, ... }
4. Иначе — sleep(poll_interval)
5. Запросить task_log с start=last_line_number
6. Добавить новые строки к общему логу
7. Повторить
8. При timeout — вернуть частичный результат
```

**Важно:** `task_follow` не использует Server-Sent Events или WebSocket. Это polling-механизм, который возвращает единый ответ после завершения задачи или по таймауту. Клиент MCP получает полную запись лога и финальный статус одной JSON-RPC сессией.

---

## 9. Необходимые права токена

| Endpoint | Required Privilege |
|----------|-------------------|
| `GET /cluster/tasks` | `Sys.Audit` на `/` |
| `GET /cluster/tasks/{upid}/status` | `Sys.Audit` на `/` |
| `GET /nodes/{node}/tasks/{upid}/status` | `Sys.Audit` на `/` |
| `GET /nodes/{node}/tasks/{upid}/log` | `Sys.Audit` на `/` |

Все task-эндпоинты требуют того же уровня `Sys.Audit`, что и `node_status` / `network_list`.

**Рекомендуемая роль:** `PVEAuditor` (см. Phase 1A).

---

## 10. Совместимость PVE 8.x / 9.x

| Endpoint | PVE 8.x | PVE 9.x | Примечания |
|----------|---------|---------|------------|
| `GET /cluster/tasks` | ✅ Поддерживается | ✅ Поддерживается | Основной endpoint для списка задач |
| `GET /cluster/tasks/{upid}/status` | ✅ Поддерживается | ✅ Поддерживается | Cluster-level status |
| `GET /nodes/{node}/tasks/{upid}/status` | ✅ Поддерживается | ✅ Поддерживается | Node-level fallback |
| `GET /nodes/{node}/tasks/{upid}/log` | ✅ Поддерживается | ✅ Поддерживается | Лог задач |
| `POST /cluster/tasks/{upid}/status/stop` | ✅ Поддерживается | ✅ Поддерживается | Для Phase 1C |
| `POST /nodes/{node}/tasks/{upid}/status/stop` | ✅ Поддерживается | ✅ Поддерживается | Node-level cancel, для Phase 1C |

**Риск:** В некоторых версиях PVE 8.x `GET /cluster/tasks/{upid}/status` возвращает 400 на UPID, принадлежащих другой ноде. Для этого предусмотрен fallback на `GET /nodes/{node}/tasks/{upid}/status`. Этот fallback уже реализован в bsahane и должен быть повторён в нашем клиенте.

**Стратегия:**
1. Пытаемся `GET /cluster/tasks` для списка задач
2. Пытаемся `GET /cluster/tasks/{upid}/status` для статуса
3. При ошибке — fallback на `GET /nodes/{node}/tasks/{upid}/status`
4. Для лога — всегда `GET /nodes/{node}/tasks/{upid}/log`, так как cluster-level endpoint для лога не существует

---

## 11. Риски и ограничения

### Риски

| Риск | Описание | Митигация |
|------|----------|-----------|
| **UPID format change** | PVE может изменить внутренний формат UPID | UPID — opaque string, код не зависит от формата |
| **Cluster task status fails** | `GET /cluster/tasks/{upid}/status` может не работать для cross-node UPID | Fallback на node-level endpoint |
| **Task log очень большой** | Некоторые задачи (vzdump) генерируют тысячи строк лога | Параметр `start` + `limit`, клиент выбирает диапазон |
| **Polling latency** | `task_wait` / `task_follow` блокируют MCP-сервер на время ожидания | Использовать `asyncio.sleep()`, не блокировать event loop; разумный timeout по умолчанию (300s) |
| **Timeout в task_wait** | Нет механизма продолжить ожидание после таймаута | Клиент может вызвать `task_status` для последующей проверки |
| **MCP protocol — no server push** | MCP использует request-response, нельзя отправлять log lines по мере появления | `task_follow` возвращает полный результат одной сессией; альтернатива — polling через `task_log` с клиентской стороны |

### Ограничения

1. **Нет отмены задач** — `POST /nodes/{node}/tasks/{upid}/status/stop` зарезервирован для Phase 1C.
2. **Нет персистентности** — задачи не сохраняются в БД. После перезапуска MCP-сервера история задач доступна только через PVE API.
3. **Нет нотификаций** — MCP не поддерживает server push (SSE). `task_follow` — polling с единым ответом.
4. **Нет парсинга прогресса** — из лога можно извлечь проценты, но в v1 это не требуется.
5. **Лимит истории задач** — PVE хранит ограниченное количество завершённых задач. Старые записи автоматически удаляются.

---

## Architecture Diagram (Phase 1B.1)

```
MCP Tool Call
    │
    ▼
mcp/registry/tools.py
    │  task_list_tool, task_status_tool, task_log_tool
    ▼
domains/tasks/service.py
    │  task_list(), task_status(), task_log()
    ▼
pve/client/core.py
    │  get_tasks(), get_task_status(), get_task_log()
    │  (cluster + node fallback)
    │  limit enforcement (default=50, max=500)
    ▼
pve/models/responses.py
    │  TaskListEntry, TaskStatus, TaskLogEntry
    ▼
httpx → PVE API
```

---

## Summary

| Компонент | Статус |
|-----------|--------|
| Pydantic models (TaskListEntry, TaskStatus, TaskLogEntry) | Design complete — Phase 1B.1 |
| PVE client methods (get_tasks, get_task_status, get_task_log) | Design complete — Phase 1B.1 |
| Domain service (task_list, task_status, task_log) | Design complete — Phase 1B.1 |
| MCP tools v1 (task_list, task_status, task_log) | Design complete — Phase 1B.1 |
| MCP tools v2 (task_wait, task_follow) | Deferred to Phase 1B.2 |
| Task cancel (POST .../stop) | Deferred to Phase 1C |
| Job persistence (SQLite) | Deferred to Orchestrator Layer |
| Operator Mode | Out of scope |

---

## Iteration Strategy

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1B.1** | `get_tasks`, `get_task_status`, `get_task_log` + models + domain + 3 MCP tools | **Implementing now** |
| **Phase 1B.2** | `task_wait`, `task_follow` (polling-based) | Deferred — after live validation of 1B.1 |
| **Phase 1C** | Task cancel, mutate operations | Deferred |
