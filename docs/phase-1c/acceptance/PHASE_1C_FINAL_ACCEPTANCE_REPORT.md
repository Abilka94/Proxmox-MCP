# Phase 1C — Final Acceptance: task_cancel

> Дата проверки: 2026-11-09, Europe/Moscow
> Вердикт: **REJECTED**
> HEAD: `4561204`; последний тег: `v0.3.0-phase1b.2`
> Новых запросов к Proxmox в этой приёмке: **0**

## 1. Executive Summary — итог приёмки

Реализация `task_cancel` соответствует основным решениям Design v0.3 в проверенном объёме. Полный локальный pytest: **256 passed, 0 failed**, 946 предупреждений. Целевая матрица: **113 passed, 0 failed**. Единственная разрешённая Live Validation B подтверждает принятый DELETE и наблюдённое прерывание конкретной задачи `qmshutdown` на 7500T/301. Это положительный результат одного сценария, а не полная приёмка.

Фаза **не готова к фиксации текущего набора файлов в Git**:

1. В трёх untracked диагностических Python-файлах обнаружен один и тот же непустой секрет API-токена. Он отличается от текущего секрета `local.yaml`, но его отзыв не доказан. Эти файлы нельзя включать в commit.
2. Те же исторические скрипты выполняют прямые изменяющие запросы при запуске/импорте, без MCP PolicyEngine и без актуального согласования целей.
3. Обязательный минимум Live Validation Plan: L1–L5 выполнены **либо ограничения отдельно приняты**. В наличии только один `wait=true` сценарий с независимым наблюдением. Отдельного принятия оставшихся ограничений в предоставленном контексте нет. Разрешение одного теста не равно отмене критерия приёмки.

Блокирующий дефект основного production-пути `task_cancel` в проверенном объёме не обнаружен. Выявлена отдельная Minor-проблема сохранения HTTP-статуса для неожиданного payload. Девять Ruff и шесть mypy ошибок независимо воспроизводятся на чистом HEAD; они не являются регрессией Phase 1C, но общий статический контроль не проходит.

Изменены только этот отчёт и README-навигация. Код, тесты, конфигурация, ACL и инфраструктура не исправлялись. Commit/push/tag не выполнялись. Вердикт не является разрешением новой версии.

## 2. Матрица требований

Нормативная основа: [workflow](../../architecture/PROJECT_WORKFLOW_RULES.md), [Design v0.3](../design/PHASE_1C_DESIGN.md), [revision](../design/PHASE_1C_DESIGN_REVISION_REPORT_v0.3.md), [Live Plan](../validation/PHASE_1C_LIVE_VALIDATION_PLAN.md). Сопоставлены [Implementation](../implementation/PHASE_1C_IMPLEMENTATION_REPORT.md), [Final Review](../review/PHASE_1C_FINAL_IMPLEMENTATION_REVIEW.md), [Final Remediation](../implementation/PHASE_1C_FINAL_REMEDIATION_REPORT.md), Stage A/B, JSON evidence и текущие исходники. Исторические статусы документов не приняты за текущее состояние.

В таблице пути `src/…` и `tests/…` отсчитываются от корня проекта. U = `tests/unit/test_task_cancel_v03.py`, I = `tests/integration/test_task_cancel.py`. PASS означает подтверждение указанным локальным методом; live-покрытие отмечено отдельно.

