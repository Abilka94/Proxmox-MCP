# Phase 1C — Combined Remediation FA-03 + FA-04

> Дата: 2026-11-09
> FA-04: **RESOLVED**
> FA-03: **PARTIALLY RESOLVED; оставшаяся live-часть BLOCKED**
> Повторный Final Acceptance: **REJECTED**
> Реальных API-запросов в этом этапе: **0**; Git index не изменялся

## 1. Executive Summary

Минимально исправлена потеря фактического HTTP-кода при non-null data в DELETE-ответе. Клиент и публичный MCP error теперь сохраняют исходный HTTP status, а результат остаётся неизвестным; повторов DELETE и ложного success нет. Универсальный `_delete_json` по умолчанию продолжает возвращать произвольный data, успешный `stop_task` с data:null сохраняет прежнюю семантику.

Добавлены **16 регрессионных/сквозных mock-сценариев**: 9 unit для FA-04, 4 MCP integration для FA-04, 3 integration для completed/no-wait/read/repeat. Финальный полный suite: **272 passed, 0 failed**, 1090 предупреждений. Ruff: прежние 9 E501; mypy: прежние 6 ошибок. Новых итоговых статических диагностик нет; baseline независимо перепроверен на HEAD.

FA-03 максимально продвинут локально: матрица L1–L5 сопоставлена с доказательствами, локальные пробелы дополнены, подготовлен отдельный исполнимый по шагам [план оставшихся live-сценариев](../validation/PHASE_1C_REMAINING_LIVE_SCENARIOS_PLAN.md). Но новый live не выполнялся, а ограничения обязательного gate пользователь не принимал. Поэтому FA-03 не закрыт, повторная приёмка **REJECTED**.

## 2. Исходные дефекты и основания

Изучены [workflow](../../architecture/PROJECT_WORKFLOW_RULES.md), [Design v0.3](../design/PHASE_1C_DESIGN.md), [Live Plan](../validation/PHASE_1C_LIVE_VALIDATION_PLAN.md), [первый Acceptance](PHASE_1C_FINAL_ACCEPTANCE_REPORT.md), Stage A/B и JSON evidence, [remediation FA-01/FA-02](PHASE_1C_FA01_FA02_REMEDIATION_REPORT.md), [Security Remediation 19.3](PHASE_1C_SECURITY_REMEDIATION_19_3_REPORT.md), исходники и tests. Исторические отчёты не переписывались.

FA-04: `stop_task` ранее получал уже извлечённый payload из `_delete_json`; при non-null data создавал новый PveApiError без status_code. При фактическом HTTP200 публичный error.http_status становился null. Транспорт при этом успевал зарегистрировать accepted, хотя endpoint-specific подтверждение было невалидным.

FA-03: Live Plan:58 требует L1–L5 в разрешённых условиях либо отдельного принятия ограничений. Stage B подтверждает один wait=true, а не все обязательные варианты. Успех pytest не заменяет live и не означает принятие исключений пользователем.

## 3. Изменение FA-04

Файл: `src/mcp_proxmox/pve/client/core.py:310–390`.

- `stop_task` вызывает `_delete_json(path, require_null=True)`.
- В приватные `_delete_json`/`_send_delete` добавлен keyword-only флаг `require_null=False`.
- Проверка ожидаемого null выполняется внутри существующего parser/error блока `_send_delete`, пока доступен фактический response.status_code.
- Non-null payload вызывает безопасную invalid_response/unknown ошибку с фактическим кодом. Транспортный pve_delete также фиксирует unknown/invalid_response и тот же HTTP status.
- Проверка не сохраняет response body, headers или credentials в диагностике; текст ошибки не содержит исходного payload.

Это не новый metadata framework, общий request store или mutable last_response. Каждый код ошибки привязан к своему response; риск смешать статусы конкурентных запросов не вводится. `_post_json`, GET-пути, domain-алгоритм, registry, PolicyEngine, config/schema и лимиты polling не менялись.

Совместимость: `_delete_json(path)` по умолчанию универсален, возвращает null/list/object как раньше. Публичные сигнатуры `stop_task` и `task_cancel`, набор полей результата и успешный data:null не изменились. 200/202/206 в новых negative tests нужны для доказательства сохранения фактического кода, а не подстановки 200; это не новая гарантия поддержки отдельных PVE endpoints.

## 4. Новые регрессионные тесты

