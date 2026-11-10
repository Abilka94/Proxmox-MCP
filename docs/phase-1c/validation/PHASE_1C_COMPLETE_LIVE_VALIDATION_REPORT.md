# Phase 1C — Complete Live Validation L1–L5

> Дата: **2026-11-10**, Europe/Moscow (+03:00)
> Общий результат Live Validation: **PASS**
> L1 / L2 / L3 / L5 / L4: **PASS / PASS / PASS / PASS / PASS**
> Изменяющие запросы: **2 POST + 2 DELETE**, ровно в разрешённых пределах
> Финальный GET VM301: **running / qmpstatus running**
> READ_ONLY восстановлен, index сохранён; Final Acceptance автоматически не объявляется

## Основание и исполняемый код

Пользователь явно разрешил полный пакет, включая повторный L4, только для **7500T / VM301 / phase1c-cancel-test**. Обязательная спецификация: [Remaining Live Scenarios Plan](PHASE_1C_REMAINING_LIVE_SCENARIOS_PLAN.md). Прочитаны [workflow](../../architecture/PROJECT_WORKFLOW_RULES.md), актуальные client/domain/MCP/Policy реализации, [Stage B](PHASE_1C_LIVE_VALIDATION_STAGE_B_REPORT.md), [Combined Remediation FA-03/FA-04](../acceptance/PHASE_1C_FA03_FA04_COMBINED_REMEDIATION_REPORT.md).

Выполнен один согласованный пакет без повторных попыток. Использован текущий checkout с исправленным FA-04. Fixture POST отправлялся существующим PveClient `_post_json`; все четыре tool-вызова отмены — **MinimalMcpServer.handle_message JSON-RPC tools/call → registry → реальная PolicyEngine → task domain → PveClient**. Прямой DELETE или вызов client.stop_task из driver не выполнялся.

Валидация выполняла реальный MCP JSON-RPC handler в локальном Python-процессе. Отдельный desktop connector/stdio с реальными отменами не проверялся и не объявляется проверенным. Driver исполнялся из stdin, постоянный исполняемый диагностический скрипт не создавался. Production-исходники и tests не редактировались.

Доказательства: [PHASE_1C_COMPLETE_LIVE_VALIDATION_EVIDENCE.json](PHASE_1C_COMPLETE_LIVE_VALIDATION_EVIDENCE.json). В JSON сохранены временные метки, безопасные HTTP metadata, точные POST parameters, ответы POST/DELETE, UPID/status/log snapshots, MCP envelopes, per-case counters, readiness, структурированные логи и восстановление политики. Authorization headers и token secret отсутствуют.

## Допуск до изменяющих запросов

Первоначальная READ-проверка началась в **21:49:10.618831**. Все девять ответов HTTP200:

| Проверка | Доказанный результат |
|---|---|
| GET `/version` | PVE **9.2.21**, release9.2, repoid4f6e0ac86f9e8c7f |
| GET `/cluster/status` | Кластер abillka94, quorum=1, четыре online-ноды: 7500T, 5800H, CeleronG3930, 7700T |
| GET `/cluster/resources?type=vm` | Единственная VMID301: qemu, node7500T, name phase1c-cancel-test, running |
| GET `/nodes/7500T/qemu/301/status/current` | running/qmpstatus running, uptime83090, HA managed=0 |
| GET `/nodes/7500T/qemu/301/config` | Нет виртуальных дисков/net; только пустой ide2=none,media=cdrom; нет lock/hookscript |
| GET `/cluster/ha/resources` | VM301 не зарегистрирована в HA |
| GET `/nodes/7500T/tasks?source=active&limit=500` | 0 активных task, конфликтов и признаков усечения нет |
| GET `/access/permissions?path=/vms/301` | Эффективные VM.PowerMgmt=true и VM.Audit=true |
| GET U0 `/status` | Исторический UPID совпадает с node/type/id/full owner, stopped/received interrupt |

Использована текущая конфигурация `config/local.yaml`, endpoint https://192.168.0.178:8006 только как транспорт. Идентичность токена проверена локально; секрет не выводился. Начальный режим READ_ONLY. Существующий verify_ssl=false не менялся. Эффективные permissions учитывают применяемые API ограничения пользователя/токена; отдельный новый аудит всех ACL и минимальных ролей не выполнялся, права не расширялись.

