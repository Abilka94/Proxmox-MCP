# Phase 1C — Task Mutation: Design v0.3

> Дата: 2026-11-02
> Статус: предложено для review; implementation не разрешена
> Primary: PVE 9.x; secondary: PVE 8.x best effort

## Основание и история

Основание: [аудит Codex](../validation/PHASE_1C_CODEX_AUDIT_REPORT.md). Источники, решения, проблемы, изменения по файлам и тесты: [отчёт revision](PHASE_1C_DESIGN_REVISION_REPORT_v0.3.md).

[Полный снимок v0.2](PHASE_1C_DESIGN_v0.2.md) сохранён без изменения содержимого. По контексту пользователя v0.2 ранее согласован, хотя внутри стоит «На ревью»; это расхождение метаданных не отменяет согласование пользователя. v0.3 требует отдельного review. Старые comparative/gap/implementation/pre-validation документы — исторические свидетельства, а не нормативный источник endpoint.

Scope: task_cancel, DELETE и минимальный PolicyMode.OPERATOR. Нет JobStore, retry mutate, статуса cancelled, новых mutate-tools, SSH, управления процессами. _post_json сохраняется.

## API и транспорт

```http
DELETE /api2/json/nodes/{node}/tasks/{encoded_upid}
Authorization: PVEAPIToken=USER@REALM!TOKENID=SECRET
```

