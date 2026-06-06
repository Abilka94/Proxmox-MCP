# MCP-Proxmox

AI-оператор инфраструктуры Proxmox VE, реализованный в виде сервера Model Context Protocol (MCP).

---

## Текущее состояние

| Параметр | Значение |
|----------|----------|
| Текущая версия | `v0.3.0-phase1b.2` |
| Последний принятый этап | **Phase 1B.2** — Task Domain Extended |
| Основная цель | PVE 9.x |
| Дополнительная цель | PVE 8.x (best effort, node-level fallback) |
| Статус тестов | **135/135** тестов проходят |
| Живая валидация | Кластер PVE 9.2.3 (3 узла, кворум есть) ✅ |

---

## Возможности

### Кластер
- Статус кластера, кворум, состав узлов

### Узлы
- Список узлов с состоянием online/offline
- Использование ресурсов узла (CPU, memory, disk, uptime)

### Виртуальные машины
- Инвентаризация ВМ с выделенными ресурсами
- Состояние ВМ в рантайме (CPU, memory, disk I/O, balloon)
- Конфигурация ВМ

### Контейнеры (LXC)
- Инвентаризация контейнеров
- Состояние контейнера в рантайме
- Конфигурация контейнера

### Хранилища
- Инвентаризация пулов хранения
- Статус и использование хранилищ
- Содержимое хранилищ

### Сеть
- Список сетевых интерфейсов узла

### Обновления
- Доступные обновления пакетов на узле
- Сводка обновлений по кластеру

### Задачи
- Список задач с фильтрацией (status, type, user, VMID)
- Статус задачи (UPID → status, exit status)
- Журнал задачи (инкрементальный, со смещением start)
- `task_wait` — ожидание завершения задачи с таймаутом и exponential backoff
- `task_follow` — ожидание с инкрементальным накоплением журнала (макс. 5000 строк)

---

## MCP-инструменты

**21 инструмент** в 9 доменах.

### Кластер
- `server_info` — идентификация и конфигурация сервера
- `cluster_info` — статус и кворум кластера

### Узлы
- `list_nodes` — список всех узлов с состоянием
- `node_status` — детальное использование ресурсов узла

### Виртуальные машины
- `vm_list` — инвентаризация ВМ
- `vm_status` — состояние ВМ в рантайме
- `vm_config` — конфигурация ВМ

### Контейнеры
- `container_list` — инвентаризация LXC-контейнеров
- `container_status` — состояние контейнера в рантайме
- `container_config` — конфигурация контейнера

### Хранилища
- `storage_list` — инвентаризация пулов хранения
- `storage_status` — использование и статус хранилища
- `storage_content` — содержимое хранилища

### Сеть
- `network_list` — сетевые интерфейсы узла

### Обновления
- `node_updates` — доступные обновления на узле
- `cluster_updates` — сводка обновлений по кластеру

### Задачи
- `task_list` — история задач с фильтрацией
- `task_status` — статус задачи по UPID
- `task_log` — журнал задачи
- `task_wait` — ожидание завершения задачи (таймаут, backoff)
- `task_follow` — ожидание с накоплением журнала

---

## Дорожная карта

- [x] **Phase 1A** — MCP + PVE Core Read (кластер, узлы, ВМ, контейнеры, хранилища, сеть)
- [x] **Phase 1B.1** — Task Domain Core (task_list, task_status, task_log, обновления узлов)
- [x] **Phase 1B.2** — Task Domain Extended (task_wait, task_follow, опрос, накопление журнала)
- [ ] **Phase 1C** — Task Mutate (task_cancel, task_stop, POST-операции)
- [ ] **Phase 2** — Knowledge Foundation (Memory, EntityRef, аннотации)
- [ ] **Phase 3** — Service Layer (привязка сервисов к ресурсам)
- [ ] **Phase 4** — Diagnostic Operator (проверки работоспособности сервисов)
- [ ] **Phase 5** — Controlled Actions (операции изменения под управлением политик)

---

## Документация

### Указатель
- [docs/README.md](docs/README.md) — полный индекс документации проекта

### Архитектура и проектирование
- [Архитектура](docs/architecture/ARCHITECTURE.md) — runtime, MCP, Policy, Domains, tiers
- [Индекс ADR](docs/adr/ADR_INDEX.md) — архитектурные решения (ADR-0001–ADR-0010)
- [Политика использования reference](docs/architecture/REFERENCE_USAGE_POLICY.md) — порядок использования reference-репозиториев
- [Дорожная карта реализации](docs/releases/IMPLEMENTATION_ROADMAP.md) — фазы 1A–6, MVP (v1.0)

### Принятые этапы

**Phase 1A** — Infrastructure Read Layer (v0.1.0)
- [Проектирование и отчёты](docs/phase-1a/) — 9 документов
- [Валидация](docs/phase-1a/validation/) — 4 документа
- [Приёмка](docs/phase-1a/acceptance/) — 1 документ

**Phase 1B.1** — Task Domain Core (v0.2.0)
- [Проектирование](docs/phase-1b/phase-1b.1/design/) — документ проектирования
- [Реализация](docs/phase-1b/phase-1b.1/implementation/) — отчёт о реализации
- [Валидация](docs/phase-1b/phase-1b.1/validation/) — 4 документа
- [Приёмка](docs/phase-1b/phase-1b.1/acceptance/) — 1 документ

**Phase 1B.2** — Task Domain Extended (v0.3.0)
- [Проектирование](docs/phase-1b/phase-1b.2/design/) — документ проектирования
- [Реализация](docs/phase-1b/phase-1b.2/implementation/) — отчёт о реализации + план валидации
- [Валидация](docs/phase-1b/phase-1b.2/validation/) — проверка подключения + отчёт о валидации
- [Приёмка](docs/phase-1b/phase-1b.2/acceptance/) — 1 документ

### Исторические документы
- [Архив](docs/archive/) — аудит кодовой базы, конкурентный анализ, аудит документации, аудит использования reference, обновление README

---

## Разработка

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/unit
python -m ruff check src/ tests/
python -m mypy src/
```

---

## Статус проекта

**Стабильная разработка.** Активная разработка с регулярными релизами. Все возможности этапов проходят валидацию на живых кластерах PVE перед приёмкой.
