# Phase 1C — выбор тестовой задачи Live Validation B

> Дата: 2026-11-02; автор: Codex
> Статус: сценарий предложен для отдельного согласования; B не начат
> Primary node: **7500T**; reserve: **5800H**
> **CeleronG3930 и 7700T запрещены для создания, изменения и остановки любых тестовых задач.**

## Итоговое решение

Рекомендуемый кандидат — worker **qmshutdown** для специально подготовленной одноразовой QEMU VM на 7500T: без ОС, виртуальных дисков, CD/ISO, сетевых интерфейсов, passthrough, hookscript, HA и автозапуска. Shutdown вызывается с timeout=60 и forceStop=0; task_cancel останавливает только этот заранее проверенный UPID. Рабочие VM/LXC, backup, migration, обновления и дисковые операции для получения UPID не используются.

Это **условно пригодный сценарий, не доказанная live-отмена**. Поддержка endpoints/параметров подтверждена установленной схемой; достаточно длинное выполнение на diskless VM — инженерная гипотеза, которую нельзя объявлять доказанной без разрешённого создания task. Если worker завершится слишком быстро, тест отмены не засчитывается, настройки рабочих ресурсов не меняются и другая произвольная задача не подставляется.

Тестовая VM сейчас не существует. Её создание/запуск/очистка — отдельные действия администратора тестового окружения, требующие разрешения; они не добавляются как новые MCP tools и не меняют scope реализации Phase 1C. Если пользователь не разрешает даже такую одноразовую fixture, текущий сценарий B остаётся BLOCKED: достоверно пригодный штатный no-op task без fixture не установлен.

## Изученные документы и границы

Прочитаны README.md, docs/README.md, PROJECT_WORKFLOW_RULES.md, REFERENCE_USAGE_POLICY.md, Design v0.3, Final Remediation Report, Live Validation Plan и последний Connectivity Recheck Report. Отчёт размещён в validation/ согласно структуре фазы. [Live Plan](PHASE_1C_LIVE_VALIDATION_PLAN.md), [READ connectivity](PHASE_1C_PVE_CONNECTIVITY_RECHECK_REPORT.md), [remediation](../implementation/PHASE_1C_FINAL_REMEDIATION_REPORT.md).

Использованы load_config/PveClient с config/local.yaml и GET к https://192.168.0.178:8006. Адрес — только транспортный вход, не тестовая нода. Все HTTP-запросы этого этапа — GET. Нодальные запросы на CeleronG3930/7700T блокировались диагностическим guard; глобальные GET inventory/schema/HA не изменяют эти ноды. Секреты, headers, полные UPID и содержимое журналов не сохранялись. Код, config/local.yaml, ACL, токены, PolicyMode не менялись. Нет POST/PUT/PATCH/DELETE, SSH, kill, commit/push/tag и запуска B.

## Фактические результаты READ на 7500T

Все перечисленные успешные GET вернули HTTP 200:

| Запрос | Результат |
|---|---|
| /api2/json/version | PVE 9.2.21, release 9.2, repoid 4f6e0ac86f9e8c7f |
| /api2/json/nodes | точные 7500T и 5800H существуют, online |
| /api2/json/nodes/7500T/version | также 9.2.21/9.2, тот же repoid |
| /nodes/7500T/status | uptime 2639642 s, CPU 0 в момент снимка; loadavg 0.04/0.04/0.00; RAM total 16650129408, available 14606270464 bytes |
| /nodes/7500T/qemu | пустой список |
| /nodes/7500T/lxc | пустой список |
| /nodes/7500T/tasks?source=active&limit=50 | 0 задач |
| /nodes/7500T/tasks?source=all&limit=50 | 50 записей: aptupdate 48, startall 2; running не обнаружен в выборке |
| /nodes/7500T/storage | local-lvm/lvmthin active, local/dir active, backup-share/dir shared active |
| /nodes/7500T/services | системные службы доступны; среди running — corosync, pve-cluster, pvedaemon, pveproxy, pvescheduler, pvestatd, HA daemons, firewall |
| /cluster/ha/resources | 0 записей |
| /access/permissions?path=/nodes/7500T | Audit-привилегии; Sys.Modify/Sys.Console отсутствуют |
| /access/permissions?path=/vms | Audit-привилегии; VM.PowerMgmt/VM.Allocate отсутствуют |
| /pve-docs/api-viewer/apidoc.js | HTTP 200, 4346888 bytes; apiSchema успешно разобрана |

