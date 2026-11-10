# Phase 1C — Live Validation B: task_cancel

> Дата: 2026-11-09, Europe/Moscow
> Начало единственной попытки: 22:47:59 +03:00
> Результат: **PASS для одного разрешённого сценария task_cancel wait=true**
> Цель: только 7500T / VM301 phase1c-cancel-test

## Основание и предел результата

Пользователь явно разрешил один qmshutdown с timeout=60/forceStop=0 и не более одного task_cancel подтверждённого UPID. Изучены workflow, Live Plan, реализация, отчёт Administrator и диагностика VM301. В этот раз актуальный preflight подтвердил running; прежний stopped-снимок не использовался как текущее состояние.

Выполнен один контролируемый тест через установленную конфигурацию и код проекта, без повторов. PASS основан не только на HTTP200 DELETE: получены terminal task status, exitstatus received interrupt и соответствующая запись task log. VM осталась running, конфигурация до/после совпадает.

Это не Acceptance всей Phase 1C и не live-покрытие остальных ошибок/режимов. Отдельный wait=false тест, повторная отмена, тесты других задач/нод не выполнялись. Не создавались новые VM, не менялись VM config, ACL, сеть, storage или пользователи. Не было force-stop, запуска VM, reboot, backup/migration, cleanup либо commit/push/tag.

## Предварительные GET-проверки

Все 7 первоначальных GET завершились HTTP200:

| GET /api2/json + путь | Подтверждение |
|---|---|
| /version | PVE 9.2.21, release 9.2, repoid 4f6e0ac86f9e8c7f |
| /cluster/resources?type=vm | VM301/qemu/name phase1c-cancel-test находится на 7500T, running |
| /nodes/7500T/qemu/301/status/current | running/qmpstatus running, uptime145, HA managed=0 |
| /nodes/7500T/qemu/301/config | нет virtual disks/net; только ide2=none,media=cdrom; hookscript отсутствует, lock отсутствует |
| /cluster/ha/resources | записи vm:301/ct:301 отсутствуют |
| /access/permissions?path=/vms/301 | VM.PowerMgmt и VM.Audit есть |
| /nodes/7500T/tasks?source=active&limit=500 | конфликтующих задач с id301 нет |

Пустой CD-ROM ide2 не содержит образа или virtual disk. Он не удалялся и не перенастраивался. Перед POST повторно выполнены 4 GET: status/current, config, HA resources, active tasks. Состояние вновь running/qmpstatus running, uptime219, имя/node корректны, блокировки/диски/сеть/hookscript/HA/конфликт отсутствуют.

Конфигурация загружена из config/local.yaml; endpoint https://192.168.0.178:8006 использован только как транспорт, token identity проверена без вывода секрета. Начальный PolicyMode READ_ONLY. Существующий verify_ssl=false сохранён; отдельная проверка доверия TLS в этом тесте не выполнялась, прежнее TLS-ограничение не объявляется устранённым. Тест выполнен по явному разрешению с текущей конфигурацией.

## Policy enforcement и исполняемый MCP

После успешного preflight в config/local.yaml временно заменено только значение mode READ_ONLY на OPERATOR. Файл повторно загружен штатным load_config; создан исполняемый MinimalMcpServer с create_default_registry и PolicyEngine из этой конфигурации. Его фактический policy.mode=OPERATOR; authorize(task_cancel.policy) прошёл, tier инструмента не менялся.

task_cancel вызван JSON-RPC tools/call через **штатный MinimalMcpServer.handle_message**, Registry → PolicyEngine → domain → PveClient. Прямой client.stop_task или прямой DELETE из диагностического кода не вызывались. Проверялся реальный JSON-RPC handler в локальном Python-процессе; отдельное подключение Codex desktop plugin/stdio transport этим тестом не валидируется. HTTP-клиент внедрён штатным параметром PveClient для ограничения маршрутов и регистрации ответов.

Guard разрешал произвольные диагностические GET только на подтверждённом API-host, а mutate — исключительно один POST точного shutdown endpoint с точными form values и один DELETE полного подтверждённого task URL. Другие HTTP-методы/targets/repeats блокировались до сети. Логи собраны в памяти JSON formatter без Authorization или token secret.

## Создание единственной задачи

Время старта task из API: epoch1794253680 = **2026-11-09 22:48:00 +03:00**.

```http
POST /api2/json/nodes/7500T/qemu/301/status/shutdown
Content-Type: application/x-www-form-urlencoded

timeout=60&forceStop=0
```

Ответ: **HTTP200**.

```json
{"data":"UPID:7500T:000C3D32:01AF9A15:6AF22370:qmshutdown:301:ai-agent@pve!openwebui:"}
```

Точный UPID:

```text
UPID:7500T:000C3D32:01AF9A15:6AF22370:qmshutdown:301:ai-agent@pve!openwebui:
```

Проверены все сегменты: node7500T, type qmshutdown, id301, ожидаемый полный token owner. Независимый GET task/status вернул HTTP200 и status=running, node7500T/type qmshutdown/id301/user ai-agent@pve/tokenid openwebui. Поэтому отмена допущена только для этой задачи. Чужие/старые UPID не использовались.

