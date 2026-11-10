# Phase 1C — Final Implementation Review v0.3

> Дата: 2026-11-02; автор: Codex
> HEAD: 4561204; принятый тег: v0.3.0-phase1b.2
> Статус: последний плановый Implementation Review завершён; исправления не начаты

## Заключение

**Critical: 0. Major: 1. Minor: 2.** Подтверждённые замечания FR-01–FR-03 перечислены ниже. Главные дефекты первоначальной реализации устранены. Проект готов к одному согласуемому пакету исправлений, затем к целевой проверке и полному regression suite. Новый общий аудит не требуется. Live Validation пока не начинать.

235 тестов проходят. Это не доказывает успешный DELETE на установленном PVE или достаточность реального токена. Код, тесты и конфигурация во время review не изменялись. Созданы только этот отчёт и навигационные ссылки. Реальные запросы к Proxmox, создание/остановка задач, ACL, commit/push/tag и Acceptance не выполнялись.

## Методология, компоненты и размещение

Прочитаны README.md, docs/README.md, PROJECT_WORKFLOW_RULES.md, REFERENCE_USAGE_POLICY.md, Design v0.3, Design Revision Report, Implementation Report, Live Validation Plan и Pre-Validation Report. По workflow этот результат review размещён в review/, отдельно от implementation и фактической live validation.

Проверена цепочка stdio entrypoint/transport → MinimalMcpServer → ToolRegistry → PolicyEngine → task_cancel → PveClient → MockTransport. Изучены конфигурационные модели/JSON Schema, авторизация, UPID validator, task_wait/task_follow, логирование, READ и новые unit/integration tests. Метод: анализ веток/инвариантов, pytest, Ruff/mypy/diff-check, дополнительные пробы в памяти с MockTransport, проверка чувствительности тестов к неверному URL. Monkeypatch действовал только в отдельном процессе, файлы не менялись.

Исходное состояние: 13 modified tracked файлов, прежние untracked документы Phase 1C и новые task_validation.py/test_task_cancel_v03.py/integration test_task_cancel.py. Существующие изменения не сбрасывались. Номера строк соответствуют проверенному состоянию. [Дизайн](../design/PHASE_1C_DESIGN.md), [Implementation Report](../implementation/PHASE_1C_IMPLEMENTATION_REPORT.md), [Live Plan](../validation/PHASE_1C_LIVE_VALIDATION_PLAN.md).

## Источники и reference

