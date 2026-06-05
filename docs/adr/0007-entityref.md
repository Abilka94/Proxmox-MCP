# ADR-0007: EntityRef — идентификация объектов в памяти и API

**Статус:** accepted  
**Дата:** 2026-06-03  
**Зависит от:** ADR-0006

## Контекст

Память оператора не должна зависеть от нестабильных строк («vmid 104» без типа и кластера). При исчезновении объекта из PVE ссылки должны деградировать предсказуемо.

## Решение

Ввести **EntityRef** — стабильный идентификатор ссылки на объект Knowledge или Infrastructure.

### Структура (логическая)

| Поле | Описание |
|------|----------|
| `layer` | `infrastructure` \| `service` |
| `kind` | См. таблицу kinds |
| `id` | Стабильный id в пределах kind |
| `cluster_id` | Идентификатор подключённого PVE endpoint (config), опционально для standalone |
| `aliases` | Опциональные прошлые имена / vmid при миграции |

### Kinds — Infrastructure

`cluster`, `node`, `lxc`, `vm`, `storage`, `network`, `task`, `backup`, `update` (последний — scope/version snapshot, не пакет).

### Kinds — Service

`service`

### Сериализация URI (MCP resources)

`pve://ref/{layer}/{kind}/{id}?cluster={cluster_id}`

### Правила

1. **SoT для Infrastructure** — PVE API; Memory хранит только ссылки и обогащение.  
2. При reconcile: если объект отсутствует в PVE → `stale=true` на EntityRef и связанных записях.  
3. **RunsOn** Service — только `lxc` или `vm`.  
4. Не предполагать глобально уникальный vmid без `node` при неоднозначности — id включает `node` + `vmid` для LXC/VM.

### Формат id для LXC/VM

`{node}:{vmid}` — канонический ключ в пределах подключения.

## Последствия

### Положительные

- C-06 из Review Report закрыт без provider-agnostic framework.  
- Единый механизм для Dependencies и Traversal.

### Отрицательные

- Миграция между кластерами = новые EntityRef (ожидаемо).

## Связанные документы

- `docs/MEMORY_KNOWLEDGE_MODEL.md` §3