Тело и дополнительные query-параметры не нужны. Схема возвращает null; ожидается HTTP 200 с {"data":null}. Для чужой задачи требуется Sys.Modify на /nodes/{node}, для GET чужого статуса — Sys.Audit там же. Своя задача проверяется по владельцу, включая полный token id. DELETE имеется также в stable-8. Источники: [Tasks master](https://github.com/proxmox/pve-manager/blob/master/PVE/API2/Tasks.pm), [stable-8](https://github.com/proxmox/pve-manager/blob/stable-8/PVE/API2/Tasks.pm). Live-успех на установленном PVE не подтверждён.

Проектируемые методы, не реализация:

```python
async def _delete_json(self, path: str) -> Any: ...
async def stop_task(self, node: str, upid: str) -> None: ...
```

_delete_json универсален по payload: возвращает body['data'], включая null/объект/массив, проверяет HTTP и JSON envelope. Публичный stop_task строит путь и требует data=null. Дополнительные поля envelope разрешены. Отсутствие data, не-JSON, null верхнего уровня, неожиданный payload и пустой 204 — invalid_response, не подтверждение принятия.

Коды: 400 — invalid_request (в том числе no such task), 401 — authentication_failed, 403 — permission_denied, 404 — resource_not_found, 501 — endpoint_unsupported, остальные — http_error. 404/501 не доказывают отсутствие UPID. Нет fallback POST, retry или redirect DELETE.

PveApiError проектно получает необязательные kind и request_outcome (not_sent/rejected/unknown), совместимые с прежними конструкторами. HTTP 4xx/501 — rejected. ConnectError/ConnectTimeout/PoolTimeout до отправки в стандартном транспорте — not_sent. Write/ReadTimeout, Write/ReadError, protocol error, 5xx, невалидный или потерянный ответ — unknown. Общий RequestError консервативно unknown: одного класса недостаточно для доказательства отсутствия отправки.

TimeoutException ловится раньше RequestError; JSON errors оборачиваются в PveApiError. Внедрённый AsyncClient закрывает его владелец, созданный внутри запроса закрывается async context manager. Публичная диагностика не содержит credentials, headers или сырого ответа. _post_json сохраняется; применим для будущих отдельно согласованных операций. Исправление тех же дефектов таймаута/JSON/ресурсов в нём предусмотрено, универсальный framework не нужен.

## Входной контракт

| Поле | Ограничение |
|---|---|
| upid | обязательная непустая строка исходного UPID, не URL |
| node | обязательная нода, равная node в UPID; localhost-алиас не допускается |
| wait | строго boolean, default false |
| timeout | integer, не bool, 1–3600 секунд, default 120 |
| poll_interval | конечное число, не bool, 0.1–30 секунд, default 1.0 |

Неизвестные поля запрещены. Нет приведения числовых строк. Все ограничения проверяются сервером до HTTP; JSON Schema их отражает. Пределы интервалов — предлагаемое решение v0.3.

Структура UPID сверяется с [UPID.pm](https://github.com/proxmox/pve-common/blob/master/src/PVE/UPID.pm): node, pid (8 hex), pstart (8–9 hex), starttime (8 hex), type, id (может быть пустым), user/token, завершающее двоеточие. Не ограничивать pstart восемью символами. Node: `[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?`. Запрещены whitespace, '/', неверное число сегментов. Поддерживается user@realm!token. Вход не декодируется как URL; percent-encoded UPID не принимается вместо исходного. Допустимые символы %, ?, #, !, @ в сегментах кодируются один раз через quote(..., safe=''). Node кодируется отдельным сегментом после проверки; httpx.URL(node).path не используется. Валидация не доказывает существование задачи.

## Строгий результат v0.3

Все структурированные результаты содержат все ключи; nullable поля присутствуют как null. MCP-ошибка до выполнения не содержит этот envelope.

| Поле | Тип и семантика |
|---|---|
| upid, node | проверенные исходные строки |
| cancel_requested | boolean/null: true — валидный ответ DELETE; false — не отправлен или явно отклонён; null — применение неизвестно |
| status | running/stopped/unknown; состояние после DELETE из наблюдения либо unknown |
| stopped | boolean/null: true при stopped, false при running, null при unknown; не доказательство отмены |
| exitstatus | строка PVE из stopped либо null |
| timed_out | boolean: исчерпан бюджет наблюдения, не HTTP timeout |
| error | null либо объект {code, phase, http_status, detail}; phase=preflight/delete/observe; http_status integer/null; detail безопасный текст |
| message | русский текст, не источник машинных решений |
| wait_seconds | фактическая длительность наблюдения >=0; 0 без polling |

Инварианты: stopped=true тогда и только тогда, когда status=stopped; status=unknown означает stopped=null. Принятие DELETE и терминальное состояние не доказывают отмену. Ни OK, ни другой exitstatus не дают достоверной причинности. Ошибка наблюдения не стирает cancel_requested=true.

Пример wait=false:

```json
{"upid":"UPID:pve1:00000001:00000001:00000001:test::user@pve!token:","node":"pve1","cancel_requested":true,"status":"unknown","stopped":null,"exitstatus":null,"timed_out":false,"error":null,"message":"API подтвердил запрос остановки; состояние после запроса не проверялось","wait_seconds":0.0}
```

### Матрица response shapes

U = unknown/null (status/stopped), T = stopped/true, R = running/false. По умолчанию timed_out=false, exitstatus=null, error=null, wait_seconds=0 без ожидания; при polling — фактическое время.

| № | Сценарий | cancel_requested | status/stopped | Отличия |
|---|---|---|---|---|
| 1 | preflight stopped | false | T | exitstatus из GET; «Задача уже завершена; DELETE не отправлен» |
| 2 | DELETE принят, wait=false | true | U | без дополнительного GET |
| 3 | DELETE принят, wait=true, GET stopped | true | T | exitstatus; «Наблюдается завершение задачи; причина не установлена» |
| 4 | timeout наблюдения | true | последнее наблюдение либо U | timed_out=true; сообщение о пределе наблюдения, не утверждение «задача не остановилась» |
| 5 | ошибка preflight GET | false | U | error.phase=preflight; DELETE запрещён |
| 6 | DELETE 401/403 | false | U | authentication_failed/permission_denied, phase=delete |
| 7 | DELETE 404/501 | false | U | resource_not_found/endpoint_unsupported |
| 8 | доказанный сбой до отправки | false | U | transport_not_sent |
| 9 | исход DELETE неизвестен | null | U | request_outcome_unknown; нет retry |
| 10 | ошибка GET после принятия | true | U | observation_failed, phase=observe; исходный HTTP-код сохранён |
| 11a | повторный вызов, preflight stopped | false | T | как №1; история предыдущего вызова неизвестна |
| 11b | повторный вызов, preflight running | по новому DELETE | по №2–10 | второй DELETE допустим; дедупликации нет |
| 12 | гонка GET/DELETE | по ответу DELETE | U без ожидания или T из GET | ошибка DELETE не превращается в успех |
| 13 | естественное завершение после DELETE | true | T из GET | exitstatus без изменения; отмена не заявляется |

При unknown DELETE даже wait=true не запускает polling: неизвестный исход возвращается сразу; дальнейшая диагностика — отдельным READ. Так наблюдение не маскирует неизвестность запроса.

## Алгоритм и READ-совместимость

1. Policy authorization, затем полная валидация.
2. Нодальный GET по node/UPID, без спекулятивного cluster endpoint/fallback. Ошибка — №5, DELETE отсутствует. Неожиданный статус (не running/stopped) — invalid_response preflight.
3. stopped — №1; running — ровно один DELETE.
4. Классифицировать rejected/not_sent/unknown; вернуть соответствующий результат.
5. Валидный DELETE и wait=false — №2. При wait=true начать monotonic deadline наблюдения.
6. Последовательный нодальный GET: stopped — №3, любая ошибка — №10, deadline — №4. Sleep <= остаток; GET ограничен min(HTTP timeout, остаток). Просроченный результат не принимается как наблюдение до deadline. CancelledError не подавлять.

timeout ограничивает только наблюдение после DELETE, preflight/DELETE имеют свои HTTP timeout. Полное время может быть больше timeout. wait=false не означает мгновенный ответ.

Контракты task_wait/task_follow сохраняются. completed=true у них означает terminal, не отмену. Прямое делегирование текущему task_wait отклонено: он смешивает 501/not_found, повторяет transient GET и не ограничивает запрос остатком deadline. Для cancel предусмотрен небольшой собственный цикл с остановкой на первой ошибке; общего рефакторинга READ нет. Поле completed в cancel не дублирует stopped. На timeout status — последнее наблюдение, явно описанное как последнее; при ошибке наблюдения — unknown.

## MCP и PolicyEngine

Ошибки JSON-RPC, неизвестный tool и неверные аргументы используют существующий McpProtocolError; аргументы — -32602 до HTTP, неизвестный tool — -32601. PolicyDenied сохраняет текущий -32603 с безопасным текстом и без HTTP. Неожиданный программный сбой — граница -32603 с безопасным сообщением.

Ожидаемые PVE/transport ошибки возвращаются как envelope выше в content/text JSON. Это намеренное отличие от текущего проброса PveApiError: принятие DELETE нельзя терять из-за ошибки наблюдения. error — машинный сигнал доменной ошибки; MCP isError в этой фазе не вводится.

| PolicyMode | READ | OPERATOR | ADMIN |
|---|---|---|---|
| READ_ONLY (default) | да | нет | нет |
| OPERATOR (явный opt-in) | да | да | нет |
| неизвестный mode/tier | нет | нет | нет |

Добавляется только PolicyMode.OPERATOR. Модель и JSON Schema допускают ровно два режима; default READ_ONLY. Tier задаётся доверенным реестром, не параметром/конфигурационным override. task_cancel остаётся OPERATOR; регрессионный тест фиксирует это. Произвольная правка исходного tier вне доверенной модели. Переключение — явное изменение конфигурации администратором и перезапуск; MCP-инструмент переключения не создаётся. Сейчас конфиги не меняются.

Минимальный аудит — существующие структурированные логи: correlation id, tool, node/UPID, phase, request_outcome, HTTP-код, результат наблюдения, timed_out; без секретов. Нельзя логировать доменную ошибку как успешную отмену. Полный append-only audit store остаётся ограничением архитектуры, не добавляется в Phase 1C.

## Review и дальнейшие разрешения

[Матрица тестов и план по файлам](PHASE_1C_DESIGN_REVISION_REPORT_v0.3.md), [Live Validation v0.3](../validation/PHASE_1C_LIVE_VALIDATION_PLAN.md). Ни один live-сценарий v0.3 не выполнен.

Для implementation отдельно согласовать v0.3: nullable boolean, timeout, отдельное наблюдение и OPERATOR. Создание тестовой задачи, DELETE, конфигурация и ACL требуют отдельного разрешения. Acceptance/commit/tag не разрешены этим документом.

