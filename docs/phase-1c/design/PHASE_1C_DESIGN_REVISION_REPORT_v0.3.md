# Phase 1C — инженерный отчёт Design Revision v0.3

> Дата: 2026-11-02; автор: Codex
> Статус: готово к review, не утверждено; implementation и acceptance не начаты

## Основание и размещение

Основание — [независимый аудит](../validation/PHASE_1C_CODEX_AUDIT_REPORT.md), замечания пользователя и повторная сверка кода. Отчёт найден в репозитории и прочитан. По PROJECT_WORKFLOW_RULES.md дизайн и обоснование revision размещены в design/, план live-проверок — в validation/. Review не объявляется завершённым этим отчётом.

Нормативное предложение — [PHASE_1C_DESIGN.md v0.3](PHASE_1C_DESIGN.md). Там определены все поля результата, 13 сценариев и матрица response shapes. [v0.2](PHASE_1C_DESIGN_v0.2.md) сохранён побайтно, включая исходные метаданные. [Предыдущий live-план](../validation/PHASE_1C_LIVE_VALIDATION_PLAN_v0.2.md) также сохранён. Старые отчёты не переписаны задним числом.

## Изученные материалы

Прочитаны README.md, docs/README.md, PROJECT_WORKFLOW_RULES.md, REFERENCE_USAGE_POLICY.md, comparative-analysis, gap-analysis, дизайн v0.2, Implementation Report, Pre-Validation Report, отчёт Codex. Повторно сверены service.py (task_cancel/task_wait/task_follow), core.py, PolicyEngine, конфигурационные модели, JSON Schema, регистрация tool, MCP server и связанные тесты.

Первичные источники, повторно просмотренные 2026-11-02:

