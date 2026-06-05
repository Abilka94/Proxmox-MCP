# Independent Project Review — MCP-Proxmox

**Дата:** 2026-06-04  
**Рецензент:** независимый (не участвовал в проекте ранее)  
**Режим:** read-only аудит, без исправления кода  
**Версия кода:** `0.1.0-alpha.0`

---

## 1. Executive Summary

Проект находится в фазе активного bootstrap. Архитектурная документация (ARCHITECTURE.md,
MEMORY_KNOWLEDGE_MODEL.md, IMPLEMENTATION_ROADMAP.md, ADR) выполнена на высоком уровне —
это сильная сторона проекта.

**Фактический статус реализации (на момент аудита):**

| Компонент | Статус | Реализовано |
|-----------|--------|-------------|
| Config System | ✅ Done | Pydantic models, YAML loader, env expansion, CLI validator, unit tests |
| Structured Logging | ✅ Done | JSON/console formatters, correlation context, secret redaction, unit tests |
| Policy Engine | ✅ Done | ToolTier enum, READ_ONLY authorization, unit tests |
| PVE Client | ✅ Done | HTTP client, auth header, typed responses, error mapping, unit tests |
| MCP Server | ✅ Done | JSON-RPC stdio transport, initialize/initialized/ping/tools/list/tools/call |
| Tool Registry | ✅ Done | ToolDefinition dataclass, registration, descriptor serialization |
| Domain Nodes | ✅ Partial | `list_nodes` implemented, `pve_node_status` missing |
| Domain Cluster | ❌ Skeleton | Empty `__init__.py` only |
| Domain Containers | ❌ Skeleton | Empty `__init__.py` only |
| Domain VMs | ❌ Skeleton | Empty `__init__.py` only |
| Orchestrator | ❌ Skeleton | Empty `__init__.py` only |
| Audit | ❌ Skeleton | Empty `__init__.py` only |
| Cache | ❌ Skeleton | Empty `__init__.py` only |
| Session | ❌ Skeleton | Empty `__init__.py` only |
| Deploy/Docker | ⚠️ Partial | Dockerfile + compose exist but entrypoint was stub (now works) |

**26 тестов проходят** (`unittest`, `0.743s`).

---

## 2. Архитектурное соответствие

### 2.1 ARCHITECTURE.md v0.2

Документ детальный, содержит чёткую слоистую архитектуру (Transport → Session → Policy →
Registry → Orchestrator → Domains → PVE). Реализация в целом следует архитектуре, но есть
отклонения.

### 2.2 MEMORY_KNOWLEDGE_MODEL.md v1.0

Memory/Knowledge слой не реализован (Phase 2). Документ пока опережает код — это ожидаемо.

### 2.3 IMPLEMENTATION_ROADMAP.md v1.0

Roadmap детальный, задачи T-100…T-117 расписаны с DoD. Реализация идёт в соответствии с
рекомендованным порядком сборки (§11).

### 2.4 Отклонения от архитектуры

| Документация | Реализация | Серьёзность |
|--------------|------------|-------------|
| ADR-0001: `httpx` async | `urllib` synchronous | **HIGH** |
| ARCHITECTURE §3.1: Orchestrator | Отсутствует | **HIGH** |
| ARCHITECTURE §3.1: Session | Отсутствует | **HIGH** |
| IMPLEMENTATION_PACKAGE: `structlog` | stdlib logging | Medium |
| ARCHITECTURE §12.2: `PVE_HOST` env var (singular) | Используется `PVE_HOST` | Low |
| ADR-0001: `pydantic-settings` в зависимостях | Не используется | Low |

---

## 3. Поэлементный аудит

### 3.1 MCP Server (`mcp/handlers/server.py`, `mcp/transport/stdio.py`)

**Качество:** Хорошее. Чистый JSON-RPC 2.0, правильная обработка ошибок, корректная
инициализация MCP.

**Проблемы:**

1. **CRITICAL: `structuredContent` в tools/call** — нестандартное поле MCP. Спецификация
   MCP определяет только `content: [{type: "text", text: "..."}]`. Поле `isError` тоже
   нестандартно (это extension из более новых версий протокола, но не из `2024-11-05`).
   Любой MCP-клиент, строго следующий спецификации, может проигнорировать или сломаться
   на этом ответе.

