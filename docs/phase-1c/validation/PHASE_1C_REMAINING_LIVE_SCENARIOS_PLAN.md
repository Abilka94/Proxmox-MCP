# Phase 1C — Remaining Live Scenarios Plan

> Дата: 2026-11-09
> Статус: **подготовлен, не выполнен; требуется отдельное разрешение**
> Не является разрешением POST, DELETE, изменения PolicyMode или состояния VM

## Основание и точный объём

Источник L1–L5: [действующий Live Validation Plan, раздел D и минимум раздела E](PHASE_1C_LIVE_VALIDATION_PLAN.md). Их определения не заменяются mock-сценариями. [Stage B](PHASE_1C_LIVE_VALIDATION_STAGE_B_REPORT.md) уже подтвердил один wait=true на собственной qmshutdown task. Новый план закрывает буквальную полную последовательность без автоматического принятия ограничений от имени пользователя.

Цель будущих изменяющих операций: **только 7500T / VM301 phase1c-cancel-test**. Для полной проверки предложены два явно раздельных случая A и B, каждый максимум один POST shutdown и один task_cancel. Это два заранее согласуемых случая, а не повтор failed/unknown операции. Любая дополнительная попытка требует нового разрешения.

5800H допускается только для READ; CeleronG3930/7700T запрещены для тестовых mutate. API-вход через 192.168.0.178:8006 является транспортом, не целевой нодой. Эти ограничения относятся к данной проверке; в production-код постоянные ограничения по нодам не добавляются.

При желании пользователя сократить объём до одного нового случая A возможно отдельно принять историческое функциональное подтверждение wait=true как достаточное для L4. **Такое решение сейчас не принято**; план по умолчанию описывает оба случая для полного покрытия.

## Предварительный допуск — только GET

Все API-пути ниже включают префикс `/api2/json`. Использовать текущую конфигурацию и PveClient проекта, не старые скрипты; credentials/headers не выводить. Перед каждой test task повторить проверки:

| GET endpoint | Требование |
|---|---|
| `/version` | Подтверждён ожидаемый кластер/PVE 9.x; версия сохранена |
| `/cluster/resources?type=vm` | VM301 существует на 7500T, имя phase1c-cancel-test |
| `/nodes/7500T/qemu/301/status/current` | running, qmpstatus running; HA не управляет VM |
| `/nodes/7500T/qemu/301/config` | Нет дисков и net-устройств, lock/hookscript; допустим только пустой ide2=none,media=cdrom как прежде |
| `/cluster/ha/resources` | Нет vm:301/ct:301 |
| `/nodes/7500T/tasks?source=active&limit=500` | Нет конфликтующих активных задач VM301; при неполноте списка/неясности — STOP |
| `/access/permissions?path=/vms/301` | Эффективные VM.PowerMgmt и VM.Audit; privsep учитывается, права токена не превышают права пользователя |

Рабочая VM должна быть уже running. Запуск stopped VM не входит в план. Старое состояние Stage B не подменяет текущий GET. При любом несоответствии **STOP до POST**. ACL/токены/TLS не исправлять автоматически. Текущий verify_ssl=false остаётся известным ограничением; изменение TLS-политики — отдельное решение.

Владельцем каждой новой task должен быть ожидаемый полный token identity из текущей конфигурации, включая tokenid. Собственная task позволяет опираться на ownership; для чужих задач потребовались бы Sys.Modify/Sys.Audit на ноде, но чужие задачи здесь запрещены. Administrator не назначать и не считать минимально необходимой ролью. Если имеющихся эффективных прав недостаточно — STOP без расширения ACL.

## Policy и ограничение запросов

Отдельное разрешение должно включать временный **локальный** OPERATOR штатным изменением конфигурации/пересозданием исполняемого MCP. Проверить registry tier OPERATOR и фактическую PolicyEngine instance. Не отключать enforcement и не менять Proxmox global settings. finally восстанавливает исходный READ_ONLY и проверяет deny без HTTP.

Исполняющий тестовый процесс должен ограничить mutate точным host/node/VM и подтверждёнными UPID, с независимыми счётчиками для A/B. Это временный тестовый guard, не изменение production MCP. Для L1/L5 guard запрещает любой DELETE: если код неожиданно его запрашивает — блокировать до сети, FAIL и STOP.

Fixture POST выполняется существующим PveClient `_post_json`, как в Stage B, по отдельному разрешению создания task. Он не становится новым MCP tool. **Отмена всегда только JSON-RPC tools/call → task_cancel → PolicyEngine → domain → PveClient**; прямой DELETE/stop_task из driver запрещён.

## Идентификаторы и маршруты

Исторический U0 из Stage B:

```text
UPID:7500T:000C3D32:01AF9A15:6AF22370:qmshutdown:301:ai-agent@pve!openwebui:
```

U_A и U_B получают только из data соответствующего нового POST. До отмены проверить node7500T, type qmshutdown, id301, полный owner и числовые сегменты UPID; GET `/nodes/7500T/tasks/{encoded_upid}/status` должен подтвердить ту же identity и running. `encoded_upid = quote(исходный_UPID, safe='')`, ровно один раз. Старый или произвольный UPID вместо ответа POST недопустим.

## Операции и критерии

### L1 — уже завершённая задача