Отдельный GET метаданных /access/users/ai-agent@pve/token/openwebui вернул **HTTP 403**: privsep/expiry этим способом не проверены. Не делается вывод, что токен недействителен: остальные авторизованные GET успешны. Текущая роль PVEAuditor задана пользователем; READ API подтверждает effective grants, а не доказательство состава всех ACL/ролей.

На 7500T не обнаружено зарегистрированных VM/LXC, но это не означает отсутствие рабочих сервисов. Нельзя менять системные службы, сеть, содержимое local/local-lvm и особенно shared backup-share. Нулевая active-выборка и история 50 записей — моментальный снимок, не гарантия на время B. Backup 5800H подтверждён online только глобальным GET; перед резервным сценарием нужен такой же READ preflight. Автоматического переноса теста на резерв нет.

## Доказательства API и ограничения источников

Установленная apiSchema подтверждает:

- POST /nodes/{node}/qemu — create_vm, строковый результат; VM.Allocate на /vms/{vmid} либо pool; при создании дисков отдельно Datastore.AllocateSpace, при bridge/vlan — SDN.Use.
- POST /nodes/{node}/qemu/{vmid}/status/start, shutdown, stop — VM.PowerMgmt на /vms/{vmid}; shutdown имеет timeout и forceStop (default 0), результат string.
- DELETE /nodes/{node}/qemu/{vmid} — VM.Allocate; это потенциально удаление VM и её ресурсов, разрешается только для fixture без volumes.
- DELETE /nodes/{node}/tasks/{upid} — null; для чужого task требуется Sys.Modify на /nodes/{node}.
- POST /nodes/{node}/termproxy и vncshell имеют allowtoken=1 и Sys.Console; прежнее общее предположение о невозможности token-auth console нельзя применять к этой установленной схеме.

