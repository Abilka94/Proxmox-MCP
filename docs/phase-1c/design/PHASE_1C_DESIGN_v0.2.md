# Phase 1C Design: Task Mutation

> Дата: 2026-06-06
> Статус: На ревью (доработан)
> Версия: v0.2-draft

## Цель

Реализовать возможность остановки запущенных задач PVE по UPID (task mutation) — первый mutate-инструмент в проекте.

---

## Scope

**Включает:**

1. POST-метод в `PveClient` (фундамент для всех будущих mutate-операций)
2. MCP tool `task_cancel` — остановка задачи по UPID
3. Проверку статуса задачи перед отменой (защита от повторной отмены)
4. Опциональный параметр `wait` — ожидание завершения после отмены

**Не включает:**

- JobStore (полноценная реализация — отдельная фаза)
- Двухфазную модель отмены (cancel_requested → cancelled)
- Stale UPID detection
- Retry-логику
- Изменение существующих read-only инструментов

---

## API Design

### PveClient: POST-метод

```python
class PveClient:
    async def _post_json(
        self,
        endpoint: str,
        data: dict | None = None,
    ) -> dict:
        ...
```

**Аргументы:**

| Параметр | Тип | Описание |
|---|---|---|
| `endpoint` | str | Путь API (например, `/nodes/{node}/tasks/{upid}/status/stop`) |
| `data` | dict | Данные формы (опционально) |

**Ошибки:**

| Условие | Исключение |
|---|---|
| HTTP 400 | `PveError("PVE API вернул ошибку: ...")` |
| HTTP 401/403 | `PveError("Недостаточно прав: ...")` |
| HTTP 404 | `PveError("Ресурс не найден: ...")` |
| HTTP 5xx | `PveError("Ошибка сервера PVE: ...")` |
| Таймаут | `PveError("Таймаут соединения с PVE API")` |

### MCP Tool: task_cancel

**Tool name:** `task_cancel`

**Arguments:**

| Аргумент | Тип | Обязательный | По умолчанию | Описание |
|---|---|---|---|---|
| `upid` | string | + | — | UPID задачи для остановки |
| `node` | string | + | — | Нода, на которой выполняется задача |
| `wait` | bool | - | false | Ожидать остановки задачи |
| `timeout` | int | - | 120 | Таймаут ожидания (сек) |
| `poll` | float | - | 1.0 | Интервал опроса статуса (сек) |

**Output (wait=false):**

```json
{
  "upid": "UPID:node:...",
  "node": "node-name",
  "status": "running",
  "cancel_requested": true,
  "stopped": false,
  "message": "Запрос на остановку задачи отправлен"
}
```

**Output (wait=true, задача остановлена):**

```json
{
  "upid": "UPID:node:...",
  "node": "node-name",
  "status": "stopped",
  "cancel_requested": true,
  "stopped": true,
  "message": "Задача остановлена"
}
```

**Output (wait=true, таймаут):**

```json
{
  "upid": "UPID:node:...",
  "node": "node-name",
  "status": "running",
  "cancel_requested": true,
  "stopped": false,
  "message": "Задача не остановилась за 120 сек"
}
```

**Output (задача уже завершена):**

```json
{
  "upid": "UPID:node:...",
  "node": "node-name",
  "cancel_requested": false,
  "stopped": false,
  "message": "Задача уже завершена"
}
```

**Логика работы:**

1. Проверить, что задача существует (GET статуса)
2. Если задача уже в терминальном статусе — вернуть `cancel_requested: false` с сообщением
3. Отправить POST на остановку задачи
4. Если `wait=true` — вызвать `task_wait` с заданными timeout/poll
5. Вернуть результат

---

## Sequence: task_cancel (wait=true)

```
Client                  MCP Server                  PVE API
  |                          |                          |
  |-- task_cancel(upid, ---->|                          |
  |    node, wait=true)      |                          |
  |                          |-- GET /nodes/{node}/ ---->|
  |                          |    tasks/{upid}/status   |
  |                          |<-- {status: "running"} ---|
  |                          |                          |
  |                          |-- POST /nodes/{node}/ --->|
  |                          |    tasks/{upid}/status/  |
  |                          |    stop                  |
  |                          |<-- {data: null} ---------|
  |                          |                          |
  |                          |-- GET /nodes/{node}/ ---->|   (poll loop)
  |                          |    tasks/{upid}/status   |
  |                          |<-- {status: "stopped"} ---|
  |                          |                          |
  |<-- {upid, status, -------|                          |
  |     stopped: true}       |                          |
```

---

## Файловая структура изменений

```
src/
└── proxmox_mcp/
    ├── client.py            # + _post_json()
    ├── tools/
    │   └── task.py          # + task_cancel handler
    └── server.py            # регистрация task_cancel (если не автоматическая)
```

---

## Обработка ошибок