Перед A и перед B заново выполнены **по восемь GET**: version, cluster/status, VM inventory/status/config, HA, active tasks и permissions. Кластер/версия/цель совпали, VM running, конфигурационный digest не изменился, task-конфликтов нет, права достаточны. Исходные configuration objects в памяти до/после A и B совпали целиком; в evidence сохраняются безопасная проекция, digest и результат сравнения, без произвольных конфигурационных credentials.

## PolicyEngine и guard

Временно изменено только значение локального mode READ_ONLY → OPERATOR с сохранением исходных байтов файла в памяти. Конфигурация повторно загружена штатным load_config; создан фактически выполняемый MinimalMcpServer с реестром и PolicyEngine из неё. Проверены mode=OPERATOR, доверенный tier task_cancel=OPERATOR и успешная authorize. Enforcement не отключался.

Временный request guard проверял:

- HTTPS host192.168.0.178:8006 и разрешённые HTTP-методы;
- POST только `/api2/json/nodes/7500T/qemu/301/status/shutdown`, без query, с точным form timeout60/forceStop0;
- максимум один POST и один DELETE отдельно для A/B, максимум два каждого на пакет;
- DELETE только внутри текущего MCP-вызова L2/L4, по точному URL проверенного UPID своего случая, без body/query;
- node7500T, type qmshutdown, id301, полный token owner, running из независимого GET и получение UPID из POST;
- запрет любого DELETE в L1/L5;
- допуск к B только после PASS L1/L2/L3/L5 и повторного полного readiness.

Guard срабатывал до транспорта, счётчики резервировались до отправки, ответы сохранялись отдельно. Все четыре mutate получили HTTP200; неоднозначности отправки нет. **Guard violations: 0.** Случаи не повторялись, автоматических retry/redirect/fallback не было. Изменяющих targets на CeleronG3930/7700T/5800H и другие VM/LXC/storage/network не было.

## Точные идентификаторы задач

```text
U0 = UPID:7500T:000C3D32:01AF9A15:6AF22370:qmshutdown:301:ai-agent@pve!openwebui:
UA = UPID:7500T:000FD3F7:022E55E4:6AF367E0:qmshutdown:301:ai-agent@pve!openwebui:
UB = UPID:7500T:000FD3F9:022E5671:6AF367E2:qmshutdown:301:ai-agent@pve!openwebui:
```

UA и UB различны и получены из соответствующего POST data. До каждого DELETE независимый GET подтвердил тот же node/type/id/user/tokenid и running. UPID проверялся как исходная строка; в API path кодировался один раз. В таблице хронологии используются обозначения U0/UA/UB; JSON requests содержит decoded path, HTTPx logs — encoded URL.

## Матрица L1–L5

| Сценарий и время +03:00 | Вызов и фактические HTTP | Результат / состояние | POST / DELETE | Verdict |
|---|---|---|---|---|
| L1, 21:52:15.756468–15.782527 | task_cancel(U0,node7500T,wait=false,timeout20,poll_interval1); один GET внутри tool | false/stopped/true, exitstatus received interrupt, error=null; VM running по исходному и следующему readiness | 0 / 0 | **PASS** |
| L2, 21:52:15.942789–16.994986 | После одного POST A и независимого GET: task_cancel(UA,node7500T,wait=false,timeout20,poll_interval1); внутри GET → DELETE | true/unknown/null, exitstatus=null, wait_seconds=0, error=null; состояние VM проверено до A и в L3 | 1 / 1 для A | **PASS** |
| L3, 21:52:16.996620–17.133851 | Независимые GET UA status/log и VM status/config | stopped/received interrupt; TASK ERROR: received interrupt; VM running/qmpstatus running, uptime83276; config_unchanged=true | 0 / 0 | **PASS** |
| L5, 21:52:17.134961–17.150865 | После достоверного terminal: task_cancel(UA,node7500T,wait=false,timeout20,poll_interval1); один GET | false/stopped/true, тот же exitstatus, error=null; VM running по L3 и повторному readiness B | 0 / 0 | **PASS** |
| L4, 21:52:17.366741–17.453975; независимые READ до 17.57 | После readiness B, одного POST B и проверки UB: task_cancel(UB,node7500T,wait=true,timeout20,poll_interval1); GET → DELETE → GET | true/stopped/true, received interrupt, wait_seconds=0.027, timed_out=false, error=null; независимый GET/log подтвердил terminal; VM running, config_unchanged=true | 1 / 1 для B | **PASS** |