| Источник | Значение для решения |
|---|---|
| [Tasks.pm master](https://github.com/proxmox/pve-manager/blob/master/PVE/API2/Tasks.pm) | DELETE, null, владельцы и проверки ACL |
| [Tasks.pm stable-8](https://github.com/proxmox/pve-manager/blob/stable-8/PVE/API2/Tasks.pm) | аналогичный маршрут, best effort |
| [RESTHandler.pm](https://github.com/proxmox/pve-common/blob/master/src/PVE/RESTHandler.pm) | allowtoken по умолчанию |
| [HTTPServer.pm](https://github.com/proxmox/pve-manager/blob/master/PVE/HTTPServer.pm) | CSRF/token, 501 и HTTP 200 |
| [RESTEnvironment.pm](https://github.com/proxmox/pve-common/blob/master/src/PVE/RESTEnvironment.pm) | завершённый worker и повторный вызов |
| [UPID.pm](https://github.com/proxmox/pve-common/blob/master/src/PVE/UPID.pm) | формат UPID, pstart длиной 8–9 hex |
| [pveum.adoc](https://github.com/proxmox/pve-docs/blob/master/pveum.adoc) | пересечение ACL separated token/user |

Это изменяемые ветки официальных репозиториев; они не заменяют схему установленных пакетов. Для воспроизводимости Live Validation должна записать точные версии пакетов и ревизию использованной схемы.

### Повторная сверка reference

Соседние репозитории читались без изменений; их тесты и live-скрипты не запускались.

| Reference | Прочитанный участок | Решение |
|---|---|---|
| RekklesNA/ProxmoxMCP-Plus | локальный src/proxmox_mcp/services/jobs.py:217–252; cancel_job, cancel_factory, cancel_requested, audit | принять разделение запроса и результата; отклонить status.stop.post(), перенос JobStore и автоматическое cancelled |
| bsahane/mcp-proxmox | локальный src/proxmox_mcp/client.py:439, wait_task; utils.py:245 require_confirm; поиск cancel_task/task_cancel по src | принять идею опционального ожидания; не переносить sync sleep, timeout 600, confirm-протокол и механизм авторизации |

Локальные refs/heads/main: RekklesNA d3a9a8d454f869a6b6a7f918d1db51535c01d1aa; bsahane 15dc99aa43e482665d7df701e8fe7aa6998894ad. git -C rev-parse вернул Permission denied; значения прочитаны из файлов refs. Это идентификаторы локальных refs, а не доказательство чистоты working tree. Прежние bf1ac3f/4e24c4d из comparative report не объявляются текущими.

Конкретное отличие от прежнего анализа: у RekklesNA обнаруженный файл services/jobs.py, а не job_store.py; POST действительно присутствует в коде, но его работоспособность не доказана. У bsahane просмотренный wait_task принимает timeout=600 и poll_interval=2.0; не переносить предположения старого анализа в наш контракт.

## Проверенные факты и границы

Код подтверждает подавление preflight PveApiError, неверный POST, проверку только timed_out после task_wait, отсутствие OPERATOR режима, неполную валидацию и success-log без полноценного audit store. Существующие тесты подтверждают базовые READ функции и запрет OPERATOR, но не правильность DELETE. Аудит ранее воспроизвёл false stopped=true при 403 в polling; повторно просмотренная ветка осталась прежней.

API-схема подтверждает регистрацию DELETE, тип null и проверку владельца. Из исходников следует допустимость token-auth и повторного вызова для завершённого worker при сохранённом task-файле. Вывод пользователя pvesh на 9.2.21 подтверждает только регистрацию. Нельзя считать доказанными live-успех DELETE, права текущего токена, отмену конкретного типа задачи или причинность её завершения. Обещание обязательного Sys.Modify для любой собственной задачи неверно.

## Проблемы и решения

| Уровень | Проблема в текущем коде/дизайне | Решение v0.3 |
|---|---|---|
| Critical | service.py:264–285, POST /status/stop | stop_task → _delete_json → штатный DELETE |
| Critical | service.py:305–321, ошибка wait превращается в stopped | подтверждение только реальным GET stopped; observation_failed сохраняет принятие запроса |
| Critical | models.py:16, schema:24, engine.py:44 | явная allowlist READ_ONLY/OPERATOR, запрет ADMIN |
| Major | service.py:269, подавление preflight | ошибка до DELETE возвращается, mutate отсутствует |
| Major | service.py:276/287/315, неоднозначные поля | tri-state request, неизвестное состояние null, отсутствие причинного cancelled |
| Major | tools.py:248 и 623, неполные проверки | типы/пределы/unknown args до HTTP, Schema согласована |
| Major | service.py:265, node как URL | структурная валидация, node/UPID match, encoding сегментов |
| Major | _classify_error:77, 501=not_found | cancel не использует эту классификацию; READ контракты не меняются |
| Major | core.py:255, неопределённый исход транспорта | not_sent/rejected/unknown, никаких автоматических повторов |
| Major | core.py:255–283, timeout/JSON/ресурсы | порядок except, PveApiError, явное владение клиентом |
| Major | server.py:124, ошибки выглядят как outcome ok | структурированная запись фаз и результатов без заявления отмены |
| Minor | дизайн poll против poll_interval, старые пути/PveError | единые реальные идентификаторы |
| Minor | implementation report 6+7+1 против 9 | исторический отчёт сохранён, новые результаты указаны отдельно |
| Minor | «немедленный» wait=false | обещается только отсутствие polling |

### Принято и отклонено

Принято: сохранить _post_json; добавить универсальный _delete_json и публичный stop_task; строгий envelope; nullable cancel_requested/stopped; отдельный нодальный цикл наблюдения; fail-closed policy; ограниченное логирование существующими средствами.

Отклонено: повтор POST/других маршрутов после DELETE; SSH/kill/ticket fallback; JobStore; автоматическое cancelled; автоматические повторы mutate; универсальный transport framework; изменение READ-контрактов; новый ADMIN mode; config override tier; MCP-переключение policy; обязательное расширение ACL до проверки владельца; новая двухшаговая confirmation-схема tool.

Полноценный append-only audit не выдаётся за реализованный. Объём этой фазы — структурированные логи текущего bootstrap; более сильный audit store требует отдельного scope.

## Новый API-контракт и матрицы

Полная матрица 13 response shapes и спецификация upid/node/cancel_requested/status/stopped/exitstatus/timed_out/error/message/wait_seconds — в [дизайне](PHASE_1C_DESIGN.md#строгий-результат-v03).

Ключевое изменение: cancel_requested=true означает подтверждённое принятие DELETE; null — неизвестный исход; stopped=true означает наблюдаемый terminal. Завершение и отмена не отождествляются. При wait=false статус после запроса unknown. При preflight stopped запрос не отправляется, но stopped=true. HTTP/transport ошибки — domain envelope; invalid params и policy — существующие MCP ошибки. Это явное изменение неприемлемого текущего контракта первой непринятой mutate-операции.

| Режим | READ | OPERATOR | ADMIN |
|---|---|---|---|
| READ_ONLY | разрешён | запрещён | запрещён |
| OPERATOR | разрешён | разрешён | запрещён |
| неизвестный | запрещён | запрещён | запрещён |

По умолчанию READ_ONLY. Режим меняется только явной конфигурацией и перезапуском. Никакое поле вызова не меняет tier. Task_cancel остаётся OPERATOR.

## План изменений по файлам

Изменения ниже только проектируются, не выполнены:

| Файл | Будущая работа |
|---|---|
| src/mcp_proxmox/pve/client/core.py | _delete_json, stop_task, типизация исхода PveApiError, ошибки JSON/timeout/ресурсов; _post_json сохранить |
| src/mcp_proxmox/domains/tasks/service.py | preflight fail-closed, envelope, нодальное наблюдение и deadline; task_wait/task_follow не менять |
| src/mcp_proxmox/mcp/registry/tools.py | runtime-validation, schema limits, OPERATOR и корректное описание |
| src/mcp_proxmox/config/models.py | только PolicyMode.OPERATOR, default READ_ONLY |
| config/schema/config.schema.json | enum READ_ONLY/OPERATOR, согласование defaults |
| src/mcp_proxmox/policy/engine.py | явная матрица allowlist, неизвестное запрещено |
| src/mcp_proxmox/mcp/handlers/server.py | согласованный mapping неверных аргументов и logging outcome; прежний protocol baseline |
| tests/unit/test_pve_client.py | DELETE, transport outcomes, _post_json regression |
| tests/unit/test_domain_tasks.py | сценарии 1–13, инварианты и deadline |
| tests/unit/test_policy.py, test_config.py, test_mcp_server.py | оба режима, ADMIN deny, registry и ошибки |
| tests/integration/test_task_cancel.py | локальный MCP → policy → domain → реальный PveClient с MockTransport, без сети |
| docs/phase-1c/implementation и validation | новые отчёты только после реальной реализации/проверок |

Изменение рабочего MCP-конфига не является частью текущей работы; после review — отдельное контролируемое действие.

## Матрица тестирования

Все новые проверки ниже — план, не результат выполнения.

| ID | Уровень | Сценарий/проверка | Существующее покрытие и действие |
|---|---|---|---|
| T01 | client | ровно DELETE, нодальный URL, пустое тело, auth header, без redirect/retry | добавить; старые 6 POST тестов оставить |
| T02 | client/input | raw UPID, token, %,?,#, пустой id, pstart 9 hex, один encoding; node mismatch/path | добавить |
| T03 | client | data:null; envelope с metadata; generic data object/list; stop_task отклоняет не-null | добавить |
| T04 | client | missing data, invalid JSON, null envelope, 204 | добавить invalid_response/unknown |
| T05 | client/domain | 400/401/403/404/501/5xx, HTTP status и phase, 501 не task_not_found | изменить старый post-error тест, добавить параметризацию |
| T06 | domain | №1: stopped до вызова, exitstatus, ни одного DELETE | изменить existing already_completed |
| T07 | domain | №2: wait=false, unknown/null, один DELETE, нет post-GET | изменить existing wait_false |
| T08 | domain | №3/13: running→stopped, OK и error exitstatus, нет заявления cancelled | изменить existing wait_true, добавить естественное завершение |
| T09 | domain | №4: timeout, последнее наблюдение/unknown, sleep/GET bounded, CancelledError | изменить existing timed_out, добавить deadline cases |
| T10 | domain | №5: preflight 400/401/403/404/501/5xx/transport/malformed; DELETE отсутствует | добавить |
| T11 | client/domain | №8: Connect/Pool error not_sent; №9: Write/Read/5xx/protocol unknown | добавить; проверить отсутствие retry и polling unknown |
| T12 | domain | №10: после DELETE GET 403/404/501/5xx/transport/invalid status; stopped не true | добавить ключевую регрессию аудита |
| T13 | domain | №11: первый running, повтор running; отдельно повтор stopped | старый repeated тест покрывает только stopped, расширить |
| T14 | domain | №12: GET running, DELETE accepted/rejected, затем stopped | добавить, не переименовывать гонку в отмену |
| T15 | schema/runtime | bool/string/NaN/inf/negative/zero/limits, unknown args, invalid UPID | добавить; ни GET, ни DELETE при invalid |
| T16 | policy/config | READ_ONLY deny operator/admin; OPERATOR allow read/operator deny admin; unknown deny | существующие READ_ONLY сохранить; добавить новый режим и parity Schema |
| T17 | MCP | tool registry OPERATOR, input_schema, -32602/-32603 и envelope ошибки | READ_ONLY deny существует; расширить |
| T18 | integration | MCP → policy → domain → PveClient MockTransport: accepted, unknown, preflight error, observe error | каталог сейчас пуст кроме __init__; добавить |
| T19 | regression | все READ tools, task_wait/task_follow, POST, дефолт READ_ONLY | полный существующий suite, проверить отсутствие изменения контрактов |
| T20 | logs | correlation/phase/outcome, без секрета и ложного success-cancel | добавить на существующий logging механизм |

### Фактический прогон

В ходе Design Revision повторно выполнено вне sandbox:

```powershell
python -B -m pytest -p no:cacheprovider -q
```

Результат: **150 passed, 1 warning in 4.95s**, Python 3.14.2. Warning: deprecated asyncio.get_event_loop_policy в pytest_asyncio. Это текущие тесты старой реализации, не проверка ещё не реализованного v0.3. В аудите ранее было 3.85s; новый прогон не подменяет прежний результат. Integration/contract suites пока не содержат тестов. Новые Python-файлы не создавались.

## Live Validation и минимальные права

[План v0.3](../validation/PHASE_1C_LIVE_VALIDATION_PLAN.md) отделяет безопасное чтение схемы/permissions, локальные policy-проверки и разрешаемый отдельно DELETE на специально созданной тестовой задаче. Ни один новый live-сценарий не выполнен. Нет обращения к текущему токену или изменения ACL.

Сначала установить владельца, включая полный token id. Для собственной задачи не предполагается универсальный Sys.Modify; чужие задачи исключены из плана. Если собственная задача не проходит, зафиксировать результат и остановиться: не повышать права и не менять auth автоматически. Любые будущие ACL — отдельное согласование минимального node scope и срока, без отключения privsep.

## Риски, открытые вопросы и readiness

К review явно вынесены: nullable booleans, status unknown при wait=false, сохранение -32603 для PolicyDenied, отдельный цикл наблюдения вместо прямого task_wait, диапазоны timeout/poll_interval и ограниченный audit logging. Это предложения, а не уже согласованные решения.

Непроверенное: установленная схема/версии пакетов PVE 9.2.21, фактический успешный DELETE с токеном, поведение выбранного типа задачи, доступный безопасный способ создать собственную тестовую задачу без расширения Phase 1C. Такой способ и объект должен назначить/одобрить оператор перед live-проверкой. PVE 8.x остаётся best effort. Показание terminal не доказывает причинность отмены даже при сообщении об interruption.

Критерии готовности к implementation: review v0.3 принят явно; спорные решения выше одобрены; матрицы полей/ошибок/прав/тестов согласованы; scope не расширен. Live-успех не требуется до начала исправления, но обязателен перед Acceptance либо должна быть отдельно согласована документированная невозможность проверки. Сам этот отчёт не разрешает implementation.

Проверка границ изменений: SHA256 всех 65 файлов из src/, tests/, config/ до и после подготовки документов совпадают (сопоставление по пути, независимо от порядка перечисления). git diff --check не выявил ошибок whitespace. Локальные файловые ссылки в изменённой навигации и новых активных документах проверены на существование; это не проверка внешних URL или Markdown anchors.

Изменены только документы и навигация. Исправления кода, конфигурации и ACL не выполнялись. После передачи v0.3 работа останавливается до решения пользователя.