2. **Нет graceful shutdown.** `serve_forever()` не обрабатывает сигналы (SIGTERM, SIGINT).
   При `KeyboardInterrupt` процесс умрёт без закрытия ресурсов.

3. **Не используется официальный MCP Python SDK.** Пакет `mcp` в зависимостях, но код
   реализует свой JSON-RPC поверх raw stdio. Это означает дублирование работы и
   потенциальную несовместимость с эволюцией протокола.

4. **Нет поддержки MCP Resources/Prompts.** Архитектура описывает URI `pve://cluster/summary`
   и prompts `diagnose_service`, но они не реализованы даже в минимальном виде.

**MCP Spec Compliance:**
- Protocol version `2024-11-05` — верно
- `initialize` response — верно (capabilities, serverInfo)
- `tools/list` — верно (name, description, inputSchema)
- `tools/call` response — **нарушает спецификацию** (structuredContent, isError)
- `notifications/initialized` — верно (пустой ответ)
- `ping` — верно
- `resources/*`, `prompts/*`, `completion/*` — не реализованы

### 3.2 PVE Client (`pve/client/core.py`, `pve/auth/config.py`)

**Качество:** Среднее. Работает, но использует устаревший `urllib`.

**Проблемы:**

1. **CRITICAL: Абстракция HTTP перетянута на `urllib` вместо `httpx`.** ADR-0001 и
   ARCHITECTURE предполагают `httpx` async. `urllib` — синхронный, без connection
   pooling, без timeouts на уровне библиотеки, без поддержки async/await. Это блокирует
   fan-out в Orchestrator (T-106) и масштабирование.

2. **Отсутствует retry-логика.** При сетевых сбоях или временных ошибках PVE (502/503)
   клиент сразу падает с `PveApiError`. В Phase 1A это может быть допустимо, но не для
   продукта.

3. **`_get_json` не различает ошибки PVE API и HTTP.** Код проверяет `"data" in decoded`,
   но PVE API может возвращать успешный HTTP 200 с `{"errors": ...}` вместо `{"data": ...}`.

4. **Token в логах.** Метод `_get_json` логирует `path` и `outcome`, но если Authorization
   header попадёт в лог через exception — `redact` в logging может не сработать (зависит
   от уровня).

5. **Нет конфигурируемого timeout.** `timeout_sec` берётся из `orchestrator.node_request_timeout_sec`,
   что является скрытой зависимостью.

### 3.3 Config System (`config/`)

**Качество:** Хорошее. Pydantic с `extra="forbid"`, env-подстановка, валидация.

**Проблемы:**

1. **config/local.yaml не поддерживается.** IMPLEMENTATION_PACKAGE §7.1 описывает
   merge `default.yaml` + `local.yaml`, но он не реализован.

2. **JSON Schema существует, но не используется в runtime.** Файл
   `config/schema/config.schema.json` есть, но `load_config` использует только Pydantic.

3. **`pydantic-settings` в зависимостях, но не используется.** MCP SDK тянет
   `pydantic-settings`, но код не использует его для загрузки env.

4. **Все секции конфига обязательны.** `connection`, `policy` обязательны, что верно.
   Но `orchestrator`, `cache`, `logging`, `audit`, `subsystems` имеют default значения
   в Pydantic, при этом JSON Schema требует их как обязательные — расхождение между
   JSON Schema и Pydantic models.

### 3.4 Logging (`logging/`)

**Качество:** Хорошее. Correlation context через `ContextVar`, форматеры, redaction.

**Проблемы:**

1. **`structlog` в зависимостях, но не используется.** Код использует stdlib logging.
   structlog мог бы дать более чистые bounded context и event API.

2. **ConsoleFormatter не покрыт тестами.** Только JSON formatter тестируется.

3. **Нет middleware-хука для MCP.** Correlation id устанавливается в
   `MinimalMcpServer.handle_message`, но нет общей middleware-цепи для всех запросов.

### 3.5 Policy Engine (`policy/engine.py`)

**Качество:** Хорошее. Чистый, минималистичный, тестируемый.

**Проблемы:**

1. **Нет modes READ_ONLY/CONFIRMATION_REQUIRED/FULL_ADMIN.** Только READ_ONLY.
   Для Phase 1A это нормально, но skeleton для других modes не заложен.

2. **Нет аудита отказов.** `PolicyDenied` не логируется в audit.

3. **Нет middleware/интеграции.** `authorize` вызывается напрямую в handler — нормально
   для минимальной реализации.