| Тест | Число | Проверяет |
|---|---:|---|
| `tests/unit/test_task_cancel_v03.py:test_non_null_payload_preserves_http_status` | 9 | 3 HTTP-кода × 3 non-null payload; статус в PveApiError и логах; unknown/invalid_response; один DELETE; отсутствие синтетического чувствительного содержимого в ошибке/логах |
| `tests/integration/test_task_cancel.py:test_mcp_non_null_delete_preserves_status_without_polling` | 4 | HTTP200/202 × wait=false/true; реальный MCP → policy → domain → PveClient; error.http_status, nullable outcome, отсутствие polling/retry и утечки payload |
| `tests/integration/test_task_cancel.py:test_mcp_completed_and_no_wait_read_repeat` | 3 | Два completed/no-DELETE сценария и последовательность wait=false → независимый GET → повтор terminal без второго DELETE |

Перед исправлением первые 13 новых cases дали **13 failed, 118 warnings, 0.37 s**, exit 1: во всех ожидался фактический HTTP status, наблюдался None. Это ожидаемый red regression run, не скрытые итоговые падения. После исправления и добавления оставшихся трёх весь suite прошёл.

Новые integration guards проверяют точный encoded URL, порядок запросов, пустой body/query, число обращений и JSON-сериализованный результат. Локальная последовательность GET/DELETE/GET/GET не является реальным live-доказательством.

## 5. Матрица обязательных L1–L5

Определения дословно по смыслу действующего Live Plan:43–47; содержания сценариев не переопределены.

| ID / требование | Доказательства | Текущий статус | Что осталось / mutate |
|---|---|---|---|
| L1: GET завершённой разрешённой task, затем task_cancel; false/stopped/true, без DELETE | Unit completed_and_repeat; новые integration completed false/true | Локально PASS; live **NOT VERIFIED** | Разрешённый MCP-вызов для заранее подтверждённого terminal UPID. Реальный DELETE не нужен и должен запрещаться guard |
| L2: собственная running task, wait=false; один DELETE 200 data:null; true/unknown/null | Unit no_wait_and_repeated_running; integration accepted и новый cancel_then_read | Локально PASS; live **NOT VERIFIED** | Новая отдельно разрешённая fixture task и одна отмена wait=false; нужны POST shutdown и максимум один DELETE |
| L3: независимый READ после L2 | Stage B содержит независимые status/log, но после wait=true; новый integration содержит READ после wait=false | Аналог READ подтверждён исторически; точный L3 **NOT VERIFIED** | GET status/log/VM после будущего L2; дополнительных mutate не нужно |
| L4: другая одобренная task, wait=true; terminal либо корректный timeout/error | Stage B running → DELETE200 data:null → stopped/received interrupt; unit terminal/deadline/observe-error | Функциональная live-часть **CONFIRMED HISTORICALLY**; полная связка с отдельной L2 task ещё не подтверждена | Полный вариант плана предусматривает отдельный B; переиспользование Stage B как достаточного требует явного решения пользователя, не предполагается автоматически |
| L5: повтор для одобренного UPID; stopped → без DELETE, running → новый DELETE только в разрешённых пределах | Unit completed_and_repeat/no_wait_and_repeated_running; новый integration повторяет terminal | Локально PASS; live **NOT VERIFIED** | Повтор только после независимого stopped; DELETE запрещён guard. Running/unknown повтор этим планом не разрешается |

FA-03: **PARTIALLY RESOLVED** означает закрытие локальных пробелов и подготовку плана. Обязательная live-часть **BLOCKED** отсутствием нового разрешения. Это не технический отказ PVE и не закрытие findings.

## 6. Выполненные безопасные проверки

Выполнены полный pytest, полный Ruff/mypy и независимое сравнение с baseline HEAD; синтаксическая проверка config/tool JSON Schema; локальная проверка READ_ONLY deny; чтение source/diff и структурированных логов; статический secrets check; повторное сопоставление существующего Stage B JSON с Markdown. Новые READ-запросы к PVE не понадобились: GET не может заменить недостающий wait=false mutate-сценарий.

Согласованность Stage B повторно проверена программно:

- JSON содержит 11 GET, один POST и один DELETE, все HTTP200;
- parsed MCP text точно равен domain_result;
- перед отменой running, после — stopped/received interrupt;
- VM до/после running;
- restored_policy READ_ONLY и restored_operator_denied=true.

