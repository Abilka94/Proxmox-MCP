# Phase 1C — Implementation v0.3

> Дата: 2026-11-02; автор: Codex
> Статус: реализация подготовлена к review; Live Validation и Acceptance не выполнялись

## Основание, история и исходное состояние

Реализован [утверждённый заданием пользователя Design v0.3](../design/PHASE_1C_DESIGN.md). [Отчёт revision](../design/PHASE_1C_DESIGN_REVISION_REPORT_v0.3.md) и [аудит](../validation/PHASE_1C_CODEX_AUDIT_REPORT.md) прочитаны и сверены с кодом. На старте HEAD 4561204, тег v0.3.0-phase1b.2; незакоммиченные изменения уже существовали в восьми code/test файлах и двух README, а документы Phase 1C были untracked. Исходный tracked diff сохранён в [PHASE_1C_PRE_V03_TRACKED.patch](PHASE_1C_PRE_V03_TRACKED.patch); прежний отчёт целиком сохранён в [PHASE_1C_IMPLEMENTATION_REPORT_v0.2.md](PHASE_1C_IMPLEMENTATION_REPORT_v0.2.md). Это история, не текущий контракт. Существующая работа продолжена, без reset/checkout/commit.

Обязательные README, workflow/reference policy, дизайн/revision report, прежние implementation/pre-validation и live plan прочитаны. Повторно просмотрены локальные RekklesNA services/jobs.py cancel_job и bsahane client.py wait_task: заимствовано разделение запроса и ожидания, ошибочный POST reference не перенесён. JobStore, confirm-протокол reference, sync polling и retry не переносились.

## Изменения по файлам

| Файл | Изменение |
|---|---|
| src/mcp_proxmox/pve/client/core.py | _delete_json, _send_delete, публичные stop_task/get_task_status_on_node; kind/request_outcome в PveApiError; закрытие собственных клиентов; сохранение _post_json и ограниченные исправления timeout/JSON/resources |
| src/mcp_proxmox/pve/client/task_validation.py | единый UPID_PATTERN, проверка node/UPID, TaskCancelInputError |
| src/mcp_proxmox/domains/tasks/service.py | новый task_cancel, строгая валидация, preflight fail-closed, nullable envelope, собственный bounded polling, журнал фаз |
| src/mcp_proxmox/mcp/registry/tools.py | строгие аргументы, схема с пределами и UPID/node patterns, OPERATOR сохранён |
| src/mcp_proxmox/mcp/handlers/server.py | TaskCancelInputError → -32602; безопасный неожиданный сбой; доменная ошибка не логируется как outcome ok; исправлен конфликт logging extra.message |
| src/mcp_proxmox/config/models.py | добавлен только PolicyMode.OPERATOR |
| src/mcp_proxmox/policy/engine.py | allowlist двух режимов, ADMIN/неизвестное запрещены; сообщения на русском |
| config/schema/config.schema.json | enum READ_ONLY/OPERATOR, default READ_ONLY |
| tests/unit/test_domain_tasks.py | семь старых тестов ошибочного cancel заменены новой матрицей в отдельном файле; READ-тесты сохранены |
| tests/unit/test_task_cancel_v03.py | новая unit-матрица транспорта/domain/policy/config/logs |
| tests/unit/test_mcp_server.py | ожидание русского PolicyDenied; существующие READ проверки сохранены |
| tests/integration/test_task_cancel.py | сквозные локальные MCP-сценарии с реальным PveClient и MockTransport |
| README.md, docs/README.md | актуальная навигация, implementation review, отсутствие live acceptance |

Ранее изменённые domains/tasks/__init__.py и tests/unit/test_pve_client.py сохранены. Рабочий config/local.yaml не переключался. Добавления в schema/model не являются изменением работающей конфигурации.

## HTTP-контракт и неизвестный исход

Ровно один DELETE /api2/json/nodes/{node}/tasks/{encoded_upid}, без тела, redirect и автоматического retry. Авторизация прежняя PVEAPIToken. Исходный UPID кодируется один раз; поддержаны token owner, пустой id и pstart 9 hex. Несовпадение node блокирует HTTP. Preflight и наблюдение используют нодальный GET без cluster fallback.

Универсальный _delete_json возвращает data (null/объект/массив); stop_task принимает только data:null. Дополнительные поля envelope допустимы. Пустое тело HTTP 200/204, malformed JSON, отсутствие data и неожиданный payload — invalid_response/unknown. Расхождение задания о пустом успехе с дизайном было вынесено пользователю; пользователь явно выбрал сохранение дизайна, без поддержки пустого 204 как подтверждения. Дизайн задним числом не менялся.