| Ситуация | Поведение |
|---|---|
| UPID не найден (404) | `PveError: "Задача с указанным UPID не найдена"` |
| Задача уже завершена | Возврат `cancel_requested: false, reason: "already_completed"` |
| Нет прав (401/403) | `PveError: "Недостаточно прав для остановки задачи"` |
| PVE API недоступен | `PveError: "PVE API не отвечает"` |
| Таймаут ожидания | `PveError: "Задача не остановилась за {timeout} сек"` (timeout=120) |

---

## Безопасность

- Tool требует аутентификации (через существующий PveClient)
- Token должен иметь привилегию `Sys.Modify` на `/nodes/{node}/tasks/{upid}`
- Опасная операция — рекомендуется ToolTier.OPERATOR (не PUBLIC)
- Audit-логирование через существующий механизм

---

## Единые значения timeout и poll

| Параметр | Phase 1B.2 (task_wait) | Phase 1C Design (v0.1) | Phase 1C Design (v0.2) | Обоснование |
|---|---|---|---|---|
| `timeout` | 120 | 300 | **120** | Значение приведено к единому стандарту проекта. 120 сек более чем достаточно для остановки задачи PVE — процесс завершается за секунды. Больший таймаут не даёт преимуществ, но увеличивает время ожидания при сбоях. |
| `poll` | 1.0 | 2.0 | **1.0** | Значение приведено к единому стандарту проекта. 1.0 сек даёт приемлемую задержку при опросе без избыточной нагрузки на PVE API. Субсекундные интервалы не оправданы для задач, останавливающихся за секунды. |

---

## Совместимость

| PVE | Статус |
|---|---|
| 9.x (Primary) | Целевая версия, полная поддержка |
| 8.x (Secondary) | Best effort. Если PVE 8.x не поддерживает `/status/stop` — возвращать понятную ошибку |

---

## Риски

| Риск | Вероятность | Влияние | Митигация |
|---|---|---|---|
| PVE 8.x не поддерживает task stop | Средняя | Среднее | Проверка на этапе Validation |
| Недостаточно прав у токена | Высокая | Среднее | Чёткое сообщение об ошибке |
| Таймаут при ожидании остановки | Средняя | Низкое | Конфигурируемый timeout |
| Повторный вызов для той же задачи | Высокая | Низкое | Проверка статуса перед отменой |

---

## Live Validation Requirements

Цель: проверить работу `task_cancel` на реальном кластере PVE 9.2.3.

### 1. Endpoint Availability

- Выполнить `POST /api2/json/nodes/{node}/tasks/{upid}/status/stop` для существующего UPID
- Ожидаемый результат: HTTP 200, `{"data": null}`
- Критерий прохождения: endpoint отвечает, не возвращает 404 или 501

### 2. Required Permissions

- Выполнить `task_cancel` с текущим токеном (`ai-agent@pve!openwebui`)
- Ожидаемый результат: если `Sys.Modify` не назначен — получить осмысленную ошибку (401/403)
- Задокументировать требуемую привилегию по результатам теста
- Критерий прохождения: ошибка однозначно указывает на недостаток прав

### 3. Response Format

- Проверить структуру ответа в режиме `wait=false`
- Проверить структуру ответа в режиме `wait=true`
- Критерий прохождения: все поля присутствуют, типы корректны

### 4. Repeated Cancel Behaviour

- Выполнить `task_cancel` дважды для одного UPID
- Первый вызов: ожидается `cancel_requested: true`
- Второй вызов: ожидается сообщение о том, что задача уже останавливается или завершена
- Критерий прохождения: второй вызов не вызывает ошибку PVE API, возвращает понятное описание

### 5. Completed Task Behaviour

- Найти завершённую задачу (status = stopped/OK)
- Выполнить `task_cancel` для неё
- Ожидаемый результат: `cancel_requested: false`, сообщение "Задача уже завершена"
- Критерий прохождения: не возникает ошибка PVE API

### 6. Wait Mode Verification

- **wait=false:** запрос отправлен, ответ получен немедленно, `stopped: false`
- **wait=true:** запрос отправлен, ответ после остановки задачи, `stopped: true`
- **wait=true + timeout:** если задача не останавливается за timeout — возврат ошибки таймаута
- Проверить оба режима

---

## План валидации

1. **Unit-тесты:** `_post_json`, `task_cancel` handler, защита от повторной отмены
2. **Live validation** (по требованиям выше):
   - Endpoint availability
   - Required permissions
   - Response format (wait=false, wait=true)
   - Repeated cancel behaviour
   - Completed task behaviour
3. **PVE 8.x:** Проверить доступность `/status/stop` (если доступен кластер)

---

## Критерии Acceptance

- [ ] Реализован `_post_json` в PveClient
- [ ] Реализован tool `task_cancel` с проверкой статуса
- [ ] Опциональный `wait` работает корректно
- [ ] Unit-тесты проходят
- [ ] Live validation на PVE 9.x пройдена (минимум 2 теста)
- [ ] Ошибки обрабатываются и возвращаются пользователю
- [ ] Документация обновлена
