> **Archived.** Рекомендации применены в [ARCHITECTURE.md](../../ARCHITECTURE.md) v0.2 §16.

# Рекомендации по обновлению ARCHITECTURE.md

**Основание:** архитектурное решение о позиционировании (2026-06-03), принятые пункты Review Report C-05, C-06, C-07, C-08, отклонение provider-agnostic framework и Workload-абстракции.  
**Целевой документ:** `docs/ARCHITECTURE.md` (планируемая версия **0.2**).  
**Связанные документы:** `docs/MEMORY_KNOWLEDGE_MODEL.md`, ADR в `docs/adr/`.

---

## 1. Новое позиционирование (обязательно отразить)

### 1.1 Что изменить в §1

| Текущая формулировка | Рекомендуемая формулировка |
|----------------------|----------------------------|
| «Infrastructure Operator для **домашнего** кластера» | **AI Infrastructure Operator для Proxmox VE** — специализированный оператор, глубоко ориентированный на PVE, а не универсальный framework |
| «MCP-Proxmox» без уточнения роли | Явно: оператор выполняет функции **системного администратора** инфраструктуры на базе Proxmox (наблюдение, диагностика, в v2+ — согласованные действия) |
| Аудитория: «операторы домашнего кластера» | Аудитория: администраторы PVE любого масштаба, разработчики MCP, интеграторы LLM-UI |

### 1.2 Новый подраздел §1.0 или §1.1 — «Что проект является и не является»

**Явно зафиксировать:**

- ✅ Специализированный **AI-оператор для Proxmox VE** (единственная платформа v1).  
- ✅ **Open-source** продукт с глубокой доменной моделью PVE.  
- ✅ Работа на **любой** инсталляции: standalone node, малый/большой кластер.  
- ❌ **Не** Universal Infrastructure Operator Framework.  
- ❌ **Не** provider-agnostic платформа.  
- ❌ **Не** привязка к конкретной инсталляции пользователя (имена VM, число нод, список сервисов).

### 1.3 Двухуровневая модель знаний (новый §1.5)

Ввести раздел **«Модель знаний оператора»** со ссылкой на `MEMORY_KNOWLEDGE_MODEL.md`:

| Уровень | Название | Сущности |
|---------|----------|----------|
| **1** | **Infrastructure Layer** (Proxmox-native) | Cluster, Node, LXC, VM, Storage, Network, Task, Backup, Update |
| **2** | **Service Layer** (пользовательская семантика) | **Service** (Name, Type, RunsOn, Dependencies, HealthStatus, Metadata) |

Цепочка рассуждения агента (пример в ARCHITECTURE, детали в Memory doc):

`Service → LXC|VM → Node → Cluster`

**Запрет в нормативной архитектуре:** встроенные знания о конкретных продуктах (Home Assistant, PostgreSQL как бренд и т.д.). Тип сервиса — **категория**, не SKU.

---

## 2. §1.2 Ограничения v1 — правки по C-05

| Было | Стало |
|------|-------|
| «Кластер: **3 ноды**, единый Proxmox Cluster» | «Подключение: **один logical endpoint** PVE (cluster VIP, любая нода или standalone); топология **N ≥ 1** нод определяется API в runtime» |
| — | Добавить: «Размер кластера, inventory и состав сервисов **не** задаются в конфигурации» |

Остальное §1.2 без изменений по смыслу (READ ONLY, API Token, размещение рядом с UI — см. §2.5 ниже).

---

## 3. §1.3 Подсистемы — синхронизация с Infrastructure Layer

### 3.1 Добавить подсистему Backup

В списке подсистем v1 (read) явно включить:

11. **Backup** — задания/снапшоты vzdump, статус backup jobs, хранилище backup (в пределах API и прав токена).

*(Сейчас backup упоминается только косвенно в OPERATOR tier.)*

### 3.2 Переименовать «Memory» в отсылку к Knowledge