### 3.6 Tool Registry (`mcp/registry/tools.py`)

**Качество:** Среднее. Работает, но смешивает ответственности.

**Проблемы:**

1. **`create_default_registry` смешивает registry с реализацией tools.**
   Функция создаёт registry с лямбда-обработчиками, замыкаясь на `pve_client`.
   Это мешает тестированию и расширяемости.

2. **Нет динамической регистрации.** `ToolRegistry` — статический и in-memory.
   Для Phase 1A достаточно.

3. **`ToolDefinition.handler` — не async.** В контексте будущего async httpx это
   создаст напряжение.

### 3.7 Domain Nodes (`domains/nodes/service.py`)

**Качество:** Среднее.

**Проблемы:**

1. **`list_nodes` возвращает все поля PVE.** `model_dump(mode="json")` экспортирует
   все поля Pydantic модели, включая `ssl_fingerprint` и другие внутренние детали
   PVE. Нет явного контракта на то, какие поля возвращаются клиенту.

2. **Только `list_nodes`.** `pve_node_status` не реализован (список tools Phase 1A
   требует оба).

3. **Нет contract tests.** Для первого реализованного domain tool нет snapshot-теста.

### 3.8 Domain Cluster, LXC, VM

**Статус:** Пустые `__init__.py`. Не реализованы.

Это блокирует Phase 1A MVP — Domains Cluster/Node/LXC/VM — core value.

---

## 4. Тестирование

### 4.1 Что тестируется

| Файл | Тестов | Что проверяют |
|------|--------|----------------|
| `tests/test_skeleton.py` | 1 | Package version |
| `tests/unit/test_config.py` | 6 | Config loading, validation, env expansion |
| `tests/unit/test_logging.py` | 3 | JSON logging, correlation id, redaction |
| `tests/unit/test_policy.py` | 3 | READ allowed, OPERATOR/ADMIN denied |
| `tests/unit/test_mcp_server.py` | 5 | MCP init, tools/list, tools/call, list_nodes, subprocess E2E |
| `tests/unit/test_pve_client.py` | 9 | Auth config, get_nodes, get_cluster_status, get_node, SSL verify, error handling |

### 4.2 Пробелы

- Нет тестов: `orchestrator`, `audit`, `cache`, `session`, `domains` (кроме nodes)
- Нет contract tests (JSON snapshots)
- Нет integration tests (mock PVE)
- Нет type checking (`mypy`) в CI
- Нет coverage измерения

### 4.3 Качество тестов

Тесты используют `unittest` (не `pytest`), что соответствует текущему окружению.
Использование `FakePveClient` и `FakeResponse`/`RecordingOpener` — правильный подход.
Тесты читаемые, изолированные, быстрые (0.743s).

---

## 5. MCP Spec Compliance & Open WebUI

### 5.1 Соответствие MCP спецификации

