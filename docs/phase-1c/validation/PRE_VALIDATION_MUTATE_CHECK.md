# Pre-Validation: PRE_VALIDATION_MUTATE_CHECK

> Дата: 2026-06-06
> Статус: Завершено
> Цель: Проверить готовность среды для live validation task_cancel

---

## 1. Активный PolicyMode

**Конфигурация:** `config/local.yaml` (и `config/default.yaml`)

```yaml
policy:
  mode: READ_ONLY
```

**Тип:** `PolicyMode.READ_ONLY` (единственное значение enum в `config/models.py`)

**JSON Schema (`config.schema.json`):**
```json
"mode": { "const": "READ_ONLY" }
```

**Вывод:** Политика READ_ONLY. Мутирующие операции блокируются.

---

## 2. Разрешён ли запуск OPERATOR tools

**Нет.** Механизм запрета:

```
PolicyEngine.authorize():
  if mode == READ_ONLY and tier != READ → raise PolicyDenied
```

Все 20 READ-tools разрешены. Единственный OPERATOR-tool (`task_cancel`) будет отклонён с сообщением:

```
Tool 'task_cancel' requires tier OPERATOR, but policy mode is READ_ONLY
```

**Необходимые изменения для Live Validation:**
1. Добавить `OPERATOR` в `PolicyMode` enum (`config/models.py`)
2. Убрать `const: "READ_ONLY"` из JSON schema (`config.schema.json`)
3. Изменить `policy.mode: OPERATOR` в `config/local.yaml`
4. Либо временно понизить `tier` для `task_cancel` до `READ` (не рекомендуется)

---

## 3. Доступность task_cancel через текущую конфигурацию

**Нет.** Даже если endpoint PVE работал бы:

- PolicyEngine заблокирует вызов
- Tool не будет выполнен

**Цепочка блокировки:**
1. MCP клиент вызывает `task_cancel`
2. `_handle_tool_call()` вызывает `self._policy.authorize(tool.policy)`
3. `PolicyDenied` → JSON-RPC error `-32603`

---

## 4. Права токена ai-agent@pve!openwebui

**Проверено через:** `GET /api2/json/access/permissions`

**Имеющиеся привилегии (только Audit):**

| Привилегия | Пути |
|---|---|
| Sys.Audit | `/`, `/access`, `/access/groups`, `/nodes`, `/pool`, `/sdn`, `/storage`, `/vms` |
| VM.Audit | все пути |
| VM.GuestAgent.Audit | все пути |
| Pool.Audit | все пути |
| Datastore.Audit | все пути |
| Mapping.Audit | все пути |
| SDN.Audit | все пути |

**Отсутствуют:**
- ❌ **Sys.Modify** — критично для task cancellation
- ❌ Permissions.Modify
- ❌ Any *.Modify или *.Admin

---

## 5. Требуемые права для POST /nodes/{node}/tasks/{upid}/status/stop

На основе RekklesNA reference и документации PVE:

| Право | Назначение |
|---|---|
| `Sys.Modify` | Изменение состояния системы (остановка задач) |

**Дополнительно (если задача связана с VM/CT):**
- `VM.Modify` — для VM-related задач
- `VM.Console` — для console задач

**Текущий токен:** не имеет ни одного из этих прав.

---

## 6. Проверка endpoint на PVE 9.2.3

### Хост
```
https://192.168.0.186:8006
```

### Ноды
- `pve` (online, 4 CPU, 16GB RAM)
- `pve2` (online, 8 CPU, 16GB RAM)
- `pve3` (online, 16 CPU, 32GB RAM)

### API Version
```
GET /api2/json/version → 200
{"version": "9.2.3", "release": "9.2", "repoid": "d0fde103346cf89a"}
```

### Endpoint: POST /nodes/{node}/tasks/{upid}/status/stop

**Результат: HTTP 501 Not Implemented**

| Method | URL | HTTP | Response |
|---|---|---|---|
| POST | `/nodes/pve/tasks/{raw_upid}/status/stop` | **501** | `"Method 'POST .../status/stop' not implemented"` |
| POST | `/nodes/pve/tasks/{encoded_upid}/status/stop` | **501** | `"Method 'POST .../status/stop' not implemented"` |
| POST | `/nodes/pve/tasks/{encoded_upid}/status/stop` (+ command=stop) | **501** | `"Method 'POST .../status/stop' not implemented"` |
| POST | `/nodes/pve/tasks/{encoded_upid}` | **501** | `"Method 'POST .../tasks/{upid}' not implemented"` |
| POST | `/nodes/pve/tasks` (with form data) | **501** | `"Method 'POST .../tasks' not implemented"` |
| POST | `/cluster/tasks/{upid}` | **501** | `"Method 'POST .../tasks/{upid}' not implemented"` |
| DELETE | `/nodes/pve/tasks/{encoded_upid}/status/stop` | **501** | `"Method 'DELETE .../status/stop' not implemented"` |
| PUT | `/nodes/pve/tasks/{encoded_upid}/status/stop` | timeout | — |
| POST | extjs `/nodes/pve/tasks/{encoded_upid}/status/stop` | timeout | — |

