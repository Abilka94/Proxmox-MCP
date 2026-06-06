# Reference Repository Usage Audit

**Date:** 2026-06-06
**Auditor:** Automated (opencode workspace audit)
**Scope:** Phase 1B.1 (task_list, task_status, task_log) + Phase 1B.2 (task_wait, task_follow)

---

## 1. Использовались ли reference repositories

### Phase 1B.1 — частично

**Да, использовались.** На этапе проектирования архитектуры Phase 1B.1 оба reference репозитория анализировались:

- **RekklesNA:** Анализ `JobStore`, `poll_job`, `services/jobs.py` — для понимания механизма отслеживания задач.
- **bsahane:** Анализ `wait_task()`, `task_status()`, `list_tasks()` в `client.py` — для понимания самой простой имплементации.

### Phase 1B.2 — нет

**Не использовались.** Проектирование `task_wait` и `task_follow` было полностью самостоятельным. Reference репозитории не открывались в ходе проектирования или реализации.

---

## 2. Что анализировалось и какие идеи были заимствованы

### Из RekklesNA (ProxmoxMCP-Plus)

| Компонент | Анализировался | Заимствовано | Отвергнуто |
|-----------|---------------|--------------|------------|
| `JobStore` (SQLite) | Да | Концепция разделения job_id и UPID | SQLite-персистентность отвергнута как преждевременная (Phase 1C+) |
| `poll_job` | Да | Подход: polling + status check | Сложная retry/cancel логика не нужна для READ-tier |
| `_extract_progress()` | Да | — | Извлечение процента из лога отвергнуто (out of scope) |
| `_normalize_status()` | Да | Маппинг `exitstatus` → человеческие статусы | Собственная модель проще и предсказуемее |
| `openapi_proxy.py` (REST jobs) | Да | — | OpenAPI не входит в MCP-first архитектуру |

### Из bsahane (mcp-proxmox)

| Компонент | Анализировался | Заимствовано | Отвергнуто |
|-----------|---------------|--------------|------------|
| `wait_task()` | Да | Параметры `upid`, `node`, `timeout`, `poll_interval` | Синхронный, блокирующий (`time.sleep`) — у нас async |
| `task_status()` | Да | Cluster→node fallback | Собственная имплементация с httpx и PveApiError |
| `list_tasks()` | Да | Клиентская фильтрация | Взята идея, но переписана с Pydantic-моделями |
| `wait=False` на mutate-тулах | Да | — | Отвергнуто (mutate-операции Phase 1C) |

---

## 3. Почему Phase 1B.2 проектировалась без reference

**Сравнение перестало выполняться по трём причинам:**

1. **Архитектурное расхождение:** Наш проект перешёл на асинхронную архитектуру (`asyncio` + `httpx`). Оба reference репозитория используют синхронные блокирующие вызовы (`proxmoxer`/`time.sleep`). Их решения не применимы напрямую.

2. **Разные целевые сценарии:**
   - RekklesNA: полный lifecycle с Job Store, retry, cancel, OpenAPI — тяжеловесный подход.
   - bsahane: быстрая синхронная обёртка над Proxmoxer — простой, но без структуры.
   - Наш проект: лёгкий, async-first, READ-tier, MCP-only.

3. **Уверенность в собственных решениях:** После Phase 1A и Phase 1B.1 проектные решения (`PveClient`, `PveApiError`, `task_status`, `task_log`) уже сформировали стабильную базу. Дальнейшие надстройки (`task_wait`, `task_follow`) естественно следуют из этой базы без внешних reference.

---

## 4. Повторный gap analysis

### Относительно RekklesNA (ProxmoxMCP-Plus)

| Возможность | RekklesNA | Proxmox-MCP | Примечание |
|------------|-----------|-------------|------------|
| Async polling | ❌ (sync) | ✅ (async asyncio) | Наше преимущество |
| Persistent job store | ✅ SQLite | ❌ | Phase 1C+ |
| Task retry | ✅ | ❌ | Phase 1C+ |
| Task cancel | ✅ | ❌ | Phase 1C+ |
| Progress from log | ✅ (regex %) | ❌ | Out of scope |
| Rich status normalization | ✅ | ✅ (простая) | Нам достаточно |
| Task wait (standalone) | ❌ (через poll_job) | ✅ task_wait | Наше преимущество |
| Task follow (log accumulation) | ❌ | ✅ task_follow | Наше преимущество |
| Log truncation | ❌ | ✅ log_truncated | Наше преимущество |
| Exponential backoff | ❌ (fixed 2s) | ✅ (1×→2×→4×, max 30s) | Наше преимущество |
| OpenAPI REST | ✅ | ❌ | MCP-only by design |
| SSH-backed console | ✅ | ❌ | Phase 2+ |

