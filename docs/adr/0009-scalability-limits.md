# ADR-0009: Scalability & Limits

**Статус:** accepted  
**Дата:** 2026-06-03  
**Зависит от:** ADR-0005

## Контекст

Review C-05/C-07: нельзя предполагать 3 ноды и малый inventory. Оператор должен одинаково корректно работать на 1 и на многих нодах, включая большие кластеры.

## Решение

### Топология

- **N ≥ 1** нод; standalone — кластер из одной ноды без отдельного code path «homelab».  
- Число нод **не** в конфиге; discovery через `pve_cluster_status` / `pve_nodes_list`.

### Fan-out (Orchestrator)

| Параметр | Default | Описание |
|----------|---------|----------|
| `max_concurrent_per_node` | 5 | Семафор HTTP к одной ноде |
| `max_concurrent_cluster` | 15 | Глобальный лимит |
| `node_request_timeout_sec` | 30 | Per-node timeout |
| `partial_results` | true | При timeout ноды — ответ с `errors[]` |

### Pagination (обязательно для list tools)

| Параметр | Default | Max |
|----------|---------|-----|
| `limit` | 100 | 1000 |
| `offset` | 0 | — |

Агрегирующие tools (`pve_cluster_overview`, `pve_guests_list_all`):

- возвращают summary + counts;  
- при `total > threshold` (config `aggregate_threshold`, default 500) — **не** встраивают полный список, а ссылку на paginated list tools + `truncated: true`.

### Cache

- TTL из конфига; для кластеров `node_count > 10` рекомендуется увеличить TTL list-операций или сужать запросы фильтрами.

### Memory / Knowledge

- `pve_memory_search`: default `limit=20`, max 100  
- Reconciliation: batch по нодам, не блокировать MCP hot path

### Logs

- `max_lines` default 500, max 5000 (config cap)

## Последствия

- ARCHITECTURE §2.2, §2.4, новый §Scalability обновляются.  
- Tool Catalog документирует лимиты каждого tool.

## Связанные документы

- `docs/MEMORY_KNOWLEDGE_MODEL.md` §8