| ID и требование | Реализация | Тесты / доказательства | Результат и ограничения |
|---|---|---|---|
| C01. Инструмент зарегистрирован как OPERATOR | registry/tools.py:615–675 | I: проверка реестра, tools/list в общем suite | PASS; 22 инструмента в текущем дереве |
| C02. Публичный stop_task и DELETE нужного ресурса | pve/client/core.py:310–327 | U:test_url_auth_encoding_and_null_success; I: строгий полный URL; Stage B | PASS; нет POST fallback |
| C03. Без тела/query, без redirect/retry DELETE | core.py:329–393 | U:test_client_http_outcome_no_retry; I: последовательность GET/DELETE/GET | PASS; повторный пользовательский вызов — отдельная операция |
| C04. Исходный UPID и совпадающая нода | pve/client/task_validation.py:5–20; core.py:310 | U:test_validation_before_http; точные URL | PASS; совпадение не доказывает существование задачи |
| C05. pstart 8–9 hex, пустой id, token owner | task_validation.py:5–10 | U: UPID с 9 hex и token; официальный UPID.pm | PASS; модель соответствует проверенному upstream |
| C06. URL encoding ровно один раз | core.py:267–270,312–314 | U: независимые encoded literals, `%`, `?`, `#`, token owner | PASS; JSON evidence хранит decoded path, HTTP-логи — encoded URL |
| C07. Строгие аргументы до HTTP, неизвестные запрещены | domains/tasks/service.py:254–273; registry/tools.py:256–271 | U:test_validation_before_http; I: invalid/extra; проверка схемы | PASS; bool не принимается за timeout/int |
| C08. Нодальный preflight, без cluster fallback | core.py:259–308; service.py:355–361 | I: точный GET; U:test_preflight_error_never_deletes | PASS |
| C09. Завершённая задача: DELETE отсутствует | service.py:362–364 | U:test_completed_and_repeat | PASS локально; L1 live отсутствует |
| C10. Running: один DELETE на вызов | service.py:365–377 | I: accepted/terminal; Stage B | PASS; live ровно один вызов |
| C11. Ошибка preflight запрещает DELETE | service.py:317–349,355–361 | U: 7 HTTP/transport cases, malformed; I: 6 malformed cases | PASS; 404/501 не доказывают отсутствие UPID |
| C12. Универсальный envelope DELETE и строго data:null в stop_task | core.py:315–323,342–388 | U:test_generic_delete_payload, invalid_success_response, empty_or_malformed | PASS по исходу; пустые 200/204 → unknown; Minor FA-04 |
| C13. rejected / not_sent / unknown различаются | core.py:349–386; service.py:317–340 | U:test_client_transport, test_delete_outcomes; I: rejected/not_sent/unknown_wait | PASS; not_sent предполагает штатный transport |
| C14. Ошибки API безопасны, unknown не становится success | service.py:317–340 | U: sanitization; I: отсутствие секрета и лишних запросов | PASS; неизвестный DELETE немедленно возвращается без polling |
| C15. wait=false: true/unknown/null без дополнительного GET | service.py:372–377 | U:test_no_wait_and_repeated_running; I: accepted | PASS локально; L2 live отсутствует |
| C16. wait=true: отдельное наблюдение | service.py:378–406 | U:test_terminal_does_not_claim_cancellation; I: terminal; Stage B | PASS; live только один быстрый terminal |
| C17. Ограниченные GET и sleep, monotonic deadline | service.py:378–406 | U:test_timeout_preserves_last_observation, test_deadline_bounds_get_and_discards_late_status | PASS локально; timeout ограничивает только наблюдение |
| C18. Ошибка наблюдения сохраняет принятие DELETE | service.py:329–340,397–399 | U:test_observation_failure_not_success; I: observe | PASS; true/unknown/null и observation_failed |
| C19. cancelled coroutine не подавляется | service.py:355–406 | U:test_coroutine_cancellation_propagates | PASS; никакого автоматического recovery mutate |
| C20. Nullable-поля и все ключи результата | service.py:288–300,342–353 | I: точный набор 11 ключей; 6 дополнительных JSON roundtrips | PASS; нет отдельной production outputSchema/Pydantic-модели ответа |
| C21. Terminal не объявляется доказанной отменой | service.py:342–353,400–403 | U: OK/interrupted/ERROR с нейтральным message | PASS; stopped и cancel_requested независимы |
| C22. Повторные вызовы и гонки | service.py:355–377 | U: completed_and_repeat/no_wait_and_repeated_running; I: race | PASS локально; live L5 отсутствует, дедупликации нет |
| C23. READ_ONLY блокирует до HTTP | mcp/handlers/server.py:137–143; policy/engine.py:41–52 | I: denied; test_mcp_server; Stage B restore flags | PASS; текущий local.yaml READ_ONLY |
| C24. OPERATOR разрешает READ/OPERATOR, запрещает ADMIN | policy/engine.py:41–52; config/models.py:17–21 | U:test_policy_matrix, unknown_policy_denied | PASS. ADMIN — tier, **не PolicyMode**; режим ADMIN намеренно отсутствует |
| C25. Schema/model parity, default READ_ONLY | config/schema/config.schema.json; config/models.py | U:test_schema_modes_and_default; дополнительная проверка схем | PASS; режимов ровно два |
| C26. MCP -32602/-32603, ожидаемые ошибки — envelope | mcp/handlers/server.py:60–89,137–151 | I: denied/invalid/extra и доменные ошибки | PASS; MCP isError не введён по дизайну |
| C27. Структурированные фазы, outcomes, HTTP, correlation | core.py:389–402; service.py:302–315; logging/setup.py | U:test_delete_json_log; Stage B pve_delete/task_cancel/tool_call | PASS; accepted транспорта означает envelope, окончательный payload проверяет stop_task |
| C28. Владение HTTP-клиентами и сохранение POST helper | core.py:259–266,325–327,404–446 | U:test_owned_clients_closed_and_injected_client_kept_open, POST regression | PASS; старый общий READ-helper не рефакторился |
| C29. READ-регрессия task_wait/task_follow и других tools | прежние READ-пути сохранены | Полный suite 256 passed | PASS; известный прежний READ/type долг остаётся |
| C30. Live минимум перед Acceptance | Live Plan:43–58 | Stage B и JSON | **FAIL:** L1/L2/L5 не выполнены, L3 только аналог независимого READ после wait=true; отдельное принятие ограничений отсутствует |
| C31. Нет секретов/опасных случайных артефактов в Git-кандидатах | validation/*.py | Точечный безопасный scan без вывода значений | **FAIL:** FA-01/FA-02 |

API-контракт дополнительно сверён с официальными [Tasks.pm](https://github.com/proxmox/pve-manager/blob/master/PVE/API2/Tasks.pm) и [UPID.pm](https://github.com/proxmox/pve-common/blob/master/src/PVE/UPID.pm): DELETE, null, ownership и Sys.Modify для чужих задач, формат идентификатора. Это текущий upstream, не снимок установленного пакета PVE 9.2.21. Реальный успех конкретного endpoint подтверждается Stage B, а не одним upstream. Новая проверка установленной API-схемы через сеть не выполнялась.

## 3. Результаты автоматических проверок

Среда: Windows, Python 3.14.2, pytest 8.4.2, pytest-asyncio 0.26.0. Выполнены реальные локальные проверки, не переписаны старые результаты.

| Команда / проверка | Результат |
|---|---|
| `python -u -B -m pytest -p no:cacheprovider --collect-only -q` | 256 tests collected, 0.29 s |
| `python -u -B -m pytest -p no:cacheprovider -q --disable-warnings` | **256 passed, 0 failed**, 946 warnings, 5.74 s, exit 0 |
| `python -u -B -m pytest -p no:cacheprovider tests/unit/test_task_cancel_v03.py tests/integration/test_task_cancel.py -q -W default` | **113 passed, 0 failed**, 946 warnings, 2.62 s, exit 0; это подмножество полного suite |
| `python -m ruff check src/ tests/` | **9 E501**, exit 1 |
| `python -m mypy src/` | **6 ошибок в 4 файлах**, проверено 46 source files, exit 1 |
| Дополнительная проверка схем и сериализации в памяти | 2 схемы синтаксически валидны; 2 допустимых и 6 недопустимых входов; 6 доменных исходов прошли JSON roundtrip/invariants |
| Сопоставление Stage B JSON | 8 проверок согласованности — PASS |
| `git diff --check` | exit 0; whitespace ошибок нет |
| Локальные Markdown-ссылки README/docs README | отсутствующих целей нет |

Два первоначальных pytest-запуска в ограниченной среде не вернули результат и были прерваны. Они не считаются ни успешными, ни падениями тестов. Тот же suite затем успешно выполнен вне этой среды с разрешённым локальным запуском. Сетевые обращения к PVE не использовались: HTTP в новых unit/integration подменён MockTransport; subprocess-тест stdio вызывает локальный server_info. Дополнительные проверки исполнялись в памяти, исходные тесты не добавлялись и не редактировались.

### Независимая классификация статических ошибок

Чистый `HEAD` извлечён через `git archive --format=zip HEAD` во временный каталог без checkout/reset текущей работы. Там тем же интерпретатором повторены Ruff и mypy. Baseline: **те же 9 E501 и те же 6 mypy ошибок**. Временная копия удалена штатным TemporaryDirectory. Сдвиги строк вызваны добавленными импортами/кодом.

| Проверка | Текущее дерево | Baseline HEAD | Классификация |
|---|---|---|---|
| Ruff | registry/tools.py:514; test_domain_tasks.py:35,41,150; test_domain_updates.py:64; test_mcp_server.py:345,413,447,532 | tools.py:489; tasks:34,40,149; остальные те же | 9 прежних E501, новых нет |
| mypy | pve/models/responses.py:204 — duplicate numa | то же | прежний код |
| mypy | config/loader.py:68 — нет yaml stubs | то же | прежнее ограничение среды/dev dependencies |
| mypy | pve/client/core.py:216 — нет TaskListEntry.vmid | :212 | прежний READ-дефект |
| mypy | domains/tasks/service.py:134,205 — object → str/None; :224 — object не iterable | :130,201,220 | прежние task_wait/task_follow типы |

**Предупреждения:** 946 DeprecationWarning исходят из pytest_asyncio, использующего asyncio event-loop policy API, устаревший в Python 3.14. Целевой прогон с отображением предупреждений подтвердил источник; это не сообщения приложения о неуспешном DELETE. Git также предупреждает о будущем LF→CRLF в двух ранее изменённых файлах. Ошибки статического baseline не скрыты за pytest и не исправлялись вне разрешённого scope.

Отрицательная матрица покрывает HTTP 400/401/403/404/501/500/302, Connect/Pool/Read/Write/protocol errors, invalid JSON/envelope, пустые 200/204, malformed preflight, неверные типы/пределы, node mismatch, policy deny, unknown без повторов и ошибку наблюдения. Исторический тест чувствительности к неверному endpoint в Final Remediation не воспроизводился заново; текущие точные URL assertions проверены чтением и обычным прогоном.

## 4. Независимая проверка Live Validation B

Источники: [Markdown-отчёт](../validation/PHASE_1C_LIVE_VALIDATION_STAGE_B_REPORT.md), [JSON evidence](../validation/PHASE_1C_STAGE_B_EVIDENCE.json). Новых запросов или повторов Live Validation не было.

```text
UPID:7500T:000C3D32:01AF9A15:6AF22370:qmshutdown:301:ai-agent@pve!openwebui:
```

| Проверка | Фактические доказательства | Оценка |
|---|---|---|
| Количество запросов исполняющего процесса | JSON.requests: 13 записей = 11 GET + 1 POST + 1 DELETE; mutate_sent совпадает | подтверждено в пределах артефакта |
| POST | /nodes/7500T/qemu/301/status/shutdown, HTTP200, data равен UPID | один POST подтверждён; timeout60/forceStop0 указаны только в Markdown, тело в JSON не сохранено |
| UPID | node7500T/type qmshutdown/id301/full token owner; pid/pstart/starttime согласованы с task snapshots | подтверждено |
| Running перед отменой | task_before_cancel.status=running; node/id/type/upid совпадают | подтверждено; тело повторного domain-preflight GET отдельно не сохранено |
| DELETE через MCP | один HTTP200/data:null; pve_delete и task_cancel/tool_call с correlation phase1c-stage-b-301; чтение production dispatch подтверждает путь | согласуется с вызовом через MCP; подписанной независимой трассы/сохранённого driver нет |
| После отмены | domain_result и независимый task_after: stopped, received interrupt; task_log: TASK ERROR: received interrupt | подтверждено; JSON MCP text после parsing точно равен domain_result |
| Состояние VM | before running/qmpstatus running/uptime219; vm_after running/qmpstatus running/uptime220 | подтверждено на момент Stage B, не утверждение о текущем состоянии без нового GET |
| Конфигурация VM | vm_config_unchanged=true | зафиксирован результат сравнения; исходные config/digest отсутствуют в JSON, независимое повторное сравнение невозможно |
| Возврат политики | config_bytes_restored, restored_operator_denied, config_current_readonly=true; restored_policy=READ_ONLY | флаги согласованы с Markdown; текущий local.yaml отдельно загружен локально и действительно READ_ONLY |
| Запрещённые цели | все mutate-записи только 7500T/301 и его UPID; иных mutate-событий в журнале нет | признаков нарушения в представленном объёме нет; не глобальный серверный аудит |

В Markdown суммарно 20 запросов, включая 7 первоначальных GET. JSON относится только к исполняющему процессу и содержит 13. Это объяснимая разница охвата, а не обнаруженная лишняя попытка. Но семь ранних GET/версия/permissions не имеют самостоятельных response snapshots в этом JSON. Дата/версия PVE 9.2.21 подтверждены историческими отчётами подключения, а не новым соединением в Acceptance.

Остановка worker после единственного DELETE, `received interrupt` и журнал подтверждают PASS контролируемого сценария B. Из этого не следуют универсальная причинность для произвольной task, корректность всех live-сценариев и отсутствие любых внешних изменений в кластере. Артефакт не является неизменяемым аудитом; по каждому запросу нет отдельных временных меток. Транспорт Codex connector/stdio с реальной отменой не проверялся; выполнялся реальный MinimalMcpServer.handle_message в локальном процессе.

### Покрытие Live Plan

| ID | Факт |
|---|---|
| L1 — уже завершённая задача без DELETE | только unit; live не выполнен |
| L2 — wait=false | только локально; live не выполнен |
| L3 — независимый READ после L2 | независимый READ имеется после wait=true; буквальный сценарий после L2 отсутствует |
| L4 — wait=true | поведение подтверждено Stage B; не «другая задача после L2», поскольку L2 отсутствует |
| L5 — повторный вызов | только unit; live не выполнен |
| L6 — естественное завершение/гонка | локальные сценарии; live специально не провоцировались |

Live Plan:58 допускает отдельное принятие ограничений вместо всех L1–L5. В этой приёмке такое принятие не предполагается автоматически. Нельзя дописывать отсутствующие результаты либо запускать новые tests без разрешения.

## 5. Security Review

### Подтверждённые свойства production-пути

PolicyEngine вызывается до handler; tier берётся из доверенного реестра. `READ_ONLY` запрещает `task_cancel` до HTTP, `OPERATOR` разрешает OPERATOR, ADMIN запрещён в обоих режимах; неизвестные mode/tier закрыты. Аргументы не позволяют переопределять tier. Нодальная принадлежность проверяется до GET и повторно публичным клиентом. Прямой generic helper не зарегистрирован MCP-инструментом. Низкоуровневый PveClient сам не является границей Policy: внутренний код обязан обращаться к mutate через доверенный MCP handler; это существующая архитектура, а не отдельная авторизация на каждую библиотечную функцию.

Ни автоматического повторного DELETE, ни redirect/fallback, ни фонового recovery нет. При новом явном вызове для running задачи новый DELETE допустим: гарантии глобальной at-most-once и дедупликации дизайн не предоставляет. Ошибка preflight блокирует mutate; ошибка наблюдения не стирает факт принятия; потеря/невалидность ответа возвращает неизвестный исход. Terminal не переименовывается в cancelled.

### Секреты и границы проверки

Локально сопоставлено текущее значение секрета и найденный исторический literal со всеми tracked/untracked non-ignored Git-кандидатами. Значения при сканировании не выводились, в отчёт не включены. Текущий секрет в кандидатах не найден; `config/local.yaml` игнорируется Git. Исторический literal найден только в трёх местах FA-01. В `src/`, `tests/`, Markdown/JSON-отчётах совпадений с этими двумя секретами не найдено. Тестовые строки `secret`, `dummy`, `raw-secret` — фиктивные fixtures, а UPID token identifier не является credential.

Это проверка известных секретов и очевидных литералов, а не доказательство отсутствия любого возможного конфиденциального материала/секретов во всех внешних файлах и Git history. При первоначальном чтении исторических скриптов credential попал в технический вывод инструмента; о событии сообщено пользователю. Значение здесь не воспроизводится. Статус отзыва старого секрета неизвестен, проверка его действительности по сети запрещена и не проводилась.

Рабочий `verify_ssl=false` подтверждён только локальным чтением. Подлинность API-сервера сертификатом не обеспечивалась в Stage B; настройка доверенного CA остаётся эксплуатационным ограничением. Administrator ACL шире минимально необходимого: успешный live-тест с ним не доказывает least-privilege ACL. Текущие ACL не запрашивались и не менялись. Состояние READ_ONLY не заменяет ограничение прав API-токена.

## 6. Git Review

HEAD `4561204`, тег `v0.3.0-phase1b.2`. До создания этого отчёта: **13 modified tracked + 28 untracked файлов** (включая содержимое каталогов). После добавления отчёта: **13 modified + 29 untracked**, всего 42 изменённых/новых файла. Индекс не изменялся; commit/tag отсутствуют. Полный перечень приведён ниже. `config/local.yaml` ignored, не staged. Кеши Python/pytest/Ruff/mypy ignored и в перечень не входят.

Tracked diff по исходникам ограничен task_cancel, клиентским helper/parser, Policy/Schema, экспортом task_cancel, защитной MCP-границей и тестами. Общая обработка исключений MCP затрагивает другие tools, но предусмотрена Implementation и прошла общий suite. Нет новых VM/LXC mutate-tools. `_post_json` и его regression tests унаследованы от незакоммиченного пакета Phase 1C; не являются новым разрешением POST через MCP. Широкого рефакторинга READ нет. Явных несвязанных production-изменений в просмотренном diff не обнаружено; исторические диагностические скрипты нельзя включать в пакет как безопасные тесты.

Документы v0.2, PRE_V03_TRACKED.patch и прежние отчёты сохраняют историю, не являются действующими инструкциями выполнения. Дизайн/план содержат исторические «не выполнено/не разрешено»; текущая навигация и этот отчёт устанавливают актуальное состояние, без переписывания истории. Новая документация на русском, placement acceptance/ соответствует workflow.

Основные несоответствия README (135 тестов, 21 tool, старый статус review) безопасно исправлены: 256 тестов, 22 tools текущего дерева, фактический REJECTED. Последний тег/последняя принятая Phase 1B.2 сохранены.

Финальная проверка: SHA-256 исходных Python-файлов `src/`, `tests/`, `config/local.yaml` и JSON Schema до/после документирования совпали. Staged-файлов 0; READ_ONLY подтверждён повторным локальным load_config. Ссылки обоих README и этого отчёта существуют; известные текущий/исторический секреты в трёх обновлённых Markdown отсутствуют.

## 7. Известные ограничения

- Нет полного live L1–L5 и отдельного принятия соответствующих ограничений.
- PVE 8.x не проверен; best effort. PVE 9.x live подтверждён только конкретный PVE 9.2.21 и собственная task.
- Нет live-проверки least-privilege ACL, foreign task и ошибок сети/прав; последние покрыты локально.
- Внешний connector/stdio cancel не валидирован; глобальный аудит кластера и независимая проверка всех флагов evidence отсутствуют.
- Нет JobStore, idempotency/dedup, rollback, append-only audit store; logs/envelope не обещают причинность terminal.
- В среде остаётся TLS verification disabled и широкий Administrator token; исправление требует отдельного решения, здесь не выполнено.
- Ruff/mypy baseline не чист; pytest_asyncio даёт deprecation warnings. Старый общий READ-helper сохраняет прежний долг обработки/владения клиентом.

## 8. Дефекты и критичность

### FA-01 — Critical: секрет в Git-кандидатах

**Места:** `docs/phase-1c/validation/check_pve_api.py:11`, `check_pve_api_v2.py:7`, `pre_validate.py:18`.

Три untracked файла содержат одинаковый literal TOKEN_SECRET. Текущий токен отличается, но старый не доказанно отозван. `git add .` включит его в историю. **Блокер Git/Acceptance**, даже если исторический токен уже не действует. Не выдавать отсутствие текущего секрета за отсутствие любых секретов.

Решение после отдельного согласования изменений: удалить ненужные скрипты из пакета либо безопасно переписать их без credentials и автоматических mutate, затем повторить scan всего списка кандидатов, включая patch/артефакты. Не ограничиваться `.gitignore`, оставляющим секрет в рабочей папке без учёта. Пользователю отдельно проверить отзыв/замену исторического credential; агент ACL/токены не меняет. Значение в отчёты не копировать.

### FA-02 — Major: небезопасные исторические auto-run скрипты

**Места:** `check_pve_api.py:89,121` (также дополнительные прямые request-вызовы); `check_pve_api_v2.py:57,62,67,72,97,100`; `pre_validate.py:99,105,111,116,121,132`.

Код верхнего уровня отправляет POST/PUT/DELETE, использует исторические host/UPID/targets, не проходит MCP PolicyEngine и отключает проверку TLS. Это не действующий task_cancel implementation, но реальные исполняемые артефакты среди untracked файлов. Импорт/запуск способен вызвать несогласованные действия. В Acceptance не запускались. **Блокер безопасного состава commit**. После отдельного разрешения убрать их либо превратить исторические примеры в неисполняемую, обезличенную документацию. Одного main guard недостаточно для безопасного запуска mutate-диагностики.

### FA-03 — Major: обязательный live-gate не закрыт

**Места:** `docs/phase-1c/validation/PHASE_1C_LIVE_VALIDATION_PLAN.md:43–58`; Stage B report и evidence.

Минимум L1–L5 не выполнен; разрешён только один wait=true test. Локальные сценарии не заменяют live автоматически. **Блокер Acceptance**, не установленный дефект алгоритма. Решение пользователя: отдельно принять перечисленные ограничения и уточнить критерий либо отдельно согласовать недостающие безопасные проверки. Новое задание Acceptance само по себе не является согласием отказаться от критерия. Сейчас новые live-запросы запрещены.

### FA-04 — Minor: потеря известного HTTP-кода при неожиданном data

**Место:** `src/mcp_proxmox/pve/client/core.py:315–322`.

При HTTP200 `{"data":123}` универсальный `_delete_json` возвращает payload, после чего `stop_task` создаёт `PveApiError(kind=invalid_response, request_outcome=unknown)` без `status_code`. Воспроизведено локальным MockTransport: status_code=None. Публичный error.http_status будет null, хотя транспортный pve_delete содержит 200. Опасного повторного DELETE и ложного успеха нет; информация теряется только в диагностике.

Предложение отдельного исправления: сохранять HTTP metadata для endpoint-specific validation, не подставлять фиктивный 200 для неизвестного ответа и не ломать универсальность helper. Добавить assert фактического кода для non-null payload; проверить согласованность transport/domain логов. В этой приёмке код/тесты не менялись. Не является самостоятельным блокером безопасности.

### Прежний долг и документация

9 Ruff и 6 mypy ошибок подтверждены baseline; это не новые дефекты Phase 1C. Метаданные версии пакета/initialize остаются 0.1.0-alpha.0 при Git-теге v0.3.0-phase1b.2 — существующая ограниченность release metadata, не обновлять как неразрешённый выпуск. Очевидные README-несоответствия исправлены только документацией; исторические review/design отчёты не переписаны.

## 9. Итоговый вердикт

**REJECTED.** Причины: FA-01/FA-02 блокируют безопасный состав Git-пакета; FA-03 — незакрытый обязательный критерий приёмки. `ACCEPTED WITH LIMITATIONS` сейчас недопустим: обязательный gate допускает исключения только после отдельного принятия, которого нет. Положительные результаты 256 тестов и Stage B сохраняются и не аннулируются этим вердиктом.

Отсутствие падений pytest не означает отсутствия security findings, прохождения Ruff/mypy или завершения Acceptance. Production task_cancel функционально готов в проверенном объёме; общая готовность текущего пакета к commit не подтверждена.

## 10. Рекомендации по завершению

1. Отдельно согласовать обработку трёх исторических Python-файлов; устранить credential и автоматические прямые mutate. При необходимости пользователь отдельно проверяет отзыв старого секрета.
2. Принять решение по недостающим live L1/L2/L5 и соответствию L3/L4: отдельное принятие ограничений либо отдельное разрешение строго определённых сценариев. В рамках этого задания не выполнять ни один.
3. FA-04 исправлять только после разрешения кода/тестов; baseline Ruff/mypy вести отдельным согласованным техническим долгом, не расширять Phase 1C автоматически.
4. После изменений выполнить адресные проверки, полный pytest, повторный secrets/manifest review и обновить Acceptance на фактическом результате. При изменении критериев явно записать решение пользователя.
5. **К commit/tag сейчас не переходить.** Даже будущая успешная Acceptance не заменяет отдельного разрешения пользователя на commit/push/tag или выпуск.

После этой проверки работа остановлена. Реальный Proxmox, VM301, ACL, конфигурация и PolicyMode не изменялись.

## Приложение: фактический состав Git-кандидатов

Список сформирован после создания отчёта; `M` — modified tracked, `??` — untracked. Он не является staging list и не означает, что все файлы допустимо коммитить.

```text
 M README.md
 M config/schema/config.schema.json
 M docs/README.md
 M src/mcp_proxmox/config/models.py
 M src/mcp_proxmox/domains/tasks/__init__.py
 M src/mcp_proxmox/domains/tasks/service.py
 M src/mcp_proxmox/mcp/handlers/server.py
 M src/mcp_proxmox/mcp/registry/tools.py
 M src/mcp_proxmox/policy/engine.py
 M src/mcp_proxmox/pve/client/core.py
 M tests/unit/test_domain_tasks.py
 M tests/unit/test_mcp_server.py
 M tests/unit/test_pve_client.py
?? docs/architecture/PROJECT_WORKFLOW_RULES.md
?? docs/phase-1c/acceptance/PHASE_1C_FINAL_ACCEPTANCE_REPORT.md
?? docs/phase-1c/comparative-analysis/COMPARISON_TASK_MUTATION_2026-06-06.md
?? docs/phase-1c/design/PHASE_1C_DESIGN.md
?? docs/phase-1c/design/PHASE_1C_DESIGN_REVISION_REPORT_v0.3.md
?? docs/phase-1c/design/PHASE_1C_DESIGN_v0.2.md
?? docs/phase-1c/gap-analysis/GAP_ANALYSIS_TASK_MUTATION.md
?? docs/phase-1c/implementation/PHASE_1C_FINAL_REMEDIATION_REPORT.md
?? docs/phase-1c/implementation/PHASE_1C_IMPLEMENTATION_REPORT.md
?? docs/phase-1c/implementation/PHASE_1C_IMPLEMENTATION_REPORT_v0.2.md
?? docs/phase-1c/implementation/PHASE_1C_PRE_V03_TRACKED.patch
?? docs/phase-1c/review/PHASE_1C_FINAL_IMPLEMENTATION_REVIEW.md
?? docs/phase-1c/validation/PHASE_1C_ADMINISTRATOR_PERMISSIONS_CHECK_REPORT.md
?? docs/phase-1c/validation/PHASE_1C_CODEX_AUDIT_REPORT.md
?? docs/phase-1c/validation/PHASE_1C_LIVE_VALIDATION_PLAN.md
?? docs/phase-1c/validation/PHASE_1C_LIVE_VALIDATION_PLAN_v0.2.md
?? docs/phase-1c/validation/PHASE_1C_LIVE_VALIDATION_STAGE_A_REPORT.md
?? docs/phase-1c/validation/PHASE_1C_LIVE_VALIDATION_STAGE_B_REPORT.md
?? docs/phase-1c/validation/PHASE_1C_PVE_CONNECTIVITY_RECHECK_REPORT.md
?? docs/phase-1c/validation/PHASE_1C_STAGE_B_EVIDENCE.json
?? docs/phase-1c/validation/PHASE_1C_TEST_TASK_SELECTION_REPORT.md
?? docs/phase-1c/validation/PHASE_1C_VM301_STOP_DIAGNOSTIC_REPORT.md
?? docs/phase-1c/validation/PRE_VALIDATION_MUTATE_CHECK.md
?? docs/phase-1c/validation/check_pve_api.py
?? docs/phase-1c/validation/check_pve_api_v2.py
?? docs/phase-1c/validation/pre_validate.py
?? src/mcp_proxmox/pve/client/task_validation.py
?? tests/integration/test_task_cancel.py
?? tests/unit/test_task_cancel_v03.py
```
