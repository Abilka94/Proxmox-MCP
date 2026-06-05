# ADR-0010: Service Type Taxonomy (без имён продуктов)

**Статус:** accepted  
**Дата:** 2026-06-03  
**Зависит от:** ADR-0006

## Контекст

Service.Type должен классифицировать роль сервиса в инфраструктуре, не конкретный продукт («postgres», «jellyfin»). Иначе архитектура встраивает каталог вендоров.

## Решение

### Service.Type — контролируемый словарь (расширяемый через ADR/CHANGELOG)

| Type | Описание |
|------|----------|
| `container_platform` | Оркестрация/платформа контейнеров внутри гостя |
| `database` | СУБД или хранилище данных |
| `media` | Медиа/стриминг |
| `web_application` | HTTP/API приложение |
| `monitoring` | Метрики, логи, observability stack |
| `ci_cd` | Сборка, registry, deploy |
| `auth` | IAM, SSO, сертификаты |
| `storage_service` | Файловый/объектный сервис уровня приложения |
| `messaging` | Очереди, брокеры |
| `custom` | Прочее; в Metadata — уточнение **без** нормативного перечня продуктов |

### Name vs Type

- **Name** — «Billing API prod» (произвольно, задаёт пользователь/агент).  
- **Type** — только из таблицы или `custom`.

### Metadata

Разрешены ключи вроде `stack`, `environment`, `owner`, `documentation_uri`.  
**Запрещено** в схеме валидации v1: поля `product`, `vendor`, `image_name` как обязательные — допустимы только как необязательные пользовательские keys в Metadata без семантики в коде оператора.

### HealthStatus

| Значение | Смысл |
|----------|-------|
| `unknown` | Не проверялось |
| `healthy` | По последнему probe/наблюдению |
| `degraded` | Работает с ограничениями |
| `unhealthy` | Недоступен |
| `maintenance` | Плановое обслуживание |

Probe metadata — в Metadata (`probe_type`, `last_check`, `last_error`), не hardcoded product checks.

## Последствия

- Примеры в user docs могут называть продукты; код и JSON Schema — нет.

## Связанные документы

- `docs/MEMORY_KNOWLEDGE_MODEL.md` §5
