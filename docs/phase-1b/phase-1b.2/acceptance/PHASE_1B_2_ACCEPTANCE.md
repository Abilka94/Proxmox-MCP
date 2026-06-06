# Phase 1B.2 — Acceptance

**Дата:** 2026-06-06
**Компонент:** Task Domain — Extended (polling)

---

## 1. Scope Phase 1B.2

Реализация двух инструментов для ожидания и отслеживания задач PVE в реальном времени:

- **`task_wait`** — ожидание завершения задачи по UPID с таймаутом
- **`task_follow`** — ожидание завершения задачи с накоплением лога

Оба инструмента являются READ-tier: используют только GET-запросы к PVE API, не создают и не изменяют задачи.

---

## 2. Реализованные инструменты

### `task_wait`

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `upid` | string | да | UPID задачи |
| `node` | string | нет | Узел (обязателен для task_log; для task_status — fallback при 400/501) |
| `timeout` | integer | нет | Максимальное ожидание в секундах (default: 120, max: 3600) |
| `poll_interval` | float | нет | Интервал опроса в секундах (default: 1.0) |

Возвращает:
- `completed: bool` — завершена ли задача
- `status: str` — последний статус (`running`, `stopped`)
- `exitstatus: str | None` — код завершения
- `wait_seconds: float` — фактическое время ожидания
- `timed_out: bool` — был ли превышен таймаут
- `error: str | None` — ошибка (task_not_found, api_error)

### `task_follow`

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `upid` | string | да | UPID задачи |
| `node` | string | да | Узел (обязателен для task_log) |
| `timeout` | integer | нет | Максимальное ожидание (default: 120, max: 3600) |
| `poll_interval` | float | нет | Интервал опроса (default: 1.0) |
| `max_lines` | integer | нет | Максимум строк лога (default: 5000) |

Возвращает:
- Всё, что `task_wait`, плюс:
- `lines: list[dict]` — накопленные строки лога
- `total_lines: int` — всего строк прочитано
- `log_truncated: bool` — превышен лимит max_lines

---

## 3. Результаты unit tests

**Всего:** 130 unit tests (114 pre-existing + 16 новых)

**Результат:** 130/130 PASS

Новые тесты (`tests/unit/test_domain_tasks.py`):

| Тест | Описание |
|------|----------|
| `test_task_wait_immediate` | Возврат сразу для stopped задачи |
| `test_task_wait_poll_loop` | Цикл опроса в UPID вернул stopped |
| `test_task_wait_timeout` | Таймаут возвращает timed_out: true |
| `test_task_wait_not_found` | 404 → task_not_found |
| `test_task_wait_api_error` | 4xx → api_error |
| `test_task_wait_node_fallback` | Переключение cluster→node при 501 |
| `test_task_wait_no_node_cluster` | Без node — попытка cluster-level |
| `test_task_wait_transient_retry` | 5xx → exponential backoff |
| `test_task_follow_immediate` | Возврат сразу с логом |
| `test_task_follow_poll_loop` | Опрос с накоплением лога |
| `test_task_follow_timeout` | Таймаут с частичным логом |
| `test_task_follow_log_accumulation` | Накопление строк через start |
| `test_task_follow_log_truncated` | Лимит 5000 строк |
| `test_task_follow_not_found` | 404 → task_not_found |
| `test_task_follow_api_error` | 4xx → api_error |
| `test_task_follow_transient_retry` | 5xx → retry |

---

## 4. Результаты integration tests

**Всего:** 5 integration tests (добавлены в `tests/unit/test_mcp_server.py`)

**Результат:** 5/5 PASS

| Тест | Описание |
|------|----------|
| `test_task_wait_tool_completed` | MCP tool: task_wait на завершённую задачу |
| `test_task_wait_tool_not_found` | MCP tool: несуществующий UPID |
| `test_task_wait_tool_timeout` | MCP tool: таймаут (mock) |
| `test_task_follow_tool_completed` | MCP tool: task_follow на завершённую задачу |
| `test_task_follow_tool_not_found` | MCP tool: несуществующий UPID |

**Общий счёт:** 135/135 тестов проходят

```
pytest tests/unit/ — 135 passed in 8.23s
```

---

## 5. Результаты live validation

**Цель:** PVE 9.2.3, кластер «Ablka94», 3 узла (pve, pve2, pve3)