HTTP 4xx/501 — rejected с исходным кодом; 404 не переименовывается в task_not_found, 501 — endpoint_unsupported. ConnectError/ConnectTimeout/PoolTimeout в стандартном транспорте — not_sent. Read/Write/protocol errors, 5xx и невалидный ответ — unknown. Generic RequestError также unknown. Для unknown нет повторного DELETE или автоматического наблюдения. _post_json сохранён; исправлены владение клиентом, порядок timeout exception и JSON decoding. READ task_wait/task_follow и их error-контракты не переработаны.

## Контракт task_cancel и примеры

Во всех domain-результатах присутствуют upid, node, cancel_requested, status, stopped, exitstatus, timed_out, error, message, wait_seconds. cancel_requested=true означает валидное подтверждение API; null — неизвестный исход; false — запрос не отправлен или явно отклонён. stopped=true означает только наблюдаемый terminal, не доказанную отмену. exitstatus возвращается без переинтерпретации. error содержит code/phase/http_status/detail без сырого ответа или секрета.

| Сценарий | cancel_requested | status / stopped | error |
|---|---|---|---|
| Уже завершена | false | stopped / true | null, exitstatus из preflight |
| Принят, wait=false | true | unknown / null | null |
| Принят, terminal наблюдён | true | stopped / true | null, фактический exitstatus |
| Истёк timeout | true | последнее наблюдение либо unknown/null | null; timed_out=true |
| Preflight error | false | unknown / null | phase=preflight; DELETE отсутствует |
| DELETE 401/403/404/501 | false | unknown / null | соответствующий HTTP code и phase=delete |
| DELETE not_sent | false | unknown / null | transport_not_sent |
| DELETE unknown | null | unknown / null | request_outcome_unknown |
| GET error после DELETE | true | unknown / null | observation_failed |
| Повторный вызов | определяется новым preflight/DELETE | по новым фактам | дедупликации нет |
| Гонка/естественное завершение | определяется ответом DELETE | terminal только из GET | причинность не заявляется |

Примеры существенных полей (остальные обязательные ключи присутствуют в реальном ответе):

```json
{"cancel_requested":true,"status":"unknown","stopped":null,"error":null}
```

```json
{"cancel_requested":true,"status":"unknown","stopped":null,"error":{"code":"observation_failed","phase":"observe","http_status":403,"detail":"Ошибка обращения к API Proxmox"}}
```

```json
{"cancel_requested":null,"status":"unknown","stopped":null,"error":{"code":"request_outcome_unknown","phase":"delete","http_status":null,"detail":"Ошибка обращения к API Proxmox"}}
```

Timeout относится к наблюдению после DELETE, не всему вызову. Monotonic deadline ограничивает GET через asyncio.timeout и sleep остатком бюджета. Просроченный terminal не принимается. Отмена coroutine не подавляется. Любая ошибка наблюдения останавливает polling, сохраняя факт принятия DELETE.

## Policy и MCP

| Режим | READ | OPERATOR | ADMIN |
|---|---|---|---|
| READ_ONLY, default | Allow | Deny | Deny |
| OPERATOR, явный opt-in | Allow | Allow | Deny |
| неизвестный | Deny | Deny | Deny |

Нет config override tier и нет MCP-переключения режима. task_cancel остаётся OPERATOR. PolicyDenied сохраняет MCP -32603; неверные аргументы — -32602 до HTTP; ожидаемые API/transport ошибки возвращаются domain envelope в content/text. Непредвиденный сбой получает безопасный русский текст без исходного исключения. isError и новый протокол MCP не вводились.

## Реализованные проверки

Unit-матрица: точные method/path/auth/encoding/body; null и generic payload; metadata; HTTP 400/401/403/404/501/500/302; Connect/Pool/Read/Write/protocol; отсутствие retry; invalid JSON/envelope/empty 200/204; unknown; уже завершена; repeated running/stopped; terminal с OK/interrupted/ERROR; preflight ошибки; observe ошибки; deadline с running и без наблюдения; cancellation; неверные типы и пределы; node mismatch; invalid status; закрытие собственных клиентов; safe logs; полная матрица policy; JSON Schema/default parity; POST regression.