Повторно открыты официальные [Tasks.pm](https://github.com/proxmox/pve-manager/blob/master/PVE/API2/Tasks.pm) и [UPID.pm](https://github.com/proxmox/pve-common/blob/master/src/PVE/UPID.pm): DELETE, null, проверки владельца/ACL и структура UPID с pstart 8–9 hex. Это изменяемые upstream-ветки, не снимок установленной PVE 9.2.21. Предоставленный ранее pvesh usage подтверждает регистрацию, не выполнение. Прочие token/CSRF/stable-8 источники перечислены в Design Revision Report; новый live-тест ими не заменяется.

Повторно прочитаны соседние reference без изменения: RekklesNA/src/proxmox_mcp/services/jobs.py:217–252 (cancel_requested/cancel_factory, ошибочный status.stop.post), bsahane/src/proxmox_mcp/client.py:439–451 (wait_task). Принято разделение запроса и наблюдения; не перенесены POST, JobStore, sync sleep или policy reference. Их код не считается доказательством API-корректности.

## Проверенная реализация и безопасность

Правильный DELETE URL строится в stop_task; UPID/node проверяются до HTTP, сегменты кодируются quote(safe=''). Нет retry/redirect DELETE. Успех только data:null; empty 200/204, malformed JSON/envelope и другой payload → unknown согласно отдельному уточнению пользователя. Собственные клиенты закрываются, внедрённый не закрывается. _post_json сохранён.

Preflight error запрещает DELETE; уже stopped возвращает false/stopped/true. wait=false возвращает true/unknown/null без post-GET. wait=true имеет отдельный нодальный цикл, bounded await/sleep и monotonic deadline. Unknown DELETE не повторяется и не запускает polling. Ошибка observe сохраняет cancel_requested=true, status=unknown, stopped=null. Terminal и exitstatus не объявляются доказанной отменой. Повтор running допускает новый DELETE, stopped предотвращает его. Дедупликация не обещана, CancelledError не подавляется.

| Mode | READ | OPERATOR | ADMIN |
|---|---|---|---|
| READ_ONLY, default | Allow | Deny | Deny |
| OPERATOR, явный opt-in | Allow | Allow | Deny |
| неизвестный | Deny | Deny | Deny |

Enum и Schema согласованы по режимам; task_cancel остаётся OPERATOR. tools/call в stdio проходит authorize до handler; альтернативный публичный transport-route без policy не обнаружен. Прямой вызов доверенного Python-кода не является удалённым обходом MCP policy. Runtime input validation не полагается только на Schema. Полная эквивалентность всего конфигурационного JSON Schema/Python model не заявляется: прежняя Schema требует больше default-полей.

Invalid args → -32602 до HTTP; PolicyDenied → прежний -32603; ожидаемые API/transport errors → envelope content/text; неожиданный сбой имеет безопасное сообщение. Отсутствие isError — утверждённое решение v0.3, не дефект этого review. Сырые секреты имитированных transport/PVE ошибок не отражались в проверенных response/logs; это не доказательство для произвольных сторонних transport/log handlers. UPID/token identifier не является token secret. Append-only audit store исключён scope.

## Подтверждённые замечания

### FR-01 — Major: тесты пропускают неверный DELETE URL

- **Файлы/строки:** tests/unit/test_task_cancel_v03.py:217–229; tests/integration/test_task_cancel.py:47–66,109.
- **Проблема:** unit проверяет method/body/auth и подстроки encoding, но не полный URL/node/API prefix. Integration transport принимает любой DELETE, дополнительно исключая только /cluster/.
- **Воспроизведение:** в отдельном процессе обернуть PveClient._delete_json, заменив `/nodes/pve1/tasks/` на `/wrong/nodes/other/tasks/`; запустить test_url_auth_encoding_and_null_success и весь integration/test_task_cancel.py.
- **Факт:** 10 passed, 91 warnings in 0.11s при неверном endpoint. Production URL сейчас правильный; подтверждена ложноположительность защиты от регрессии.
- **Ожидание:** exact-URL тест падает; MockTransport отклоняет неизвестный маршрут/метод.
- **Исправление:** независимая полная ожидаемая строка raw_path/host/scheme, пустые query/body; integration handler допускает лишь GET status → DELETE → разрешённые GET status. Не вычислять expected через production helper.
- **Тесты:** полный путь с обычным/special UPID, node, API prefix, точные preflight/observe URLs, число запросов, отсутствие POST/fallback/лишнего DELETE.
- **Закрытие:** правильная реализация проходит; wrong-endpoint подмена в памяти вызывает ожидаемое падение; полный suite проходит.

Применённая подмена только в памяти:

```python
original = PveClient._delete_json
async def wrong_endpoint(self, path):
    if path.startswith('/nodes/'):
        path = path.replace('/nodes/pve1/tasks/', '/wrong/nodes/other/tasks/')
    return await original(self, path)
# pytest_sessionstart: PveClient._delete_json = wrong_endpoint
# targets: test_url_auth_encoding_and_null_success + tests/integration/test_task_cancel.py
```

### FR-02 — Minor: неодинаковая классификация malformed preflight

- **Файлы/строки:** client/core.py:239–243,259–274,416–417; domains/tasks/service.py:316–323; test_task_cancel_v03.py:277–285.
- **Проблема:** новый wrapper нормализует ValueError/ValidationError, но старый parser выбрасывает PveApiError без kind при missing data/не-object data.
- **Воспроизведение:** MockTransport HTTP 200 с `{}`, `{"data":[]}` и, для сравнения, `{"data":{"status":"invalid"}}`; вызвать task_cancel.
- **Факт:** первые два дают api_error, третий invalid_response. Во всех случаях DELETE отсутствует, false stopped нет.
- **Ожидание:** некорректный успешный status response единообразно invalid_response; HTTP/transport errors сохраняют свою природу.
- **Исправление:** нормализовать только новый нодальный cancel parser; не менять READ-контракты. Не считать любой status_code=None malformed: это также транспортная ошибка; не сравнивать сообщения исключений.
- **Тесты:** missing data, list/null, missing/invalid status, broken JSON; отдельно transport/401/403; assert полного error.code/phase/http_status и нулевого DELETE.
- **Закрытие:** malformed cases → invalid_response preflight; остальные ошибки отличимы; READ regression проходит.

### FR-03 — Minor: журнал теряет HTTP outcome

- **Файлы/строки:** service.py:300–312,324–337,362–364; core.py:303–345; test_task_cancel_v03.py:311–326.
- **Проблема:** request_outcome логируется как nullable boolean cancel_requested; при accepted нет HTTP code, not_sent/rejected не имеют самостоятельной транспортной категории. Domain unknown заменяет исходный kind. Ответ допустим, но журнал неполон относительно дизайна.
- **Воспроизведение:** configure_logging(log_format='json', stream=StringIO()); MockTransport GET running → DELETE 200 data:null; wait=false.
- **Факт:** delete event содержит request_outcome=true, error=null, status=unknown; HTTP code отсутствует. Сама операция обрабатывается корректно.
- **Ожидание:** журнал различает accepted/rejected/not_sent/unknown и доступный HTTP code.
- **Исправление:** безопасное transport событие DELETE с четырьмя категориями, фактическим HTTP status либо null и kind; cancel_requested response не менять. Audit store не добавлять.
- **Тесты:** сериализованный JSON formatter + correlation_context для success/401/ConnectError/ReadTimeout; проверить code/category/phase/correlation и отсутствие секрета. Одного caplog record недостаточно.
- **Закрытие:** четыре исхода различимы, accepted содержит 200; response и число запросов неизменны.

## Матрица всех 13 сценариев

| № | Сценарий | Проверка и оценка |
|---|---|---|
| 1 | stopped до вызова | completed_and_repeat: false/stopped/true, exitstatus; соответствует |
| 2 | accepted wait=false | no_wait_and_repeated_running, integration accepted; соответствует, URL coverage FR-01 |
| 3 | accepted wait=true terminal | terminal_does_not_claim_cancellation, integration terminal; соответствует |
| 4 | timeout | timeout_preserves_last_observation, deadline_bounds_get; bounded await/sleep |
| 5 | preflight error | 7 параметров и integration preflight; DELETE отсутствует; FR-02 для malformed |
| 6 | DELETE 401/403 | client_http_outcome_no_retry + domain rejected; соответствует |
| 7 | DELETE 404/501 | client_http_outcome_no_retry, правильные kind в коде; соответствует |
| 8 | сбой до отправки | ConnectError/ConnectTimeout/PoolTimeout + domain not_sent; стандартный transport |
| 9 | unknown после возможной отправки | Read/Write/protocol + domain unknown без polling + integration unknown |
| 10 | observe error после accepted | 7 параметров и integration observe; true/unknown/null, без ложного success |
| 11 | повтор | отдельно running и stopped; история/дедупликация не обещана |
| 12 | гонка | integration race: GET running → DELETE 400; accepted+terminal покрыт terminal; причинность не заявляется |
| 13 | естественное завершение | OK и нейтральное сообщение; фактическая причина локально недоказуема |

MockTransport проверяет классификацию исключений, не реальную фазу TCP-отправки. Прежний suite покрывает READ tools; stdio subprocess вызывает только локальный server_info. Live-скрипты не запускались. Дополнительно в FR-01 добавить сквозные rejected/not_sent/unknown(wait=true) варианты и строгий порядок HTTP: сейчас они покрыты преимущественно комбинацией unit-уровней.

## Фактические результаты

`python -B -m pytest -p no:cacheprovider -q --disable-warnings`: **235 passed, 757 warnings in 5.86s**, Python 3.14.2, вне sandbox. Расклад: 143 прежних сценария + 83 новых unit + 9 integration. Отдельный sensitivity run: 10 passed, 91 warnings in 0.11s — доказательство FR-01, не прибавляется к suite count. Дополнительные пробы: три malformed payload и JSON success-log на MockTransport.

`git diff --check`: exit 0, whitespace ошибок нет; предупреждения Git касаются LF/CRLF двух ранее изменённых файлов.

`ruff check src/ tests/`: exit 1, 9 E501: registry/tools.py:514; test_domain_tasks.py:35,41,150; test_domain_updates.py:64; test_mcp_server.py:345,413,447,532.

`mypy src/`: exit 1, 6 ошибок: responses.py:204 duplicate numa; loader.py:68 yaml stubs; core.py:216 TaskListEntry.vmid; service.py:134,205,224 старые task_wait/task_follow типы.

Сверка с HEAD, pre-v0.3 tracked patch и Implementation Report относит эти статические замечания к старым участкам. Новых Ruff/mypy диагностик в добавленной логике нет. Выросшее число warnings связано с pytest async tests: deprecation asyncio policy API внутри pytest_asyncio, не warning приложения. Baseline полного прежнего unittest-набора содержал одно такое предупреждение. Зависимости/warning filters не менялись. 15 прежних статических замечаний не включены в FR-01–03 и не исправляются без отдельного scope.

## Неподтверждённые риски и ограничения

Не доказаны live-успех DELETE на PVE 9.2.21, фактические ACL/ownership и безопасный тип тестовой задачи. PVE 8.x остаётся best effort. not_sent предполагает штатный httpx transport; произвольный injected transport может иметь свои retries/ошибки. Production _make_client не включает retry. Deadline зависит от кооперативной cancellation; патологический transport, её подавляющий, не доказан дефектом штатного пути. Прямой trusted Python вызов клиента не защищается MCP policy по архитектуре. Terminal/exitstatus не доказывают причинность; unknown и отсутствие дедупликации — принятые ограничения. Эти риски не включены в подтверждённые дефекты.

## Единый пакет исправлений без нового общего аудита

После отдельного согласования:

1. FR-01: tests/unit/test_task_cancel_v03.py и tests/integration/test_task_cancel.py — строгие независимые URL/method/sequence assertions, negative sensitivity, сквозные rejected/not_sent/unknown wait=true.
2. FR-02: core.py только новый cancel nodal path/parser + unit/integration malformed-response assertions. Не изменять _get_json/task_wait/task_follow ради общей унификации. Если затрагивается READ-контракт, остановить эту часть для согласования.
3. FR-03: _send_delete в core.py и при необходимости domain logging; JSON logging tests, без изменения response shapes/нового audit store.
4. Обновить Implementation Report фактическими изменениями и результатами, сохранить историю; актуализировать навигационный статус.
5. Targeted FR-01–03 и отрицательная подмена URL, затем полный regression suite, Ruff/mypy/diff-check. Новых static ошибок нет. Расширять проверку только при новых сбоях, не запускать новый общий аудит.
6. Завершение: критерии каждого FR выполнены; suite проходит; правильный endpoint защищён тестом; нет false stopped; policy matrix неизменна; рабочий config/local.yaml и ACL не менялись; отчёт обновлён; нет live mutate/commit.

Пакет не меняет архитектуру и согласованный API. Необходимое разрешение сейчас — начало этого комплексного этапа исправлений Python/тестов. Review сам его не разрешает.

## Допуск к Live Validation

План v0.3 достаточно разделяет стадии, но не разрешает их исполнение:

| Категория | Порядок |
|---|---|
| Без mutate | чтение версии/схемы/permissions, регистрация DELETE; локальные READ_ONLY deny тесты |
| Временный OPERATOR | отдельное разрешение изменения рабочего режима/перезапуска; затем восстановить согласованный режим |
| ACL | не нужны автоматически для своей token-owned задачи; отказ фиксировать, отдельно согласовать минимальный node scope/срок; не отключать privsep |
| Тестовый task | специально подготовленный оператором собственный task с известными целью/ресурсом/последствиями; без production, backup, migration, чужих задач |
| DELETE | отдельное разрешение сценария и UPID/node; L2/L4 и повторный running — mutate |
| Результаты | время, версии пакетов/кода, correlation id, разрешение, владелец, HTTP/envelope без credentials, MCP result, независимые GET/log/последствия |

Gate: пакет FR-01–03 закрыт, локальные проверки пройдены, безопасная задача назначена, режим и права проверены без автоматического расширения. Ошибки/timeout/unknown проверять локально; не требуются live revoke ACL и сбои сети. Unknown DELETE не повторять автоматически. L1–L5 выполнять только в разрешённых пределах; реальные результаты — отдельным Live Validation Report, а не подмена ожидаемых результатов в плане.

Final Implementation Review завершён. Следующее действие — согласование единого пакета FR-01–FR-03. Исправления, Live Validation и Acceptance не начаты.