Все HTTP в матрице — **200**. Во всех tool-results присутствуют согласованные nullable-поля, timed_out=false; тексты сообщений не используются как доказательство причинности. Полные JSON-RPC ответы сохранены в evidence с id phase1c-complete-L1/L2/L5/L4.

### wait=false и wait=true

L2 tool ограничен request_range `[21,23)` в JSON: **только GET и DELETE**, без последующего status GET. Независимый L3 начинается после возврата MCP. Полный tool-call занял 1.0522 s, но wait_seconds=0: длительность DELETE не является polling. Инструмент правильно возвращает unknown/null, несмотря на принятие DELETE.

L4 request_range `[38,41)`: GET preflight, DELETE, затем **один GET наблюдения внутри tool**. Аргументы timeout20/poll_interval1 действительно переданы штатной реализации с monotonic deadline. Terminal наблюдён за 0.027 s; полный tool-call — 0.0872 s. Так как первый GET сразу terminal, sleep/исчерпание 20-секундного бюджета в live не происходили. Строгий deadline и timeout negative cases остаются подтверждёнными локальными тестами, а не этим быстрым live-исходом.

L1/L5 request_range `[10,11)` и `[27,28)` соответственно: по одному GET, **нулю DELETE**. Повтор выполнялся только после независимого stopped; повтор running/unknown не выполнялся.

### Фактический результат отмен

Для A и B имеются running до отмены, валидный DELETE200 data:null, последующий stopped, exitstatus received interrupt и строка task log `TASK ERROR: received interrupt`. Совокупность подтверждает прерывание обоих специально созданных worker в контролируемом сценарии. Один HTTP200 отдельно не засчитывался завершением. Это не универсальный классификатор причинности для любых задач и не гарантия rollback.

## Счётчики и итоговое состояние

| Категория | Количество |
|---|---:|
| GET, включая initial/repeated readiness, tools, independent и final READ | **42** |
| POST shutdown A | **1** |
| DELETE UA, через MCP | **1** |
| POST shutdown B | **1** |
| DELETE UB, через MCP | **1** |
| Другие mutate / повторные попытки | **0** |
| Всего HTTP | **46**, все HTTP200 |

Финальный GET в **21:52:17.572111**: VM301 phase1c-cancel-test, running/qmpstatus running, uptime83277, HA managed=0. Configuration objects после A/B совпали с соответствующими до теста и между случаями. Диски/сеть/HA/ACL не менялись; cleanup, restart, force-stop и запуск VM не выполнялись.

В finally исходные байты local.yaml восстановлены: config_bytes_restored=true, restored_policy=READ_ONLY. Создан отдельный проверочный MinimalMcpServer с восстановленным конфигом/реестром/PolicyEngine. Его authorize(task_cancel.policy) вернул PolicyDenied: restored_operator_denied=true. Для проверки deny не отправлялись tool/HTTP-запросы. OPERATOR-экземпляр прекратил работу; внешний ранее запущенный connector этим не объявляется управляемым.

## Финальные локальные проверки и Git

Полный `python -u -B -m pytest -p no:cacheprovider -q --disable-warnings` после live: **272 passed, 0 failed, 1090 warnings in 6.04s**, exit0. Предупреждения соответствуют прежнему pytest_asyncio/asyncio deprecation baseline. Исходники/tests не менялись, новые статические регрессии не вводились; Ruff/mypy не повторялись в live-этапе, прежние 9/6 диагностик не объявляются устранёнными.

Git index совпадает со снимком до работы: сохранён один ранее staged обезличенный guide. Итоговый status: **1 staged tracked, 13 unstaged tracked, 32 untracked файла**; HEAD остаётся 4561204. Commit/push/tag/reset/checkout не выполнялись. Сравнение рабочих хешей подтвердило изменение только README/docs README, создание только настоящего report и JSON evidence, отсутствие удалений. Исторические отчёты, local.yaml, source/tests и остальные существующие файлы неизменны. Обе diff --check проверки и навигационные ссылки прошли; повторная локальная READ_ONLY/PolicyDenied проверка выполнена без HTTP. В новых артефактах отсутствуют текущий token secret и Authorization headers; UTF-8 JSON корректен.