### Относительно bsahane (mcp-proxmox)

| Возможность | bsahane | Proxmox-MCP | Примечание |
|------------|---------|-------------|------------|
| Async | ❌ (sync) | ✅ (async) | Наше преимущество |
| wait_task timeout | ✅ (TimeOutError) | ✅ (timed_out: true) | Оба есть, наша модель мягче (не exception) |
| Task log accumulation | ❌ | ✅ task_follow | Наше преимущество |
| Управление ошибками | ❌ (голый try/except) | ✅ (PveApiError + классификация) | Наше преимущество |
| Multi-cluster | ✅ | ❌ | Out of scope |
| CloudInit / Windows / RHCOS | ✅ (столько тулов) | ❌ | Phase 1C+ |
| Количество task-тулов | 3 + 23 inline | 5 (list/status/log/wait/follow) | Сравнимо |

---

## 5. Где наш проект сильнее

- **Архитектура:** async, httpx, Pydantic, чёткое разделение client→domain→mcp
- **Безопасность:** PveApiError с классификацией, structured error handling
- **task_follow:** лог-аккумуляция с инкрементальным pull, log_truncated, лимит 5000 строк
- **Exponential backoff:** нет ни в одном reference
- **timed_out vs error:** timeout возвращается отдельным полем, не exception
- **Единообразие:** все READ-тулы следуют единому паттерну

## 6. Где reference сильнее

- **RekklesNA Job Store:** полный lifecycle (retry, cancel, persistent), SQLite-backed
- **RekklesNA retry:** retry_factory + retry_spec — гибкий механизм повторного запуска
- **bsahane multi-cluster:** поддержка нескольких PVE кластеров
- **bsahane domain coverage:** CloudInit, Windows, RHCOS, Docker Swarm, IaC
- **Оба reference:** mutate-операции (create, delete, start, stop) — у нас Phase 1C

## 7. Чего всё ещё нет в Proxmox-MCP

- Persistent job store (Phase 1C+)
- Task cancellation (Phase 1C)
- Task retry (Phase 1C+)
- POST/mutate операции (Phase 1C)
- Multi-cluster (Phase 2+)
- SSH-backed console (Phase 2+)
- Progress percentage extraction (out of scope)
- OpenAPI surface (out of scope)
- CloudInit / Windows / RHCOS provisioning (Phase 2+)

---

## 8. Использование reference при проектировании task_list / task_status / task_log / task_wait / task_follow

### task_list
**Частично самостоятельное.** Идея клиентской фильтрации взята из bsahane (`list_tasks` в `client.py`). Pydantic-модели, async execute — собственная разработка.

### task_status
**Самостоятельное.** Cluster→node fallback присутствует в обоих reference, но имплементация через `PveApiError` и `status_code in (400, 501)` — наше ноу-хау, выработанное в ходе live validation Phase 1B.1 (баги #3, #4).

### task_log
**Самостоятельное.** Ни один reference не имеет `task_log` как отдельного MCP тула. RekklesNA использует лог внутри `poll_job` для извлечения прогресса. bsahane не использует лог вообще.

### task_wait
**Самостоятельное.** Polling-цикл с таймаутом — очевидный паттерн, не требующий reference. Наша имплементация отличается от bsahane (async, не exception на timeout, сохранение последнего статуса).

### task_follow
**Самостоятельное.** Уникальная разработка — ни один reference не реализует аккумуляцию лога в реальном времени. RekklesNA получает лог однократно при poll. bsahane не имеет task_log вообще.

---

## 9. Вывод

Reference репозитории сыграли свою роль на этапе Phase 1A и раннего Phase 1B.1 (выбор архитектуры, понимание Proxmoxer vs httpx, концепция job_id). Однако начиная с середины Phase 1B.1 (особенно после live validation и обнаружения багов PVE API), сравнение объективно перестало приносить пользу:

- Архитектуры разошлись (sync vs async, proxmoxer vs httpx)
- Reference не имеют эквивалентов для task_follow и log_truncation
- Баги PVE API (501 на cluster-level status) решались экспериментально, не через reference

**Рекомендация:** Проводить ad-hoc сравнение только при проектировании новых доменов (Phase 1C — mutate-операции, Phase 2 — multi-cluster). Еженедельный мониторинг не требуется — достаточно проверять git upstream при появлении новой функциональности.