### Endpoint: GET /nodes/{node}/tasks/{upid}/status (работает)

```
GET /nodes/pve/tasks/{encoded_upid}/status → 200
{"data": {"status": "stopped", "upid": "...", "type": "vncshell", ...}}
```

### Что работает через API token

| Path | Method | HTTP |
|---|---|---|
| `/api2/json/version` | GET | 200 |
| `/api2/json/nodes` | GET | 200 |
| `/api2/json/access/permissions` | GET | 200 |
| `/api2/json/nodes/{node}/tasks` | GET | 200 |
| `/api2/json/nodes/{node}/tasks/{upid}/status` | GET | 200 |
| `/api2/json/cluster/tasks` | GET | 200 |

### Что НЕ работает через API token

| Path | Method | HTTP | Причина |
|---|---|---|---|
| `/nodes/{node}/tasks/{upid}/status/stop` | POST | 501 | Endpoint не реализован в PVE 9.2.3 |
| `/nodes/{node}/tasks` | POST | 501 | Нет POST-обработчика |
| `/cluster/tasks` | POST | 501 | Нет POST-обработчика |
| `/access/ticket` | POST | 403 | Недоступен для API token (только ticket auth) |

---

## 7. Поведение при недостатке прав

**Тест:** POST на несуществующий endpoint с токеном без Sys.Modify

**Результат:** HTTP 501, не 401/403. Ошибка авторизации **не возникает**, потому что endpoint не существует на уровне роутинга API. Если бы endpoint существовал, PVE вернул бы:

- **401** — без auth → `"No ticket"`
- **403** — с токеном без прав → `"Permission check failed"`
- **501** — endpoint не зарегистрирован

---

## 8. Дополнительное исследование: API vs PVE Version

| Компонент | PVE 8.x (RekklesNA) | PVE 9.2.3 (текущий) |
|---|---|---|
| POST `/status/stop` | Работает | **501 Not Implemented** |
| GET `/status` | Работает | Работает |
| Метод Auth | proxmoxer (cookie) | API Token |
| Таргет | 8.x | 9.x (primary) |

**Вывод:** Endpoint `POST /nodes/{node}/tasks/{upid}/status/stop` **отсутствует** в PVE 9.2.3. Это критическое расхождение с reference-решением.

---

## 9. Инженерный отчёт и рекомендация

### Выводы

1. **task_cancel не может быть протестирован** в текущей среде:
   - Endpoint отсутствует (501) на PVE 9.2.3
   - Токен не имеет Sys.Modify
   - PolicyMode блокирует OPERATOR tools

2. **Причина расхождения:**
   - Reference-решение (RekklesNA) работает на PVE 8.x через proxmoxer (cookie-based auth)
   - PVE 9.2.3 не имеет POST-обработчика для task cancellation через API
   - Возможно, endpoint был удалён в 9.x или перенесён

3. **Альтернативные пути для task cancellation в PVE 9.x:**
   - SSH-доступ к ноде: `pvesh stop <upid>` или `kill <pid>`
   - API через `/api2/extjs/` (требует ticket auth)
   - Ticket-based auth вместо API token
   - Создание task через другой механизм (например, vzdump with kill switch)

### Рекомендация

**❌ Live Validation откладывается.**

Нельзя запускать Live Validation в текущем состоянии, так как:

- **Endpoint отсутствует** — основная функциональность не может быть проверена
- **Token не имеет прав** — даже если endpoint появится, права потребуют расширения
- **PolicyMode блокирует** — требуется изменение конфигурации

### Необходимые действия перед повторной попыткой

1. **Исследовать альтернативный API endpoint для PVE 9.x** — найти, есть ли эквивалент `task_cancel` в 9.x
2. **Расширить токен** — добавить `Sys.Modify` через веб-интерфейс PVE (Datacenter → Permissions → API Tokens)
3. **Изменить PolicyMode** — добавить `OPERATOR` в `PolicyMode` enum, изменить schema, обновить конфиг
4. **Если endpoint недоступен** — задокументировать, что Phase 1C `task_cancel` требует PVE 8.x, либо реализовать через SSH

---

## Приложение: Результаты тестовых запросов

```
GET  /api2/json/version                                         → 200 OK
GET  /api2/json/nodes                                            → 200 OK (3 nodes)
GET  /api2/json/access/permissions                               → 200 OK (Audit only)
GET  /api2/json/nodes/pve/tasks/{upid}/status                    → 200 OK
POST /api2/json/nodes/pve/tasks/{raw_upid}/status/stop           → 501 Not Implemented
POST /api2/json/nodes/pve/tasks/{encoded_upid}/status/stop       → 501 Not Implemented
POST /api2/json/nodes/pve/tasks                                  → 501 Not Implemented
POST /api2/json/cluster/tasks                                    → 501 Not Implemented
POST /api2/json/cluster/tasks/{upid}                              → 501 Not Implemented
DELETE /api2/json/nodes/pve/tasks/{upid}/status/stop              → 501 Not Implemented
```