## Ограничения и завершение

Общий результат пакета **PASS**; фактические L1–L5 теперь подтверждены этим запуском, включая отдельный новый B. Это предоставляет новые доказательства для последующей приёмки, но **не является автоматической Final Acceptance** и не разрешает выпуск/commit/tag.

PVE8, реальные сетевые/ACL отказы, долгий timeout, внешняя desktop/stdio цепочка не проверялись live. Существующие verify_ssl=false и широкие ранее назначенные права не менялись. Глобальный аудит посторонних ресурсов не выполнялся; отсутствие наших неразрешённых mutate подтверждается ограниченным driver/HTTP журналом, не утверждением об отсутствии любых внешних событий в кластере.

В evidence для initial GET сохранено время получения ответа; для остальных HTTP — времена начала/окончания. Это время клиента +03:00. Часы PVE отдельно не синхронизировались; UPID starttime не используется для вывода о порядке субсекундных клиентских событий. Журнал не является подписанным append-only audit store. Значения секрета и Authorization не сохранялись, выводы ограничены представленными snapshots и проверяемым кодом.

После пакета дополнительные API-запросы не выполнялись; VM оставлена в фактически наблюдённом состоянии. Ни повторной попытки, ни очистки не было.

## Полная хронология HTTP

Ниже перечислены все запросы пакета. Идентификаторы строк — индексы `requests` в JSON (с нуля). Запросы, помеченные L1/L2/L5/L4, выполнены внутри соответствующего MCP-вызова. Для компактности общие path сокращены только в Markdown; полный path/query сохранён в JSON.

