# Phase 1C — Final Remediation FR-01–FR-03

> Дата: 2026-11-02; автор: Codex
> Статус: FR-01, FR-02, FR-03 закрыты локальными доказательствами
> Live Validation и Acceptance не выполнялись

## Основание и границы

Выполнен единый разрешённый пакет из [Final Implementation Review](../review/PHASE_1C_FINAL_IMPLEMENTATION_REVIEW.md), без нового общего аудита. Прочитаны README, docs/README, workflow/reference policy, Design v0.3, Implementation Report, Final Review и Live Plan. История и незакоммиченная работа сохранены; reset/restore/очистка/commit не применялись. HEAD остаётся 4561204, принятый тег v0.3.0-phase1b.2.

Изменены только src/mcp_proxmox/pve/client/core.py, tests/unit/test_task_cancel_v03.py, tests/integration/test_task_cancel.py, Implementation Report, этот отчёт и навигация двух README. Конфликта с READ-контрактом не потребовалось: FR-02 реализован изолированно в новом cancel-пути. Конфигурация, PolicyEngine, JSON Schema, task_wait/task_follow и рабочий config/local.yaml не изменялись на этом этапе.

## FR-01 — закрыто

tests/unit/test_task_cancel_v03.py:217–246: проверяется полный URL независимо от production helper, отдельно scheme/host/raw_path/query, method DELETE, пустое тело и один запрос. Ожидаемые encoded UPID заданы литералами для обычного и специального UPID с %, ?, #; проверяется token owner и pstart 9 hex. Проверка не получает expected path из кода клиента.

tests/integration/test_task_cancel.py:60–100: строгий MockTransport допускает только точные нодальные status/DELETE URLs и предусмотренную последовательность GET → DELETE → optional GET. Неизвестный method/path, query/body, лишний запрос или повторный DELETE вызывают AssertionError. После вызова сверяется вся последовательность. Нет POST/fallback. Расширены rejected (401), not_sent (ConnectError), unknown с wait=true, preflight transport и malformed scenarios. При rejected/not_sent/unknown wait=true наблюдение не начинается.

Отрицательная проверка: в отдельном процессе временно обёрнут PveClient._delete_json; `/nodes/pve1/tasks/` заменён на `/wrong/nodes/other/tasks/`. Файлы production не менялись. Запущены два параметра exact URL unit и все 19 integration сценариев. Результат: **10 failed, 11 passed, 190 warnings in 0.57s**, pytest exit 1. Это ожидаемое обнаружение дефекта. Сценарии, не доходящие до DELETE, закономерно не падают. Контролирующий процесс завершился 0 только после проверки ожидаемого pytest exit 1. После завершения процесса подмена исчезла; обычный полный suite прошёл.

В предыдущем review неверный URL давал 10 passed; теперь чувствительность подтверждена падениями. FR-01 закрыт.

## FR-02 — закрыто

core.py:259–307: get_task_status_on_node использует собственную ограниченную нодальную GET/parser ветку. Existing _get_json, _get_task_status_node, task_wait/task_follow не изменены. Собственный клиент закрывается, injected остаётся у владельца, авторизация прежняя, redirect отключён.

HTTP 200 с missing data, data=null/list, missing/invalid status и broken JSON преобразуется в PveApiError(kind=invalid_response), далее в preflight envelope без DELETE. Фактический HTTP status сохраняется. HTTP 401/403/404/501 имеют отдельные категории, RequestError — transport_error. Исключения без HTTP status не объявляются автоматически malformed. Сравнения текстов exception не используются.

Unit: test_malformed_preflight_normalized, шесть payload, проверка code=invalid_response/phase=preflight/http_status=200 и ровно одного GET. Integration: те же шесть malformed вариантов, preflight HTTP403 и отдельный ConnectError с transport_error. Прежние READ и cancel negative tests прошли полным набором. FR-02 закрыт.