Markdown дополнительно описывает семь ранних GET, поэтому его 20 запросов не равны 13 записям исполняющего процесса в JSON. Это разный охват. JSON не содержит тела POST и всех preflight/config snapshots: параметры timeout60/forceStop0 и часть условий подтверждены текстовым отчётом, не независимыми raw snapshots. Нельзя расширять доказательства до глобального аудита всех ресурсов или внешнего connector/stdio с реальным cancel.

## 7. Непокрытые live-сценарии

Нет live L1, L2, L5 и независимого READ именно после L2. Stage B сохраняет положительное функциональное wait=true доказательство, но не считается полным L1–L5 gate. Нет новой live-проверки после FA-04; исправлен только невалидный response path, которого успешный Stage B не затрагивал.

Реальные отказы сети/прав, malformed replies, race и timeout намеренно не провоцировались. Они проверены локально. PVE 8.x остаётся best effort; новый перенос тестов на другую ноду не разрешён.

## 8. План дополнительных Live Validation

Отдельный документ: [PHASE_1C_REMAINING_LIVE_SCENARIOS_PLAN.md](../validation/PHASE_1C_REMAINING_LIVE_SCENARIOS_PLAN.md). Он содержит точные node/VMID/endpoints/methods/params, предварительный допуск, ожидаемые результаты, последствия, STOP-условия, проверки и необходимость разрешения.

Полный вариант предусматривает A wait=false и отдельный B wait=true: максимум два POST shutdown(timeout60,forceStop0) и два DELETE через MCP, без retry. L1/L5 вызываются только для terminal UPID с guard, запрещающим DELETE. Все изменяющие targets — только 7500T/301. При stopped VM, task unknown/running после лимита наблюдения или любом несоответствии — STOP, без запуска VM/очистки/исправлений инфраструктуры.

План **не выполнен и не является разрешением**. Сокращение объёма через отдельное принятие исторического L4/других ограничений возможно только решением пользователя. Текущий этап не переключал OPERATOR.

## 9. Pytest, Ruff, mypy и baseline

| Проверка | Фактический результат |
|---|---|
| Red regression FA-04 до исправления | 13 expected failed, exit 1 |
| Первый полный suite после FA-04 | 269 passed, 1063 warnings, 6.54 s |
| Полный suite после дополнительных L1/L2/L3/L5 mock cases | **272 passed, 0 failed, 1090 warnings, 5.99 s**, exit 0 |
| Полный Ruff | **9 прежних E501**, exit 1 |
| Полный mypy | **6 прежних ошибок в 4 файлах**, 46 source files, exit 1 |
| Schema syntax / current READ_ONLY deny | PASS |
| diff --check / cached --check | PASS |

Команда suite: `python -u -B -m pytest -p no:cacheprovider -q --disable-warnings`. После финального suite выполнены только переносы строк в новом integration-тесте для Ruff; поведения не меняли. Обнаруженный новый E501 при подготовке теста исправлен; финальный Ruff вернулся к девяти baseline-ошибкам. Увеличение предупреждений соответствует добавленным async-cases и прежнему deprecated asyncio policy API pytest_asyncio; это не ошибки приложения.

Baseline проверен заново: `git archive --format=zip HEAD` извлечён во временный каталог, там тем же Python запущены Ruff/mypy. Текущие изменения не checkout/reset и не затёрты. Временная копия удалена штатным TemporaryDirectory.

| Диагностика | Текущее дерево | Baseline HEAD |
|---|---|---|
| Ruff registry E501 | tools.py:514 | :489 |
| Ruff старых tasks tests | test_domain_tasks.py:35,41,150 | :34,40,149 |
| Ruff остальных старых tests | test_domain_updates.py:64; test_mcp_server.py:345,413,447,532 | те же места |
| mypy duplicate numa | responses.py:204 | то же |
| mypy yaml stubs | loader.py:68 | то же |
| mypy READ TaskListEntry.vmid | core.py:216 | :212 |
| mypy прежних READ task_wait/task_follow типов | service.py:134,205,224 | :130,201,220 |

Новых итоговых регрессий Ruff/mypy — **0**. Общие статические проверки не объявляются зелёными: baseline остаётся техническим долгом и не исправляется вне scope.

## 10. Security Review

FA-04 не сохраняет сырой response payload/headers в PveApiError или logs. Unit с синтетическим чувствительным payload проверяет отсутствие его содержимого в ошибке и логах; integration — в JSON MCP response. HTTP status берётся из фактического response, не hardcoded. Unknown остаётся unknown; wait=true не начинает polling после unknown DELETE.