Пункт 10 заменить на:

10. **Knowledge & Memory** — персистентная модель знаний (Infrastructure + Service), см. `MEMORY_KNOWLEDGE_MODEL.md`.

### 3.3 Logs

Оставить как подсистему наблюдаемости или вынести в §2 как cross-cutting; не смешивать с Knowledge.

---

## 4. §2 Архитектура MCP — диаграммы и слои

### 4.1 Диаграмма §2.1

**Добавить блоки:**

- `Knowledge Graph / EntityRef` (рядом с Memory)  
- `Service Layer` (логически над Domain Services, данные из Memory + PVE)  
- В Domains: явно **Backup**; убрать любые подписи «3 нод»

**Обновить External:** «Proxmox VE» без жёсткой «9» в диаграмме; версия — в Compatibility Matrix (§новый).

### 4.2 Таблица §2.2 — Orchestrator (C-05, C-07)

| Было | Стало |
|------|-------|
| «Скрывает топологию **3 нод**» | «Агрегирует ответы по **всем нодам** inventory; fan-out с лимитами (§Scalability)» |
| — | Добавить строку **Knowledge Service** | EntityRef, Service graph, reconciliation |

### 4.3 Новый компонент: Knowledge Service

Описать слой между Memory Store и Orchestrator:

- CRUD памяти (заметки, сервисы, связи)  
- Резолв `EntityRef` → вызов domain tools  
- Traversal Service → Infrastructure для diagnostic playbooks  

### 4.4 §2.4 Rate limiting (C-07)

Заменить «домашний кластер — 3–5 параллельных» на:

- `max_concurrent_per_node` (config, default 5)  
- `max_concurrent_cluster` (config, default 15)  
- ссылка на §Scalability & Limits

---

## 5. Новые нормативные разделы (вставить после §2 или §9)

### 5.1 §Scalability & Limits (C-07) — **новый раздел**

Минимальное содержание:

| Тема | Требование |
|------|------------|
| **Топология** | 1..N нод; standalone = N=1 без отдельного «режима продукта» |
| **List operations** | Обязательные `limit`, `offset` или cursor; default limit (напр. 100) |
| **Aggregate tools** | `pve_cluster_overview` — bounded summary, не полный dump; при превышении порога — partial + `truncated: true` |
| **Fan-out** | Параллельные запросы к нодам с semaphore; timeout per node |
| **RRD / metrics** | Ограничение timeframe и resolution |
| **Logs** | `max_lines` cap (уже в конфиге) |
| **Memory search** | `limit` на результаты; пагинация |
| **Large cluster** | Рекомендация фильтров: `node`, `type`, `tags` в list tools |

### 5.2 §Compatibility Matrix (C-08) — **новый раздел**

| Поле | Описание |
|------|----------|
| Supported PVE | Мажорные версии (напр. 8.x, 9.x) — уточнить в ADR-0008 |
| API path | `/api2/json` version policy |
| Feature flags | SDN, backup API — optional capabilities, graceful degrade |
| MCP server version | Semver, матрица в README |
| Breaking changes | CHANGELOG + migration notes |

### 5.3 §EntityRef (C-06) — краткая отсылка

Короткий подраздел со ссылкой на `MEMORY_KNOWLEDGE_MODEL.md` §3:

- формат ссылки на объект Infrastructure и Service  
- стабильность при переименовании (alias)  
- `stale` при исчезновении объекта из PVE

---

## 6. §3 Структура проекта

### 6.1 Добавить модули

```
src/
├── knowledge/          # EntityRef, Service model, graph traversal
│   ├── entityref/
│   ├── service/
│   └── reconciliation/
├── domains/
│   └── backup/         # новый domain
```

### 6.2 Не делать

- `providers/` / `core/` split (отклонено)  
- переименование `pve_*` в `infra_*` (отклонено C-04 из review)

---

## 7. §4 Tool Tiers — Backup и Knowledge tools