## FR-03 — закрыто

core.py:329–393: транспортное событие pve_delete фиксируется при выходе из DELETE-ветки, включая ошибки. Поля: phase=delete, request_outcome=accepted/rejected/not_sent/unknown, фактический http_status или null, kind. Correlation context добавляется существующим JSON formatter. Событие не содержит token secret, Authorization, headers, сырого exception или response body.

Транспортная accepted относится к валидному HTTP/JSON envelope универсального _delete_json; endpoint-specific подтверждение data:null по-прежнему проверяет stop_task. Публичный task_cancel envelope и различие между принятием запроса/terminal/причинностью не изменены. Никакого Audit Store не добавлено.

Unit test_delete_json_log сериализует реальный JsonFormatter в StringIO и проверяет четыре исхода: success 200, HTTP401, ConnectError и ReadTimeout. Проверены категория, HTTP status, kind, phase, correlation_id и отсутствие raw-secret/Authorization в строке JSON. Состояние logger восстанавливается после теста. FR-03 закрыт.

## Результаты проверок

| Проверка | Фактический результат |
|---|---|
| Целевые pytest unit v0.3 + integration | 113 passed, 946 warnings in 2.53s |
| Неверный DELETE endpoint в памяти | pytest exit 1: 10 failed, 11 passed in 0.57s; ожидаемые падения |
| Полный pytest | 256 passed, 946 warnings in 7.03s |
| Полный Ruff после исправления нового import-order | 9 прежних E501; новых диагностик нет |
| mypy src/ | 6 прежних ошибок; новых диагностик нет |
| git diff --check | без whitespace ошибок |

Команды pytest: python -B -m pytest -p no:cacheprovider -q --disable-warnings; targeted с tests/unit/test_task_cancel_v03.py tests/integration/test_task_cancel.py. Выполнены локально вне sandbox, HTTP только MockTransport; live-скрипты не запускались. После полного прогона выполнена только перестановка локальных импортов Ruff, затем проверен Ruff; поведение тестов не менялось.

Сравнение с baseline: было 235 passed; стало 256 (+21: +11 unit и +10 integration с учётом параметризации). Целевой набор теперь 94 unit +19 integration. Warnings 946 вместо 757 связаны с дополнительными async pytest-сценариями и прежними deprecated asyncio policy API pytest_asyncio на Python 3.14.2, а не новыми предупреждениями приложения.

Ruff baseline сохранён: registry/tools.py:514; test_domain_tasks.py:35,41,150; test_domain_updates.py:64; test_mcp_server.py:345,413,447,532. mypy baseline: responses.py:204 duplicate numa; loader.py:68 yaml stubs; core.py:216 TaskListEntry.vmid; service.py:134,205,224 старые READ-типы. Они не исправлялись вне scope. Новый I001 в добавленном logging-тесте исправлен сортировкой импортов; итоговых новых диагностик нет.

## Ограничения и следующий этап

Сохранены Design v0.3, nullable cancel_requested/stopped, semantics unknown/terminal, матрица READ_ONLY/OPERATOR/ADMIN, отсутствие retry и неизвестность причинности отмены. Изменения HTTP status в диагностике malformed ответов сохраняют фактическое значение, не меняя структуру публичного envelope.

Нет live-подтверждения DELETE на PVE 9.x; PVE 8.x best effort. Тип безопасной тестовой задачи и минимальные реальные ACL должны быть отдельно определены оператором. Дополнительные права не назначались, privsep и рабочий PolicyMode не менялись. Не создавались/не останавливались задачи, не выполнялись реальные mutate, Live Validation, Acceptance, commit/push/tag.

**Локальный gate remediation пройден.** Следующий этап — отдельно согласованная [Live Validation](../validation/PHASE_1C_LIVE_VALIDATION_PLAN.md). Этот отчёт не является разрешением на неё. Новый общий Implementation Review не проводился и не предлагается.