| # | Время клиента +03:00 | Фаза | Метод | Endpoint / query | HTTP |
|---:|---|---|---|---|---:|
| 0 | 21:49:10.814878+03:00 | initial_preflight | GET | `/api2/json/version` | 200 |
| 1 | 21:49:10.825134+03:00 | initial_preflight | GET | `/api2/json/cluster/status` | 200 |
| 2 | 21:49:10.840897+03:00 | initial_preflight | GET | `/api2/json/cluster/resources?type=vm` | 200 |
| 3 | 21:49:10.864585+03:00 | initial_preflight | GET | `/api2/json/nodes/7500T/qemu/301/status/current` | 200 |
| 4 | 21:49:10.889127+03:00 | initial_preflight | GET | `/api2/json/nodes/7500T/qemu/301/config` | 200 |
| 5 | 21:49:10.894712+03:00 | initial_preflight | GET | `/api2/json/cluster/ha/resources` | 200 |
| 6 | 21:49:10.903575+03:00 | initial_preflight | GET | `/api2/json/nodes/7500T/tasks?source=active&limit=500` | 200 |
| 7 | 21:49:10.909236+03:00 | initial_preflight | GET | `/api2/json/access/permissions?path=%2Fvms%2F301` | 200 |
| 8 | 21:49:10.920279+03:00 | initial_preflight | GET | `/api2/json/nodes/7500T/tasks/{U0}/status` | 200 |
| 9 | 21:52:15.720266+03:00 | verify_U0 | GET | `/api2/json/nodes/7500T/tasks/{U0}/status` | 200 |
| 10 | 21:52:15.756801+03:00 | L1 | GET | `/api2/json/nodes/7500T/tasks/{U0}/status` | 200 |
| 11 | 21:52:15.783528+03:00 | readiness_A | GET | `/api2/json/version` | 200 |
| 12 | 21:52:15.796270+03:00 | readiness_A | GET | `/api2/json/cluster/status` | 200 |
| 13 | 21:52:15.806414+03:00 | readiness_A | GET | `/api2/json/cluster/resources?type=vm` | 200 |
| 14 | 21:52:15.821935+03:00 | readiness_A | GET | `/api2/json/nodes/7500T/qemu/301/status/current` | 200 |
| 15 | 21:52:15.846019+03:00 | readiness_A | GET | `/api2/json/nodes/7500T/qemu/301/config` | 200 |
| 16 | 21:52:15.866483+03:00 | readiness_A | GET | `/api2/json/cluster/ha/resources` | 200 |
| 17 | 21:52:15.872004+03:00 | readiness_A | GET | `/api2/json/nodes/7500T/tasks?source=active&limit=500` | 200 |
| 18 | 21:52:15.882887+03:00 | readiness_A | GET | `/api2/json/access/permissions?path=%2Fvms%2F301` | 200 |
| 19 | 21:52:15.890150+03:00 | create_A | POST | `/api2/json/nodes/7500T/qemu/301/status/shutdown` | 200 |
| 20 | 21:52:15.922610+03:00 | verify_A | GET | `/api2/json/nodes/7500T/tasks/{UA}/status` | 200 |
| 21 | 21:52:15.943084+03:00 | L2 | GET | `/api2/json/nodes/7500T/tasks/{UA}/status` | 200 |
| 22 | 21:52:15.967477+03:00 | L2 | DELETE | `/api2/json/nodes/7500T/tasks/{UA}` | 200 |
| 23 | 21:52:16.996862+03:00 | L3 | GET | `/api2/json/nodes/7500T/tasks/{UA}/status` | 200 |
| 24 | 21:52:17.031415+03:00 | L3 | GET | `/api2/json/nodes/7500T/tasks/{UA}/log?start=0&limit=5000` | 200 |
| 25 | 21:52:17.061952+03:00 | L3 | GET | `/api2/json/nodes/7500T/qemu/301/status/current` | 200 |
| 26 | 21:52:17.098276+03:00 | L3 | GET | `/api2/json/nodes/7500T/qemu/301/config` | 200 |
| 27 | 21:52:17.135251+03:00 | L5 | GET | `/api2/json/nodes/7500T/tasks/{UA}/status` | 200 |
| 28 | 21:52:17.154031+03:00 | readiness_B | GET | `/api2/json/version` | 200 |
| 29 | 21:52:17.170954+03:00 | readiness_B | GET | `/api2/json/cluster/status` | 200 |
| 30 | 21:52:17.183300+03:00 | readiness_B | GET | `/api2/json/cluster/resources?type=vm` | 200 |
| 31 | 21:52:17.208830+03:00 | readiness_B | GET | `/api2/json/nodes/7500T/qemu/301/status/current` | 200 |
| 32 | 21:52:17.236258+03:00 | readiness_B | GET | `/api2/json/nodes/7500T/qemu/301/config` | 200 |
| 33 | 21:52:17.260278+03:00 | readiness_B | GET | `/api2/json/cluster/ha/resources` | 200 |
| 34 | 21:52:17.268038+03:00 | readiness_B | GET | `/api2/json/nodes/7500T/tasks?source=active&limit=500` | 200 |
| 35 | 21:52:17.279475+03:00 | readiness_B | GET | `/api2/json/access/permissions?path=%2Fvms%2F301` | 200 |
| 36 | 21:52:17.290032+03:00 | create_B | POST | `/api2/json/nodes/7500T/qemu/301/status/shutdown` | 200 |
| 37 | 21:52:17.329918+03:00 | verify_B | GET | `/api2/json/nodes/7500T/tasks/{UB}/status` | 200 |
| 38 | 21:52:17.367035+03:00 | L4 | GET | `/api2/json/nodes/7500T/tasks/{UB}/status` | 200 |
| 39 | 21:52:17.391644+03:00 | L4 | DELETE | `/api2/json/nodes/7500T/tasks/{UB}` | 200 |
| 40 | 21:52:17.426838+03:00 | L4 | GET | `/api2/json/nodes/7500T/tasks/{UB}/status` | 200 |
| 41 | 21:52:17.455603+03:00 | L4_independent | GET | `/api2/json/nodes/7500T/tasks/{UB}/status` | 200 |
| 42 | 21:52:17.481686+03:00 | L4_independent | GET | `/api2/json/nodes/7500T/tasks/{UB}/log?start=0&limit=5000` | 200 |
| 43 | 21:52:17.508530+03:00 | L4_independent | GET | `/api2/json/nodes/7500T/qemu/301/status/current` | 200 |
| 44 | 21:52:17.543462+03:00 | L4_independent | GET | `/api2/json/nodes/7500T/qemu/301/config` | 200 |
| 45 | 21:52:17.572111+03:00 | final_READ | GET | `/api2/json/nodes/7500T/qemu/301/status/current` | 200 |