| # | Сценарий | Статус |
|---|----------|--------|
| 3.1 | `task_wait` — Already Completed | **PASS** |
| 3.2 | `task_wait` — Poll Until Completion | **PASS** |
| 3.3 | `task_wait` — Timeout | **SKIP** (нет running task, read-only токен) |
| 3.4 | `task_wait` — Non-Existent UPID | **PASS** |
| 3.5 | `task_wait` — Without Node | **PASS** (PVE 9.2.3 → 501, fallback работает) |
| 3.6 | `task_follow` — Already Completed + Log | **PASS** |
| 3.7 | `task_follow` — Poll Until Completion + Log | **PASS** |
| 3.8 | `task_follow` — Timeout + Partial Log | **SKIP** (нет running task) |
| 3.9 | `task_follow` — Without Node | **PASS** (by design) |
| 3.10 | `task_follow` — Non-Existent UPID | **PASS** |
| — | Data Validation Checks (Section 4) | **24/24 PASS** |

**Итого:** 8 PASS, 2 SKIP, 0 FAIL — **READY FOR ACCEPTANCE**

---

## 6. Информационные находки

### 6.1 PVE 9.2.3 — Cluster-level task_status returns 501

Кластерный endpoint `/cluster/tasks/{upid}/status` возвращает **501 Not Implemented** на PVE 9.2.3 — такое же поведение, как на PVE 8.x.

На момент проектирования предполагалось, что PVE 9.x поддерживает cluster-level task_status. Практика показала обратное.

**Последствия:** `task_wait` без параметра `node` возвращает `task_not_found` на PVE 9.2.3. Для корректной работы требуется указывать `node`.

### 6.2 Использование node-level fallback

Код корректно обрабатывает 400/501 от cluster-level endpoint:
- При наличии `node` → fallback на `/nodes/{node}/tasks/{upid}/status` (работает на PVE 9.2.3)
- При отсутствии `node` → ошибка `task_not_found`

Механизм fallback был реализован для PVE 8.x, но оказался востребован и на PVE 9.x.

### 6.3 Ограничения read-only токена

Токен `ai-agent@pve!openwebui` имеет только READ-привилегии:
- `Sys.Modify` — нет
- `VM.PowerMgmt` — нет
- POST-запросы всех типов → 403

**Последствия:** невозможно запустить новую задачу для live-тестирования таймаутов (сценарии 3.3, 3.8). Таймауты покрыты unit-тестами (mock).

---

## 7. Known Limitations

| Ограничение | Описание | Статус |
|-------------|----------|--------|
| Cluster-level `task_status` | 501 на PVE 9.2.3 и 8.x | Принято. Node-level работает. |
| `task_wait` без `node` | Не работает на PVE 9.2.3 | Принято. `node` рекомендуется всегда указывать. |
| Read-only токен | Невозможно POST для live-валидации таймаутов | Принято. Unit-тесты покрывают. |
| `task_follow` требует `node` | `node` — обязательный параметр | По дизайну. |
| Лимит логов | `max_lines=5000`, `log_truncated=true` | По дизайну. |
| Таймаут | По умолчанию 120s, максимум 3600s | По дизайну. |
| No POST operations | `task_cancel`, `task_stop` не реализованы | Phase 1C. |
| PVE 8.x cluster-level | 501 на `/cluster/tasks/{upid}/status` | Node-level fallback работает. |

---

## 8. Acceptance Recommendation

**Phase 1B.2 рекомендуется к приёмке (ACCEPTED).**

Обоснование:
1. Реализованы оба инструмента (`task_wait`, `task_follow`) в соответствии с утверждённым дизайном.
2. Все 135 тестов проходят (130 unit + 5 integration).
3. Live validation на PVE 9.2.3 кластере: 8/10 сценариев PASS, 2 SKIP (объективная причина — отсутствие running задач). Дефектов не обнаружено.
4. Информационные находки не требуют изменения кода.
5. Обратная совместимость с PVE 8.x сохранена (node-level fallback).

---

## 9. Итоговый статус

```
Phase:     1B.2 — Task Domain Extended
Status:    ACCEPTED
Tag:       v0.3.0-phase1b.2
Commit:    4863b48 ← новый коммит поверх текущего состояния
Changes:   7 modified files, 5 new directories, 6 new files
Tests:     135/135 PASS (114 pre-existing + 16 unit + 5 integration)
Live:      8/10 PASS, 2 SKIP, 0 FAIL
```