Integration-матрица: MCP → policy → domain → PveClient с MockTransport: accepted, terminal, preflight denial, observe denial, unknown, READ_ONLY denial, invalid args, extra args, гонка с отклонённым DELETE. Проверены отсутствие HTTP для policy/input errors, отсутствие cluster fallback, полный набор ключей envelope и отсутствие секрета.

Новые тесты не обращаются к инфраструктуре. Семь старых cancel-тестов удалены только после переноса их смысла в строгий контракт новых тестов; предыдущий текст доступен в pre-v0.3 patch. task_wait/task_follow и READ tools прогоняются полным suite.

## Результаты качества и ограничения

Финальный полный локальный результат: **235 passed, 757 warnings in 7.05s**. Из прежних 150 тестов заменены 7 старых cancel-тестов; добавлены 83 unit-сценария и 9 integration-сценариев (с учётом параметризации): 150 − 7 + 83 + 9 = 235. Все проходят. Предупреждения относятся к устаревающим asyncio policy API pytest_asyncio на Python 3.14.2. Команда: python -B -m pytest -p no:cacheprovider -q --disable-warnings. Выполнение вне sandbox, без live-скриптов.

Полный mypy показывает 6 ранее существовавших ошибок: duplicate numa в responses.py; отсутствующие yaml stubs; TaskListEntry.vmid в READ get_tasks; три ошибки типов в task_wait/task_follow. Они не исправлялись: находятся вне scope. В добавленном v0.3 коде диагностик mypy нет. Полный Ruff содержит прежние E501 в READ registry и старых тестах; новые файлы и добавленные участки проверяются отдельно. Не объявлять весь статический baseline чистым.

Ограничения: нет live-успеха на PVE 9.x, PVE 8.x best effort; нет доказательства причинности отмены и дедупликации; стандартная классификация not_sent предполагает штатный httpx transport, кастомный транспорт обязан корректно выражать ошибки. Нет JobStore, retry engine, task_stop, VM/LXC/backup mutations или append-only audit store. Обычные структурированные логи не выдаются за полноценный audit store. Прежний GET transport вне cancel сохраняет известный долг владения клиентом/ошибок; новый нодальный cancel-путь закрывает свои клиенты.

## Соответствие дизайну и следующий этап

Реализованы ключевые решения v0.3: DELETE, публичный клиентский метод, preflight fail-closed, tri-state request, наблюдаемый stopped, bounded отдельный polling, строгие входы, OPERATOR matrix, безопасные ошибки и тесты. Единственное уточнение задания (empty success) согласовано явно, решение совпадает с дизайном.

Implementation подготовлена к review, а не к объявлению Acceptance. Следующий этап — отдельно разрешённая [Live Validation](../validation/PHASE_1C_LIVE_VALIDATION_PLAN.md) на одобренной тестовой задаче после review. Рабочий режим, ACL и тестовую задачу не менять без разрешения. Реальные mutate, создание задач, Live Validation, Acceptance, commit/push/tag не выполнялись.

Финальная проверка whitespace: git diff --check без ошибок. Полный Ruff: 9 прежних E501 в READ registry/старых тестах, без новых замечаний v0.3; mypy: 6 перечисленных прежних ошибок. Новые файлы и изменённый core/domain/policy/config/server проходят целевую Ruff-проверку.

## Final Remediation FR-01–FR-03 — 2026-11-02

Единый пакет замечаний закрыт. [Подробный отчёт о remediation](PHASE_1C_FINAL_REMEDIATION_REPORT.md) содержит изменения по файлам/строкам, доказательства и ограничения. Этот раздел дополняет исторические результаты выше, не заменяя их задним числом.

FR-01: независимые точные URL и строгие HTTP sequence assertions; отрицательная подмена endpoint теперь даёт 10 ожидаемых падений (11 сценариев без DELETE проходят). FR-02: malformed preflight нормализован только в новом cancel-пути, HTTP/transport сохраняют категории. FR-03: безопасное JSON transport событие с четырьмя outcomes, фактическим HTTP status, kind/phase/correlation; response shapes сохранены.

Targeted: 113 passed. Полный набор: **256 passed, 946 warnings in 7.03s**. Ruff: прежние 9 E501; mypy: прежние 6 ошибок; новых итоговых диагностик нет. git diff --check без ошибок. Config/ACL/PolicyMode и READ-контракты не менялись. Новый общий review, реальные mutate, Live Validation, Acceptance и commit не выполнялись. Локальная remediation завершена; следующий этап — отдельно разрешённая Live Validation.