Policy enforcement и доверенный OPERATOR tier сохранены. Проверка текущего READ_ONLY в памяти действительно запретила task_cancel, без HTTP. Конфигурация/ACL/токен не менялись. `_post_json` не расширялся; новых mutate-tools, retry/fallback, постоянных ограничений по нодам или диагностических скриптов нет.

Статический поиск текущего token secret и исторических S2/S4 в tracked/untracked Git-кандидатах и index не выявил совпадений. В новых тестах только фиктивные credentials/синтетическое содержимое, без реальных секретов. S2/S4 остаются в HEAD history согласно Security Remediation 19.3; их подлинность/отзыв не установлены и не проверялись по сети. Рабочий ignored local.yaml с ожидаемым credential не является Git-кандидатом. Удалённые три опасных скрипта не восстановлены.

Ограничения: обычные логи не append-only audit store; произвольные внешние transport/log handlers не проверялись; TLS verification disabled в рабочей конфигурации и широкие ранее назначенные ACL не исправлялись.

## 11. Git status и сохранность существующей работы

HEAD `4561204`, тег `v0.3.0-phase1b.2`. На старте один обезличенный historical guide уже staged. Снимки всех index entries до/после идентичны; HEAD также не изменился. Автоматического git add/reset/checkout не было.

Изменения этого задания:

1. `src/mcp_proxmox/pve/client/core.py` — минимальный FA-04 fix.
2. `tests/unit/test_task_cancel_v03.py` — 9 regression cases.
3. `tests/integration/test_task_cancel.py` — 7 integration cases.
4. `README.md`, `docs/README.md` — актуальный статус и навигация.
5. Настоящий новый combined report.
6. Новый remaining live plan.

Всего **7 файлов**. Фактический итоговый status: **14 modified tracked** (1 staged прежний guide и 13 unstaged) + **30 untracked файлов**. Untracked unit/integration files существовали до задания, их изменения не создают новые status entries. Добавлены два Markdown-документа. Сравнение рабочих хешей подтвердило изменение только core, двух test-файлов и двух README, добавление только двух новых документов, отсутствие удалений. Пользовательские изменения, исторические отчёты, local.yaml, schema и посторонний код не сбрасывались и не исправлялись. Ссылки обоих README и новых документов проверены; целевая Ruff-проверка трёх изменённых Python-файлов проходит полностью.

## 12. Обновлённый Acceptance Verdict

| Обязательное свойство | Результат повторной проверки |
|---|---|
| DELETE endpoint, UPID/node validation и encoding | PASS локально; исторический положительный Stage B |
| Preflight/terminal/running/unknown/error contracts | PASS локально; новые non-null errors сохраняют HTTP status |
| wait=false / wait=true / deadline / cancellation / отсутствие retry | PASS локально, соответствующий suite |
| Nullable cancel_requested/stopped, отсутствие утверждения cancelled | PASS; успешная семантика не менялась |
| READ_ONLY/OPERATOR/ADMIN tiers, schema, safe JSON/logging | PASS локально; ADMIN не является добавленным PolicyMode |
| FA-01/FA-02 и обезличивание S2/S4 | Прежняя remediation сохранена; опасные файлы отсутствуют |
| FA-04 | **RESOLVED** |
| Обязательный live L1–L5 либо явно принятые ограничения | **NOT MET** |

**Final Acceptance — REJECTED.** Причина — незакрытый FA-03 live-gate. Новый функциональный блокер в исправленном FA-04 пути не обнаружен. `ACCEPTED WITH LIMITATIONS` нельзя объявить без решения пользователя принять обязательные ограничения. Успех 272 pytest сам по себе не разрешает ни Acceptance, ни выпуск.

## 13. Остаточные риски

Неполное live-покрытие; исторические значения в Git без подтверждённого отзыва; PVE8 best effort; непроверенный реальный внешний connector; прежний Ruff/mypy долг; отсутствие dedup/rollback/audit store. Ни один из этих пунктов не скрыт за положительным локальным suite и не исправлялся несанкционированными инфраструктурными действиями.

## 14. Рекомендации

Согласовать отдельно точный remaining live plan либо явно принять конкретные ограничения. До решения не выполнять новые POST/DELETE и не переключать рабочий режим. После разрешённых проверок обновить Acceptance по фактическим доказательствам. К commit/push/tag и следующей Phase не переходить без отдельного разрешения.

Работа остановлена после локального remediation, повторной оценки и подготовки документов. Новая Live Validation не выполнялась.
