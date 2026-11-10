# Phase 1C Implementation Report

> Дата: 2026-06-06
> Статус: Реализация завершена (ожидает Validation)
> Версия: v1.0

## Состав изменений

### Изменённые файлы

| Файл | Изменение |
|---|---|
| `src/mcp_proxmox/pve/client/core.py` | Добавлен `_post_json()` — универсальный POST-метод для PVE API |
| `src/mcp_proxmox/domains/tasks/service.py` | Добавлена `task_cancel()` — доменная функция отмены задачи |
| `src/mcp_proxmox/domains/tasks/__init__.py` | Экспортирован `task_cancel` |
| `src/mcp_proxmox/mcp/registry/tools.py` | Зарегистрирован MCP tool `task_cancel` |
| `tests/unit/test_pve_client.py` | Добавлены unit-тесты `_post_json()` (6 тестов) |
| `tests/unit/test_domain_tasks.py` | Добавлены unit-тесты `task_cancel` (7 тестов) |
| `tests/unit/test_mcp_server.py` | Добавлены server-тесты `task_cancel` (1 тест + `_post_json` в FakePveClient) |
| `src/mcp_proxmox/mcp/handlers/server.py` | Исправлен баг логирования (KeyError при `PolicyDenied`) |

### Созданные файлы

| Файл | Описание |
|---|---|
| `docs/phase-1c/implementation/PHASE_1C_IMPLEMENTATION_REPORT.md` | Настоящий отчёт |

---

## PveClient._post_json()

**Сигнатура:**

```python
async def _post_json(self, path: str, data: dict[str, Any] | None = None) -> Any:
```

**Описание:** Универсальный POST-метод для PVE API. Реализован по аналогии с `_get_json()`, но использует `POST` вместо `GET`. Предназначен для всех будущих mutate-операций.

**Обработка ошибок:**
- HTTP 4xx/5xx → `PveApiError` с status_code и текстом ответа
- Transport error → `PveApiError` с деталями
- Timeout → `PveApiError`
- Отсутствие `data` в ответе → `PveApiError`
- Audit-логирование через `self._logger.info("pve_post", ...)`

**Параметр `data`:** опциональный dict для form-данных. В текущей реализации task_cancel не использует данные, но метод готов к будущим POST-запросам с телом.

---

## task_cancel()

**Сигнатура:**

```python
async def task_cancel(
    client: PveClient,
    upid: str,
    *,
    node: str,
    wait: bool = False,
    timeout: int = 120,
    poll_interval: float = 1.0,
) -> dict[str, object]:
```

**Логика работы:**

1. Проверить статус задачи через `client.get_task_status(upid, node=node)`
2. Если статус `"stopped"` → вернуть `cancel_requested: false, message: "Задача уже завершена"`
3. Отправить `POST /nodes/{node}/tasks/{upid}/status/stop`
4. Если `wait=false` → вернуть `cancel_requested: true, stopped: false`
5. Если `wait=true` → вызвать `task_wait()` и маппировать ответ

**API endpoint:** `POST /api2/json/nodes/{node}/tasks/{upid}/status/stop` (UPID URL-encoded)

**Response shapes:**

| Режим | cancel_requested | stopped | message |
|---|---|---|---|
| wait=false | true | false | "Запрос на остановку задачи отправлен" |
| wait=true (успех) | true | true | "Задача остановлена" |
| wait=true (таймаут) | true | false | "Задача не остановилась за {timeout} сек" |
| Завершена | false | false | "Задача уже завершена" |

---

## MCP Tool: task_cancel

**Tool name:** `task_cancel`

**Tier:** `ToolTier.OPERATOR`

**Input schema:**
- `upid` (string, required)
- `node` (string, required)
- `wait` (boolean, optional, default: false)
- `timeout` (integer, optional, default: 120)
- `poll_interval` (number, optional, default: 1.0)

**Description:** `"Request cancellation of a running task by UPID. Sends stop signal to the PVE task scheduler. Use wait=true to block until the task actually stops."`

---

## Reference Solutions

### Заимствовано

| Решение | Источник |
|---|---|
| `POST /nodes/{node}/tasks/{upid}/status/stop` | RekklesNA |
| Флаг `cancel_requested` в ответе | RekklesNA (концептуально) |
| Параметр `wait` (опционально) | bsahane (концептуально) |
| Возврат UPID + status | bsahane |

### Отклонено

| Решение | Причина |
|---|---|
| JobStore | Scope Phase 1C не включает |
| proxmoxer | Архитектурное решение — httpx |
| `require_confirm()` | Оператор лейер — отдельная фаза |

### Отличия от reference

| Аспект | Reference | MCP-Proxmox |
|---|---|---|
| Асинхронность | sync | async |
| HTTP клиент | proxmoxer | httpx |
| Проверка перед отменой | только в JobStore | GET статуса перед POST |
| Тип ошибок | JobConflictError / bare | PveApiError с status_code |
| Таргет PVE | 8.x | 9.x (primary) |

---

## Тестирование

### Количество тестов

| Компонент | До Phase 1C | После Phase 1C | Добавлено |
|---|---|---|---|
| client (`test_pve_client.py`) | 23 | 29 | 6 |
| task domain (`test_domain_tasks.py`) | 12 | 19 | 7 |
| server (`test_mcp_server.py`) | 38 | 39 | 1 |
| **Итого** | **140** | **149** | **9** |

(Числа не включают тесты config, policy, logging и т.д.)

### Покрытие _post_json()

- [x] Успешный POST, возврат data
- [x] Передача form-data
- [x] Auth header
- [x] HTTP ошибка → PveApiError
- [x] Transport error → PveApiError
- [x] Отсутствие data → PveApiError

### Покрытие task_cancel

- [x] wait=false — немедленный ответ
- [x] wait=true — ожидание до остановки
- [x] Уже завершённая задача
- [x] Таймаут ожидания
- [x] Ошибка API при POST
- [x] Повторная отмена (уже завершена)
- [x] Передача node в get_task_status

### Не покрыто тестами

- Live validation на реальном кластере PVE (требуется отдельный план)
- PVE 8.x совместимость (нет кластера)
- Проверка прав доступа (Sys.Modify) — только live

---

## Ограничения реализации

1. **Нет JobStore** — отмена не отслеживается после возврата ответа. Повторный вызов для одной задачи приведёт к "уже завершена".
2. **Нет двухфазной модели** — `cancel_requested` возвращается только в ответе, не сохраняется между вызовами.
3. **API endpoint не верифицирован на PVE 9.2.3** — требуется live validation.
4. **Права доступа не проверены** — live validation покажет, достаточно ли `Sys.Modify`.
5. **PVE 8.x** — best effort, без гарантий.

---

## Готовность к Live Validation

- [x] Код реализован
- [x] Unit-тесты проходят (149/149)
- [x] Server-тесты проходят
- [x] PHASE_1C_LIVE_VALIDATION_PLAN.md — требуется создать
- [ ] Live validation выполнена
- [ ] Acceptance подписан

Следующий шаг: создание плана live validation и выполнение на PVE 9.2.3.
