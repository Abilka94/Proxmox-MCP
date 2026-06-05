# ADR-0008: Compatibility Matrix для Proxmox VE

**Статус:** accepted  
**Дата:** 2026-06-03  
**Зависит от:** ADR-0005

## Контекст

Оператор должен работать на разных версиях и топологиях PVE без привязки к «VE 9 only» в нормативном тексте. Нужна явная политика поддержки для OSS.

## Решение

### Поддерживаемые версии Proxmox VE (целевые)

| Ветка | Статус v1.0 | Примечание |
|-------|-------------|------------|
| **9.x** | Tier 1 (primary) | Полное покрытие READ подсистем |
| **8.x** | Tier 2 (best effort) | Тесты CI; отдельные поля API могут отсутствовать |
| **7.x** | Не поддерживается | — |

### API

- Base path: `/api2/json`  
- Версия MCP-сервера (Semver) не привязана 1:1 к версии PVE; матрица в README.

### Capability flags (runtime discovery)

При старте или первом запросе фиксировать доступность:

| Capability | Влияние |
|------------|---------|
| `cluster_mode` | multi-node vs standalone |
| `sdn` | Network SDN tools |
| `backup_api` | Backup subsystem |
| `ceph` | Storage subtype hints |

Недоступная capability → tool возвращает `CapabilityUnavailable`, не crash.

### Документация

- Таблица в `docs/ARCHITECTURE.md` §Compatibility Matrix  
- Изменения API — CHANGELOG + issue label `pve-9` / `pve-8`

## Последствия

- Заголовки документов: «Proxmox VE» с матрицей, не только «VE 9».

## Связанные документы

- ADR-0004 (network scope) уточняет SDN внутри 0008