### 7.1 READ tier — добавить

| Подсистема | Примеры |
|------------|---------|
| Backup | `pve_backup_list`, `pve_backup_job_status`, `pve_backup_snapshot_list` (уточнить по API) |
| Knowledge | `pve_service_get`, `pve_service_list`, `pve_service_link`, `pve_memory_*`, `pve_knowledge_traverse` |

### 7.2 Матрица §4.4

Добавить строки **Backup** и **Service (Knowledge)**.

---

## 8. §6 Память оператора — заменить отсылкой

**Заменить §6** на краткий summary + ссылку:

> Полная спецификация: **`docs/MEMORY_KNOWLEDGE_MODEL.md`**.

В summary оставить:

- два уровня знаний  
- EntityRef  
- локальное хранилище vs PVE SoT  
- write в READ_ONLY только для Knowledge (не для PVE)

Удалить/перенести примеры **Home Assistant**, **ZFS на node1** из нормативного ARCHITECTURE → в `docs/examples/` (опционально).

---

## 9. §2.5 и homelab — смягчить привязку

| Было | Стало |
|------|-------|
| «Docker host / **homelab**» | «Deployment host»; homelab — **пример** в `deploy/` |
| Open WebUI как primary | «Рекомендуемая интеграция»; MCP-клиенты любые |
| §9.3 `pve.homelab.local` | `pve.example.local` + комментарий «подставьте FQDN инсталляции» |

---

## 10. §10 Дорожная карта

Добавить milestone:

- **v1.0:** Infrastructure Layer READ + Knowledge (Service layer, EntityRef) + Scalability + Compatibility doc  
- **v1.1:** Diagnostic prompts (Service → VM/LXC → Node)  
- **v2.0:** OPERATOR tier включая backup triggers  

Убрать любые формулировки про «provider SDK».

---

## 11. §11 Открытые вопросы — обновить

**Закрыть / перенести в ADR:**

- ADR-0005: позиционирование AI PVE Operator  
- ADR-0006: двухуровневая модель знаний  
- ADR-0007: EntityRef  
- ADR-0008: Compatibility Matrix  
- ADR-0009: Scalability & Limits  
- ADR-0010: Service Type taxonomy (без имён продуктов)

**Оставить открытым:**

- ADR-0001: язык реализации  
- ADR-0002: stdio vs SSE  
- ADR-0003: memory write в READ_ONLY  

---

## 12. Чеклист правок по разделам

| § | Действие | Приоритет |
|---|----------|-----------|
| 1 | Переписать позиционирование, убрать homelab/3 nodes | P0 |
| 1.5 | Двухуровневая модель знаний | P0 |
| 1.2 | C-05 topology | P0 |
| 1.3 | +Backup, Knowledge | P0 |
| 2.1–2.2 | Диаграмма, Orchestrator, Knowledge Service | P0 |
| NEW | Scalability & Limits | P0 |
| NEW | Compatibility Matrix | P0 |
| NEW | EntityRef (кратко) | P0 |
| 6 | Заменить ссылкой на MEMORY_KNOWLEDGE_MODEL | P0 |
| 4, 8 | Backup + Knowledge tools | P1 |
| 3 | `knowledge/`, `backup/` | P1 |
| 9.3, 2.5 | Нейтральные примеры деплоя | P2 |
| 10, 11, 12 | Roadmap, ADR index | P1 |

---

## 13. Что сознательно не менять (решение архитектора)

- Префикс tools `pve_*` и URI `pve://`  
- Отдельные домены **LXC** и **VM** (не Workload)  
- **PVE Client**, привилегии PVE в §5.4  
- Policy Engine, tiers READ / OPERATOR / ADMIN  
- Структура `src/pve/`, `src/domains/{lxc,vms,...}`  

---

*После утверждения рекомендаций — внести правки в ARCHITECTURE.md v0.2 и синхронизировать CHANGELOG.*