## Вызов task_cancel и HTTP DELETE

JSON-RPC request id/correlation: phase1c-stage-b-301. Аргументы: полученный UPID, node7500T, wait=true, timeout20, poll_interval1.

Domain сам повторно сделал preflight GET status (HTTP200) и только затем один DELETE:

```http
DELETE /api2/json/nodes/7500T/tasks/{URL-encoded confirmed UPID}
```

Ответ: **HTTP200**, `{"data":null}`. В транспортном журнале pve_delete: phase=delete, request_outcome=accepted, http_status=200, kind=null, correlation_id=phase1c-stage-b-301.

Фактический результат MCP tool:

```json
{
  "cancel_requested": true,
  "error": null,
  "exitstatus": "received interrupt",
  "message": "Наблюдается завершение задачи; причина не установлена",
  "node": "7500T",
  "status": "stopped",
  "stopped": true,
  "timed_out": false,
  "upid": "UPID:7500T:000C3D32:01AF9A15:6AF22370:qmshutdown:301:ai-agent@pve!openwebui:",
  "wait_seconds": 0.019
}
```

0.019 s — время domain-наблюдения, не полная длительность POST+DELETE. Нейтральное message сохраняет согласованный контракт и не переименовано в cancelled.

## Независимое наблюдение и состояние после

После domain polling выполнен независимый GET task/status: HTTP200, status=stopped, exitstatus=received interrupt, тот же node/type/id/user/token. GET task/log: HTTP200, одна строка:

```text
TASK ERROR: received interrupt
```

В данном контролируемом запуске сочетание running до DELETE, принятого единственного DELETE, последующего terminal и received interrupt подтверждает корректный результат теста остановки worker. ERROR в task log ожидаем для прерванного qmshutdown и не означает ошибку MCP transport. Это не утверждение об универсальной причинной классификации любой завершённой PVE task и не проверка rollback.

GET VM status/current после теста: vmid301/name phase1c-cancel-test, **running/qmpstatus running**, uptime220, HA managed=0. GET config выполнен повторно; объект config до/после идентичен, включая digest. Диски/сеть не подключались, принудительная остановка не применялась. Глобальный аудит всех посторонних ресурсов не выполнялся, поэтому абсолютное отсутствие любых независимых внешних изменений не заявляется; guard подтверждает отсутствие наших mutate к иным targets.

## Точное количество запросов

| Категория | Количество | HTTP |
|---|---:|---|
| Первоначальный GET preflight | 7 | все200 |
| GET в исполняющем тестовом процессе | 11 | все200 |
| POST qmshutdown | **1** | 200 |
| DELETE task, только через MCP | **1** | 200 |
| Другие mutate | **0** | — |
| Всего GET / mutate | **18 / 2** | все20 ответов HTTP200 |

Нет повторных тестовых попыток и автоматического retry DELETE. На CeleronG3930/7700T/5800H и другие объекты 7500T изменяющие запросы не отправлялись. Физическая точка API-входа не использовалась как node target.

## Возврат READ_ONLY

В finally исходные bytes config/local.yaml восстановлены: config_bytes_restored=true. Штатный load_config после возврата вернул READ_ONLY. OPERATOR-экземпляр завершён; создан проверочный MinimalMcpServer с восстановленной конфигурацией/PolicyEngine. authorize для его task_cancel.policy вызвал PolicyDenied (restored_operator_denied=true). Повторного вызова tool или DELETE для проверки deny не делалось.

Итоговые проверки: restored_policy=READ_ONLY, config_current_readonly=true. Восстановлены исходные credentials/TLS/прочие параметры без изменения. Исходники не редактировались; проверка git diff по рабочей конфигурации не должна трактоваться как очистка ранее существовавшей работы.

## Доказательства, ограничения и verdict

Машиночитаемый журнал этой единственной попытки: [PHASE_1C_STAGE_B_EVIDENCE.json](PHASE_1C_STAGE_B_EVIDENCE.json). Содержит безопасный method/path/status, POST/DELETE response, UPID, MCP/domain result, task status/log, VM before/after и подтверждение возврата режима. Секрет/Authorization не сохранялись. После записи проверено отсутствие текущего token secret в артефактах без вывода его значения.

**PASS** относится только к одному task_cancel wait=true в указанных условиях. Нет timeout/unknown/продолжающейся task: оба GET-наблюдения подтверждают stopped, журнал — interrupt. VM продолжает running; очистка не требовалась и запрещённые дополнительные действия не выполнялись. Смена Administrator ACL была ранее сделана пользователем, этим тестом ACL не менялись.

Не проверены отдельный wait=false live, repeated cancel, ошибка прав/сети, PVE8, внешний Codex plugin/stdio transport и доверие TLS. Нельзя объявлять Acceptance или полное прохождение всех пунктов общего Live Plan. После этой одной попытки работа остановлена; новый тест, любые иные mutate и commit требуют нового разрешения.