| Аспект | Статус |
|--------|--------|
| Protocol version 2024-11-05 | ✅ |
| JSON-RPC 2.0 | ✅ |
| Initialize handshake | ✅ |
| tools/list | ✅ (кроме resources, prompts) |
| tools/call | ⚠️ **structuredContent — нестандартное расширение** |
| resources/* | ❌ |
| prompts/* | ❌ |
| Completion | ❌ |
| Logging | ❌ (MCP logging, не app logging) |
| Roots | ❌ |

### 5.2 Open WebUI совместимость

Open WebUI поддерживает MCP через stdio (локальный) и SSE (удалённый).

- **Stdio:** будет работать, если Open WebUI настроен на запуск `python -m mcp_proxmox`
  как подпроцесс.
- **SSE:** не реализован. Open WebUI, запущенный удалённо (на сервере), не сможет
  подключиться к этому MCP-серверу. ADR-0002 признаёт это и откладывает SSE на T-600.

### 5.3 Проблемы stdio transport

- `readline()` без таймаута может заблокировать процесс навсегда при обрыве stdin.
- Нет heartbeat/ping от сервера.
- Нет лимита на размер сообщения (Content-Length может быть гигантским).

---

## 6. Технический долг

### 6.1 Немедленный (блокирует разработку)

1. **Python 3.14 несовместимость.** `pyproject.toml` требует `<3.14`, система — 3.14.2.
   Зависимости устанавливаются, но формально контракт нарушен.

2. **`urllib` вместо `httpx`.** Это архитектурное решение, принятое в ADR-0001.
   Отказ от него вызовет проблемы при реализации async fan-out в Orchestrator.

3. **Отсутствие Orchestrator.** Без него нельзя реализовать multi-node поддержку,
   ради которой спроектирована архитектура.

### 6.2 Накапливаемый (усложнит дальнейшие фазы)

1. **`structuredContent` в tools/call.** При переходе на официальный MCP SDK придётся
   переписывать формат ответов.

2. **Нет Session context.** Все последующие фазы (Audit, Policy, Knowledge) зависят
   от session_id и cluster_id в контексте.

3. **Domain Nodes возвращает нестабильный контракт.** `model_dump(mode="json")`
   зависит от полей Pydantic модели PVE, которые могут меняться между версиями PVE.

4. **Нет версионирования ToolDefinition.** Поле `version` описано в ARCHITECTURE
   для deprecation, но не реализовано.

---

## 7. Скрытые зависимости

| Источник | Зависит от | Риск |
|----------|------------|------|
| `PveClient.timeout_sec` | `OrchestratorConfig.node_request_timeout_sec` | Неочевидная связь config->client |
| `create_default_registry` | `PveClient` через замыкание | Нельзя зарегистрировать tool без PVE клиента |
| `MinimalMcpServer` | Stdout/stderr для логов | Логи в stderr смешиваются с JSON-RPC (при debug) |
| Документация ARCHITECTURE | Неявно предполагает async | Orchestrator будет async, PVE Client синхронный |

---

## 8. Проблемы масштабирования

1. **Синхронный PVE Client.** Невозможно эффективно опрашивать N нод параллельно
   (fan-out). Придётся переписывать на `httpx` async.

2. **Нет пагинации.** PVE API поддерживает пагинацию, но `list_nodes` и
   `get_cluster_status` не используют `limit`/`offset`.

3. **Нет кэша.** Для кластеров >100 гостей повторные list-запросы будут дорогими.

4. **In-memory registry.** При 100+ tools (Phase 1B+) статическая регистрация
   станет неудобной.

---

## 9. Опасные решения

1. **Token из env не валидируется при старте.** Сервер запускается даже с
   заведомо невалидным токеном — ошибка возникнет только при первом PVE-запросе.
   Это затрудняет отладку конфигурации.

2. **`StrictModel` с `extra="forbid"`.** Препятствует добавлению нестандартных полей
   конфигурации. Может сломать пользовательские конфиги при обновлении.

3. **Нет лимита на `Content-Length` в stdio.** Злоумышленник или баг клиента может
   отправить гигабайтный запрос.

4. **Нет rate limiting.** PVE API не защищён от burst-запросов со стороны оператора.

---

## 10. Качество фундамента

### Config System
- Архитектурное качество: 7/10 (хорошая Pydantic model, но нет layered config)
- Качество кода: 8/10 (чистый, типизированный)
- Тестируемость: 9/10 (изолированные тесты, easy mocking)
- Расширяемость: 6/10 (`extra="forbid"` ограничивает)
- Технический долг: низкий

### Logging
- Архитектурное качество: 7/10 (stdlib вместо structlog)
- Качество кода: 8/10
- Тестируемость: 7/10 (только JSON, ConsoleFormatter не тестируется)
- Расширяемость: 7/10 (можно добавить formatters)
- Технический долг: низкий

### Policy Engine
- Архитектурное качество: 8/10 (чистый, правильный)
- Качество кода: 9/10
- Тестируемость: 9/10
- Расширяемость: 7/10 (нет hooks для других modes)
- Технический долг: низкий

### PVE Client
- Архитектурное качество: 4/10 (urllib вместо httpx async)
- Качество кода: 6/10 (работает, но устаревший HTTP client)
- Тестируемость: 8/10 (opener injection)
- Расширяемость: 5/10 (синхронный — блокирует async)
- Технический долг: **ВЫСОКИЙ** (нужен рефакторинг на httpx)

### MCP Server
- Архитектурное качество: 6/10 (нестандартные поля, нет SDK)
- Качество кода: 7/10
- Тестируемость: 8/10
- Расширяемость: 5/10 (нет Resources/Prompts, нет сессий)
- Технический долг: средний

---

## 11. Итоговая оценка

### Готовность к дальнейшей разработке

**Да, можно продолжать.** Фундамент заложен: конфиг, логирование, policy engine, PVE
client, MCP transport — всё работает. 26 тестов проходят.

### Качество фундамента

**Выше среднего для early bootstrap.** Архитектурная документация отличная. Три из
пяти core-компонентов (Config, Logging, Policy) реализованы качественно. PVE Client
и MCP Server требуют доработки, но работают.

### Есть ли причины остановить разработку?

**Нет, но есть причины сделать два технических шага перед продолжением:**

1. **Переписать PVE Client на `httpx` async.** Это потребуется для Orchestrator (T-106)
   и fan-out. Чем раньше — тем меньше кода придётся переписывать.

2. **Убрать `structuredContent` из MCP-ответов.** Любая интеграция с реальными
   MCP-клиентами (Cursor, Open WebUI, Claude Desktop) может сломаться на нестандартных
   полях. Привести ответы к спецификации `2024-11-05`.

### Рекомендуемый порядок ближайших шагов

1. **Исправить `structuredContent`** (MCP spec compliance).
2. **Перевести PVE Client на `httpx` async** (архитектурный долг).
3. **Реализовать T-105 Session context** (блокирует Audit, Policy, Knowledge).
4. **Реализовать T-106 Orchestrator** (блокирует multi-node, pagination).
5. Продолжить по roadmap: T-107 Cluster, T-108 Node (дополнить), T-109 LXC, T-110 VM.

### Изменение статусов в документации

Текущие документы `CODEBASE_AUDIT_REPORT.md` и `PHASE_1A_PROGRESS_REPORT.md` — **опасно
устарели**. Они утверждают, что MCP Server, PVE Client и Domain Nodes — это stubs/skeleton.
Это дезинформирует нового разработчика. Рекомендуется:

- Обновить или архивировать `CODEBASE_AUDIT_REPORT.md`
- Обновить `PHASE_1A_PROGRESS_REPORT.md` с актуальным списком выполненных работ
- `CHANGELOG.md` дополнить записями о T-102, T-104, T-107 (partially), T-108 (partially)

---

## 12. Critical Issues / Recommended Improvements / Nice To Have

### Critical Issues

| # | Проблема | Компонент | Серьёзность |
|---|----------|-----------|-------------|
| C1 | `structuredContent` в tools/call — нестандартное поле MCP | MCP Server | High |
| C2 | `urllib` вместо `httpx` async — блокирует fan-out | PVE Client | High |
| C3 | Python 3.14 несовместимость (requires <3.14) | Project | High |
| C4 | Отсутствует Orchestrator — multi-node не работает | Orchestrator | High |
| C5 | Отсутствует Session — Audit и Knowledge заблокированы | Session | High |
| C6 | CODEBASE_AUDIT_REPORT.md опасная дезинформация | Docs | Medium |

### Recommended Improvements

| # | Улучшение | Компонент |
|---|-----------|-----------|
| R1 | Убрать `structuredContent` и `isError` из tools/call | MCP Server |
| R2 | Заменить `urllib` на `httpx` async | PVE Client |
| R3 | Обновить `pyproject.toml` для Python 3.14 | Project |
| R4 | Добавить graceful shutdown (signal handling) | MCP Server |
| R5 | Обновить устаревшие audit/progress доки | Docs |
| R6 | Добавить `limit`/`offset` в list tools | Domains |
| R7 | Явный контракт полей в domain tools (не model_dump) | Domains |
| R8 | Задокументировать MCP-тестирование через MCP Inspector | Tests |
| R9 | Orchestrator: node discovery, fan-out semaphore | Orchestrator |
| R10 | Session context: cluster_id, session_id | Session |

### Nice To Have

| # | Предложение | Причина |
|---|-------------|---------|
| N1 | `config/local.yaml` merge | Гибкость конфигурации |
| N2 | `pydantic-settings` для env variables | Меньше кода |
| N3 | SSE transport | Open WebUI remote |
| N4 | MCP SDK (официальный) | Совместимость |
| N5 | Contract tests (JSON snapshots) | Стабильность API |
| N6 | Rate limiting для PVE | Безопасность |
| N7 | Content-Length лимит в stdio | Безопасность |
| N8 | Cache TTL для list tools | Производительность |

---

*Отчёт составлен на основе анализа кода по состоянию на 2026-06-04.*  
*Вердикт: продолжать разработку можно, но с двумя обязательными техническими исправлениями.*