1. Цель: 7500T/301, U0. GET `/nodes/7500T/tasks/{encoded_U0}/status` — требуется stopped и совпадение identity. Если задача недоступна/удалена из журнала, STOP данного сценария; не создавать замену автоматически.
2. После отдельного разрешения вызвать MCP `task_cancel(upid=U0,node="7500T",wait=false,timeout=20,poll_interval=1)`.
3. Ожидаемый API-вызов handler: только GET того же `/status`; **DELETE не разрешён**. Результат false/stopped/true, exitstatus из GET, error=null.
4. Последствия не ожидаются. Любой DELETE блокируется guard; при HTTP/input/policy error — FAIL/STOP. Сохранить MCP-result, число GET и нулевое число DELETE. Инструмент OPERATOR требует отдельного разрешения даже для этого no-op случая.

### L2 — случай A, wait=false

| Параметр | Точный план |
|---|---|
| Node / VMID | 7500T / 301 |
| Создание task | **POST** `/nodes/7500T/qemu/301/status/shutdown` |
| Form parameters | `timeout=60`, `forceStop=0` |
| Проверка UPID | U_A только из POST; сверка node/type/id/owner, независимый GET `/nodes/7500T/tasks/{encoded_U_A}/status` |
| Отмена | MCP `task_cancel(upid=U_A,node="7500T",wait=false,timeout=20,poll_interval=1)` ровно один раз |
| API отмены внутри MCP | **DELETE** `/nodes/7500T/tasks/{encoded_U_A}`, без body/query; только после собственного preflight GET |
| Ожидаемый результат | HTTP200 data:null; cancel_requested=true, status=unknown, stopped=null, wait_seconds=0, без polling |
| Последствия | Штатный shutdown способен завершить VM, если она ответит; отмена worker не является rollback. forceStop=0 исключает согласие на принудительный stop |
| STOP | Любой identity mismatch; задача уже stopped до отмены; неизвестный исход/ошибка POST или DELETE; нарушение guard; неожиданный ресурс/состояние |
| Проверка | Полная HTTP sequence, безопасный MCP envelope, далее L3 |
| Разрешение | **Обязательно отдельное**: один POST и максимум один DELETE для A |

Если задача завершилась до отмены, DELETE не отправлять. Такой исход не доказывает L2; не запускать новую task для повтора без нового разрешения. При unknown POST не создавать вторую task.

### L3 — независимый READ после A

Для U_A выполнить GET `/nodes/7500T/tasks/{encoded_U_A}/status` и `/log?start=0&limit=5000`, а также VM `/status/current` и `/config`. Сохранить фактические status/exitstatus и безопасный журнал. Для краткого READ-наблюдения ограничить срок 20 сек, интервал 1 сек; при недоступности/ошибке или истечении срока завершить наблюдение, не повторять mutate. Наблюдённый terminal не объявлять универсальным доказательством причинности.

Если task всё ещё running, финальное состояние неизвестно или VM stopped — STOP дальнейших mutate, сообщить пользователю; никаких cleanup/restart/force-stop. Сравнивать нужные поля конфигурации и digest, не сохранять возможные credentials из произвольного config/log. READ разрешение и привязка к A должны входить в согласованный запуск.

### L5 — повтор для уже terminal U_A

Только если независимый GET уже доказал stopped, повторить MCP `task_cancel(upid=U_A,node="7500T",wait=false,timeout=20,poll_interval=1)` один раз. Handler должен выполнить только GET `/nodes/7500T/tasks/{encoded_U_A}/status`; ожидание false/stopped/true, прежний фактический exitstatus. DELETE запрещён guard.

Если U_A running/unknown, повтор tool **не разрешён** этим планом, поскольку может создать второй DELETE. Не выполнять повтор при неопределённости. Эффект ожидается no-op; любые отклонения — STOP. Дополнительное разрешение пользователя обязательно.

### L4 — отдельный случай B, wait=true

Повторить полный READ-допуск. Если VM301 не running, STOP без запуска. После отдельного разрешения выполнить ровно один POST `/nodes/7500T/qemu/301/status/shutdown`, параметры `timeout=60,forceStop=0`. Получить U_B, доказать U_B != U_A, ту же цель/owner и running через GET.

Один MCP `task_cancel(upid=U_B,node="7500T",wait=true,timeout=20,poll_interval=1)`: свой preflight GET, максимум один DELETE `/nodes/7500T/tasks/{encoded_U_B}`, затем ограниченное GET-наблюдение `/status`. Успех запроса — только валидный data:null; terminal/exitstatus — только наблюдение. Unknown DELETE не повторять и не маскировать polling. timed_out/observation error не считать PASS успешной отмены.

Последствия и STOP-условия те же, что A. После результата — независимые GET status/log/VM status/config. При running/unknown worker не исправлять состояние дополнительным mutate. Для B необходимо отдельное явное разрешение на один POST и максимум один DELETE; историческое разрешение Stage B не переносится на этот случай.

## Завершение и лимиты

- Полный вариант: максимум **2 POST + 2 DELETE** на 7500T/301, только при отдельном согласовании A/B; L1/L5 — по нулю DELETE.
- Нет автоматического retry, второй попытки внутри случая или перехода B после ошибки A. Никаких действий на других VM/LXC/storage/network/nodes.
- В finally восстановить READ_ONLY, пересоздать MCP, локально проверить отказ OPERATOR. Не отправлять реальный DELETE для проверки deny.
- VM не удалять, не запускать и не останавливать ради очистки. Ничего не коммитить/тегировать.
- Отчёт будущего выполнения должен содержать время каждого шага, UPID, args без секретов, HTTP statuses, MCP result, независимые READ snapshots, счётчики mutate и доказательство возврата политики.

До разрешения все пункты остаются **NOT EXECUTED**. Этот документ — готовый план согласования, не исполняемый диагностический скрипт и не факт новой Live Validation.
