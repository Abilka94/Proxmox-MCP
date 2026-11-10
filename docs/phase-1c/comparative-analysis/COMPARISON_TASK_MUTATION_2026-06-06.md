# Comparative Analysis: Task Mutation (Phase 1C)

> Дата: 2026-06-06
> Автор: opencode
> Статус: Завершён

## Цель анализа

Сравнить подходы к реализации task mutation (остановка/отмена задач) в референсных реализациях MCP-серверов для Proxmox VE и определить оптимальную архитектуру для данного проекта.

---

## Исследованные репозитории

| Репозиторий | Ветка | Коммит |
|---|---|---|
| RekklesNA/ProxmoxMCP-Plus | main | bf1ac3f |
| bsahane/mcp-proxmox | main | 4e24c4d |

---

## 1. RekklesNA (ProxmoxMCP-Plus)

### 1.1. Job Store и cancel_job

Основной механизм отмены задач реализован через `JobStore`:

**Файл:** `src/proxmox_mcp/job_store.py`

```python
def cancel_job(self, job_id: str) -> dict:
```

**Логика работы:**

1. Проверяет, что job существует и не находится в терминальном статусе
2. Проверяет, что job не в статусе retrying
3. Если у job есть `cancel_factory` — вызывает её с UPID
4. Иначе — вызывает PVE API напрямую:
   ```python
   self.proxmox.nodes(node).tasks(upid).status.stop.post()
   ```
5. Устанавливает статус `"cancel_requested"` (не сразу "cancelled")
6. При завершении задачи статус обновляется на `"cancelled"`

**Статусы job:**

| Статус | Терминальный | Retryable |
|---|---|---|
| `running` | - | - |
| `completed` | + | - |
| `failed` | + | + |
| `cancelled` | + | + |
| `cancel_requested` | - | + |
| `retrying` | - | - |

**Ошибки:**

- `JobConflictError` — если задача уже завершена или в процессе retrying
- stale UPID — логирование с audit

### 1.2. PVE API Endpoint для остановки задачи

```http
POST /api2/json/nodes/{node}/tasks/{upid}/status/stop
```

Реализация через proxmoxer:

```python
self.proxmox.nodes(node).tasks(upid).status.stop.post()
```

### 1.3. VM/LXC Stop

Проект также реализует:

- `stop_vm` → `POST /nodes/{node}/qemu/{vmid}/status/stop`
- `stop_container` → `POST /nodes/{node}/lxc/{vmid}/status/stop` (force) или `status/shutdown` (graceful)
- Все операции регистрируются в JobStore с cancel_factory

### 1.4. Архитектурные особенности

- JobStore — центральный компонент для отслеживания и управления фоновыми задачами
- cancel_factory — функция, создающая UPID для отмены (может отличаться от исходного UPID при retry)
- `cancel_requested` vs `cancelled` — двухфазный протокол отмены
- Audit-логирование stale UPID

---

## 2. bsahane (mcp-proxmox)

### 2.1. Отсутствие отмены задач

**Ключевое наблюдение:** проект не реализует `task_cancel`, `cancel_task`, `stop_task` или `abort_task`.

API task mutation отсутствует.

### 2.2. Wait + Mutate Pattern

Вместо отмены, каждая mutate-операция поддерживает опциональное ожидание:

```python
def stop_vm(self, node: str, vmid: int, wait: bool = False) -> dict:
    ...
    upid = result.get("data")
    if wait:
        self.client.wait_task(upid, node, timeout, poll_interval)
    return {"upid": upid, "status": status}
```

**Параметры:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `wait` | bool | False | Ожидать завершения задачи |
| `timeout` | int | 300 | Таймаут ожидания |
| `poll_interval` | float | 2.0 | Интервал опроса |

**Возврат:** Всегда возвращает `UPID` и, если `wait=True`, `status`.

### 2.3. Обработка ошибок

- `require_confirm(confirm)` — защита от случайных вызовов
- `TimeoutError` — если задача не завершилась за отведённое время
- Собственные типы ошибок отсутствуют — используются исключения proxmoxer

### 2.4. Task Status

- Реализован `get_task_status(node, upid)`
- Использует кластерный endpoint `/cluster/tasks/{upid}/status` с fallback на нодальный
- Аналогично подходу, принятому в Phase 1A данного проекта

---

## 3. Сравнительная таблица

| Критерий | RekklesNA | bsahane | Наш проект |
|---|---|---|---|
| Task cancel | + (job_store) | - | - (план Phase 1C) |
| Wait после mutate | опционально (через JobStore) | опционально (параметр wait) | - |
| Job Store | + (полноценный) | - | - |
| cancel_requested vs cancelled | + | N/A | - |
| Cancel retrying задач | + | N/A | - |
| Stale UPID detection | + | - | - |
| Audit-логирование | + | - | + (есть базовое) |
| Собственные типы ошибок | JobConflictError | - | + (PveError) |
| PVE API endpoint | `/status/stop` | N/A | N/A |
| Подтверждение операций | - | require_confirm | (будет рассмотрено) |
| Poll interval конфигурируемый | - | + | - |

---

## 4. Ключевые различия

### 4.1. Наличие механизма отмены

- RekklesNA имеет полноценный механизм отмены задач через JobStore
- bsahane полностью обходит эту функциональность
- Вывод: отмена задач PVЕ — востребованная, но не обязательная функция

### 4.2. Модель статусов задач

- RekklesNA использует двухфазную отмену (`cancel_requested` → `cancelled`)
- Это позволяет отличать "запрос на отмену отправлен" от "задача действительно отменена"
- Вывод: двухфазная модель предпочтительна для надёжности

### 4.3. Job-ориентированный vs. Операционный подход

- RekklesNA: каждая mutate-операция создаёт job в JobStore
- bsahane: каждая операция возвращает UPID, ожидание опционально
- Наш проект сейчас ближе к bsahane (возвращаем UPID без JobStore)

### 4.4. Безопасность

- RekklesNA: JobConflictError предотвращает повторную отмену
- bsahane: require_confirm предотвращает случайные вызовы
- Вывод: желательно комбинировать оба подхода

---

## 5. PVE API Endpoint для остановки задачи

На основе анализа RekklesNA и документации PVE API:

**Эндпоинт:**

```http
POST /api2/json/nodes/{node}/tasks/{upid}/status/stop
```

**Тело запроса:** не требуется (пустой POST)

**Ответ:**
```json
{
  "data": null
}
```

**Примечание:** эндпоинт может также работать как `POST /api2/json/nodes/{node}/tasks/{upid}/status` с параметром `stop=1`. Необходимо уточнить при реализации.

**Права доступа:** вероятно, требуется привилегия `Sys.Modify` на `/nodes/{node}/tasks/{upid}`. Требует верификации на этапе Validation.

---

## 6. Выводы

1. Реализация `task_cancel` необходима для полноты task domain.
2. Двухфазная модель отмены (`cancel_requested` → `cancelled`) предпочтительна.
3. JobStore не является обязательным для Phase 1C, но желателен в перспективе.
4. Параметр `wait` (по аналогии с bsahane) улучшает UX.
5. API endpoint: `POST /nodes/{node}/tasks/{upid}/status/stop`.
6. Необходима проверка прав доступа на этапе live validation.