Официальные исходники: [Qemu API](https://github.com/proxmox/qemu-server/blob/master/src/PVE/API2/Qemu.pm), [QemuServer](https://github.com/proxmox/qemu-server/blob/master/src/PVE/QemuServer.pm), [Nodes API](https://github.com/proxmox/pve-manager/blob/master/PVE/API2/Nodes.pm), [termproxy](https://github.com/proxmox/pve-xtermjs/blob/master/termproxy/src/main.rs). Это upstream master, не точный снимок установленных qemu-server/termproxy пакетов.

Qemu API указывает proxyto=node, возвращает fork_worker qmshutdown для не-HA VM; paused VM без forceStop отклоняется. QemuServer использует system_powerdown при отсутствии guest agent, ждёт timeout, а без force при истечении времени возвращает ошибку. Для diskless BIOS VM ожидание вероятно, но не гарантировано. API create дополнительно проверяет конфигурационные параметры; одна VM.Allocate не является универсальным разрешением любого custom-конфига.

Nodes API для termproxy создаёт worker локально на entrypoint и готовит remote shell tunnel при другом node; termproxy upstream ждёт клиента примерно 10 s, затем только после authentication запускает terminal command. Таким образом, консольный proxy не гарантирует размещение UPID на разрешённой ноде. Это существенное ограничение topology, а не запрет самой token-auth.

## Сравнение кандидатов

| Кандидат | Поддержка / права | Изоляция, длительность, прерывание и cleanup | Решение |
|---|---|---|---|
| qmshutdown отдельной diskless VM | установленная схема; VM.PowerMgmt на одном VMID; собственный task cancel без Sys.Modify | только fixture, небольшие CPU/RAM и конфиг; timeout=60/forceStop=0; состояние fixture после отмены проверяется, затем отдельные stop/destroy | выбран условно |
| Создание/запуск/stop diskless VM как target cancel | create/start/stop в схеме; Allocate/Config или PowerMgmt | ограничимы fixture, но обычно короткие; отмена provisioning может оставить partial config/process | только подготовка/cleanup, не target |
| termproxy без WebSocket | схема allowtoken=1, Sys.Console на node | нет guest volumes; короткий timeout; привилегия чувствительна; UPID может быть на запрещённом entrypoint, возможен server-side SSH tunnel | отклонён для этой топологии |
| vncshell/VNC | схема allowtoken=1, Sys.Console | shell/console и worker placement; ненужная зона доступа, риск на entrypoint | отклонён |
| startall на пустой 7500T | установленная схема; PowerMgmt на / либо явно выбранных VMID | короткий task, пустота node может измениться, риск запуска неожиданного guest | отклонён |
| aptupdate | установленная схема; Sys.Modify node | изменяет package cache узла, рабочие обновления запрещены | отклонён |
| Backup/restore/migration/clone/snapshot/download/disk task | часть штатных API, но не исследовалась как допустимая цель | storage/network/volumes, незавершённые объекты и недопустимые побочные эффекты | исключены условиями пользователя |
| Generic sleep/no-op worker через API | подтверждённого установленного маршрута нет | не придумывать endpoint, не заменять SSH/kill/произвольным shell | не пригоден без доказательств |

Для выбранного qmshutdown отмена worker не является rollback и не обещает сохранение VM running. Допустимо любое проверенное конечное состояние только одноразовой fixture; неизвестное состояние означает stop test и READ-диагностику. Никакой произвольный существующий UPID не используется.

## Минимальная модель прав

Основной принцип: **provision/cleanup делает отдельно уполномоченный оператор; тестовый токен создаёт только qmshutdown и отменяет свой UPID**. Это исключает необходимость VM.Allocate/Config для токена и не даёт ему доступ к рабочим storage/VM.

| Субъект/операция | Минимальное требование |
|---|---|
| ai-agent@pve, выполнение shutdown/start при необходимости | VM.PowerMgmt на /vms/<TEST_VMID>; Audit уже есть |
| ai-agent@pve!openwebui | тот же VM.PowerMgmt на одном /vms/<TEST_VMID>, при separated privileges — пересечение с владельцем |
| task_cancel собственного qmshutdown | подтверждённый полный token owner; Sys.Modify заранее не назначать |
| Чтение status/log | собственный task либо имеющийся Sys.Audit |
| Создание/настройка fixture оператором | VM.Allocate на выделенном VMID + необходимые VM.Config.* для выбранных параметров; точные effective права проверяет оператор, не расширять token |
| Stop/delete fixture оператором | VM.PowerMgmt и VM.Allocate на том же VMID; никаких используемых volumes |
| Назначение временных ACL | только существующий уполномоченный администратор; этому действию требуется отдельное разрешение |

Не предлагаются Administrator, PVEAdmin, VM.PowerMgmt на /, Sys.Modify на node, storage privileges или отключение privsep. Если privsep неизвестен, администратор сначала подтверждает его READ-метаданными: token не может превысить права user. Для non-separated token выдача user PowerMgmt также затрагивает другие его full-privilege tokens — оценить перед изменением.

Права /vms/<TEST_VMID> глобальны по VMID, а не node; привязку к 7500T обеспечивает сценарий и preflight, не такой ACL. VM не мигрируется, HA не включается, node/UPID проверяется перед каждым mutate. User и token — разные owners: qmshutdown должен создаваться именно текущим token, а не оператором через UI. Чужую задачу не отменять и не добавлять Sys.Modify ради обхода.

## Точный план после отдельного одобрения

1. Утвердить allowlist: только 7500T; 5800H — отдельный резервный запуск с новым разрешением и preflight. CeleronG3930/7700T не могут быть целями fixture/task/cleanup. 192.168.0.178 — только HTTP entrypoint. Каждый mutating endpoint должен иметь проверенную node-routing семантику; console proxies запрещены сценарием.
2. Решить TLS trust: текущий verify_ssl=false сохранён, предыдущее системное certificate verification не прошло. Перед чувствительными правами/операциями отдельно одобрить доверенный TLS либо явно принять существующий режим. Проверить, что Codex использует правильный MCP checkout и конфиг.
3. Повторить GET version, exact node/status/qemu/lxc/tasks/permissions и наличие свободной ёмкости. Изменение inventory/нагрузки/активных операций — stop. Выбрать свободный cluster-wide TEST_VMID через GET nextid + inventory; не резервировать и не использовать конкретное число заранее.
4. Отдельно разрешённый оператор создаёт fixture на 7500T. Предлагаемый профиль: имя phase1c-cancel-test, 1 vCPU, memory=128 MiB, balloon=0, cpulimit=0.1, BIOS seabios, ACPI=1, agent=0, onboot=0, start=0, vga=none. Не задавать disk/ISO/net/hostpci/usb/serial/hookscript/HA/storage/pool. Если установленная схема/оператор не допускают профиль, не подбирать рабочую VM; остановиться для согласования. Чтением полного конфига проверить отсутствие volumes/net и привязку node.
5. Администратор отдельно выдаёт user и separated token custom-role только VM.PowerMgmt на /vms/<TEST_VMID>, сохраняя текущие Audit grants и исходные ACL. Срок и отзыв фиксируются. Оператор запускает fixture штатным API только на 7500T; дождаться завершения startup UPID. GET status/current должен показывать running, не paused; повторно проверить HA/config/no volumes/no network.
6. Только после отдельного разрешения временно включить OPERATOR в MCP и перезапустить нужный процесс. READ_ONLY baseline и способ возврата зафиксировать. Не снижать tier task_cancel. Никаких новых VM tools в проект не добавлять.
7. Под текущим token выполнить **только запланированный** POST /api2/json/nodes/7500T/qemu/<TEST_VMID>/status/shutdown с form timeout=60, forceStop=0. Не задавать skiplock/keepActive, не использовать reboot/stop вместо shutdown. Это будущий task creation, сейчас не выполнялось.
8. Получить UPID из data ответа. Проверить raw UPID: node=7500T, type=qmshutdown, id=TEST_VMID, owner=ai-agent@pve!openwebui; точное совпадение с GET status. GET должен показать running. Если stopped/unknown/чужой owner/другой node/type — DELETE запрещён, тест неполон. Если задача слишком быстрая, не подключать ОС/рабочие диски ради продления; согласовать дальнейший вариант.
9. Немедленно вызвать MCP task_cancel для этого UPID/node, сначала wait=false. Отдельный direct DELETE не нужен: иначе будет два mutate. Ожидается cancel_requested=true/status=unknown/stopped=null либо честная ошибка/unknown. Независимыми GET status/log и VM status установить наблюдаемое состояние. Timeout/естественное завершение не объявлять успешной причинной отменой.
10. Для wait=true отдельно разрешить второй qmshutdown той же проверенной fixture (если она still running), либо отдельно разрешить её повторный start. Снова новый UPID и те же gates; task_cancel wait=true, timeout=30, poll_interval=1. Не отменять startup/create/cleanup UPID и не переиспользовать первый UPID вместо нового task. При completed race сценарий отмены не засчитывается.
11. Проверить logs: correlation id, pve_delete outcome/HTTP, domain result, raw exitstatus. Не сохранять Authorization/token secret. Проверить отсутствие изменений VM/LXC inventory, networks и volumes вне fixture; не удалять естественную task history. Не создавать искусственный network/ACL failure на кластере.
12. Оператор по отдельно разрешённому cleanup читает fixture config/node, убеждается, что нет volumes/net/new attachments/active workers, затем штатно stop при необходимости и destroy только TEST_VMID на 7500T. Ни purge чужих данных, ни удаление общих backup, ни force/unlock/kill/SSH не разрешаются. При partial cleanup остановиться для ручного решения оператора.
13. Удалить лишь добавленные временные ACL/role assignments (учесть, что destroy может удалить VM-specific ACL), не затронуть существующие Audit grants; при необходимости удалить временную custom-role, если никем не используется. Вернуть READ_ONLY/перезапуск и проверить deny. Cleanup и возврат ACL/режима входят в отдельное будущее разрешение, не в текущую подготовку.
14. Записать фактический Stage B Report: node/VMID/UPID без секретов, версии, разрешения, создание/отмена/cleanup HTTP, время, owner, mode/ACL before-after, наблюдение и ограничения. Acceptance/commit не выполнять автоматически.

## Stop-условия и риски

Немедленно прекратить при неверном endpoint/node/owner/VMID, UPID запрещённой ноды, изменившейся fixture, дисках/сети/HA/hookscript, неожиданной нагрузке, task не running, недостаточных правах, TLS-неопределённости без решения, unknown DELETE или изменении production inventory. Unknown — только READ-диагностика, без retry mutate. Worker завершился сам — не доказательство отмены.

Fixture не пишет guest disks, но её конфигурация и task logs записываются PVE, расходуются CPU/RAM/служебные процессы. Нулевого воздействия на сам host не обещается. Общие сервисы и backup-share неприкосновенны. Возможна мгновенная естественная остановка/ошибка QEMU или более короткий shutdown; длительность пока гипотеза. Если отмена оставит fixture running, очистка выполняется отдельно оператором; SIGKILL/SSH не подставляются автоматически. Поведение установленного qemu-server пакета не доказано одним upstream master.

## Критерии готовности и необходимые согласования

Схема и READ-обстановка подтверждены; сценарий подготовлен. **READY FOR SCENARIO REVIEW, NOT READY TO EXECUTE B**: нет fixture, VMID, временных PowerMgmt grants, согласованного TLS и разрешения mutate. Runtime-длительность и cancellation ещё не проверены.

Отдельно согласовать: diskless fixture create/start/stop/destroy на 7500T; минимальные временные user/token ACL; OPERATOR и возврат; TLS; два shutdown-task и ровно соответствующие task_cancel; cleanup; резервный переход на 5800H только отдельным решением. Ничего из этого сейчас не выполнено. Новый исходный код и MCP mutations вне task_cancel не предлагаются.
