# Documentation Audit

**Дата:** 2026-06-03  
**Контекст:** завершение архитектурной фазы; старт Phase 1A  
**Аудитор:** подготовка к реализации (automated inventory)

---

## 1. Инвентаризация всех .md файлов

| # | Путь | Строк (approx) |
|---|------|----------------|
| 1 | `docs/ARCHITECTURE.md` | 640 |
| 2 | `docs/MEMORY_KNOWLEDGE_MODEL.md` | 757 |
| 3 | `docs/IMPLEMENTATION_ROADMAP.md` | 760 |
| 4 | `docs/implementation/IMPLEMENTATION_PACKAGE.md` | new |
| 5 | `docs/implementation/PHASE_1A_TASK_PLAN.md` | new |
| 6 | `docs/audit/DOCUMENTATION_AUDIT.md` | this |
| 7 | `docs/audit/DOCUMENTATION_CLEANUP_PLAN.md` | new |
| 8 | `docs/adr/ADR_INDEX.md` | 78 |
| 9 | `docs/adr/template.md` | 25 |
| 10 | `docs/adr/0001-implementation-language.md` | new |
| 11 | `docs/adr/0002-mcp-transport.md` | new |
| 12 | `docs/adr/0005-ai-proxmox-operator-positioning.md` | 39 |
| 13 | `docs/adr/0006-two-level-knowledge-model.md` | 50 |
| 14 | `docs/adr/0007-entityref.md` | 62 |
| 15 | `docs/adr/0008-pve-compatibility-matrix.md` | 51 |
| 16 | `docs/adr/0009-scalability-limits.md` | 60 |
| 17 | `docs/adr/0010-service-type-taxonomy.md` | 57 |
| 18 | `docs/archive/reviews/ARCHITECTURE_REVIEW_2026-06-03.md` | 413 |
| 19 | `docs/archive/recommendations/ARCHITECTURE_UPDATE_RECOMMENDATIONS.md` | 279 |

**Отсутствуют (запланированы, не созданы):**

| Путь | Статус |
|------|--------|
| `README.md` (root) | planned T-116 |
| `CHANGELOG.md` | planned T-509 / T-004 |
| `LICENSE` | planned T-004 |
| `docs/TOOL_CATALOG.md` | planned T-211 |
| `docs/OPERATIONS.md` | planned Phase 1B |
| `docs/adr/0003-memory-write-in-read-only.md` | proposed, not created |
| `docs/adr/0004-network-scope.md` | proposed, not created |

---

## 2. Статус каждого документа

| Документ | Статус | Комментарий |
|----------|--------|-------------|
| ARCHITECTURE.md v0.2 | **normative** | Верхний уровень runtime/MCP |
| MEMORY_KNOWLEDGE_MODEL.md v1.0 | **normative** | Memory, Service, EntityRef |
| IMPLEMENTATION_ROADMAP.md v1.0 | **active** | Фазы, MVP; не дублирует ARCHITECTURE |
| IMPLEMENTATION_PACKAGE.md | **active** | Старт Phase 1A, toolchain |
| PHASE_1A_TASK_PLAN.md | **active** | Детализация T-000…T-117 |
| ADR_INDEX.md | **active** | Индекс ADR |
| adr/template.md | **active** | Шаблон |
| adr/0001 | **draft** → принять → accepted | Implementation language |
| adr/0002 | **draft** → принять → accepted | MCP transport |
| adr/0005–0010 | **normative** (accepted) | Архитектурные решения |
| ARCHITECTURE_REVIEW_2026-06-03.md | **historical** | Pre-v0.2 review |
| ARCHITECTURE_UPDATE_RECOMMENDATIONS.md | **historical** | Черновик правок; v0.2 применён |
| DOCUMENTATION_AUDIT.md | **active** | Мета-документация |
| DOCUMENTATION_CLEANUP_PLAN.md | **active** | План действий |

**Obsolete:** нет отдельного файла ARCHITECTURE v0.1 в tree (заменён in-place на v0.2).

---

## 3. Источники истины (Sources of Truth)

| Тема | SoT | Вспомогательные |
|------|-----|-----------------|
| Runtime, MCP, Policy, Domains, tiers | **ARCHITECTURE.md** v0.2 | ROADMAP |
| Memory, Service, EntityRef, traverse | **MEMORY_KNOWLEDGE_MODEL.md** v1.0 | ADR 0006, 0007, 0010 |
| Позиционирование, PVE-only | **ADR-0005** | ARCHITECTURE §1 |
| Scalability limits | **ADR-0009** | ARCHITECTURE §9 |
| PVE compatibility | **ADR-0008** | ARCHITECTURE §10 |
| Service.Type | **ADR-0010** | MEMORY §5 |
| Порядок реализации | **IMPLEMENTATION_ROADMAP.md** | PHASE_1A_TASK_PLAN |
| Toolchain Phase 1A | **IMPLEMENTATION_PACKAGE.md** | ADR-0001, 0002 |
| Задачи T-* | **PHASE_1A_TASK_PLAN.md** | ROADMAP §13 |
| Список ADR | **ADR_INDEX.md** | individual ADR files |
| Конкретные tool contracts | **TOOL_CATALOG.md** (future) | Registry code |

---

## 4. Документы, не нужные для ежедневной разработки после архитектурной фазы

| Документ | Нужен? | Рекомендация |
|----------|--------|--------------|
| ARCHITECTURE_REVIEW | Нет (справочно) | archive |
| ARCHITECTURE_UPDATE_RECOMMENDATIONS | Нет (выполнено) | archive |
| ADR draft 0001/0002 до accept | Да до T-000/T-001 | accept → normative |

Разработчик Phase 1A должен читать: **ARCHITECTURE, IMPLEMENTATION_PACKAGE, PHASE_1A_TASK_PLAN, ADR 0005–0010, accepted 0001–0002**.

---

## 5. Согласованность (проверка)

| Проверка | Результат |
|----------|-----------|
| ARCHITECTURE ↔ MEMORY | ✓ ARCHITECTURE §16; нет дублирования Memory |
| ARCHITECTURE ↔ ROADMAP | ✓ Phase 1A/1B согласованы |
| PACKAGE ↔ ADR-0001/0002 | ✓ Python, stdio |
| TASK_PLAN ↔ ROADMAP §13 | ✓ T-000…T-117 покрыты |
| ADR_INDEX ↔ файлы adr/ | ⚠ обновить после accept 0001, 0002 |
| Recommendations ↔ ARCHITECTURE v0.2 | ✓ рекомендации применены; файл historical |

**Противоречий между normative/active документами не выявлено.**

---

## 6. Пробелы (не противоречия)

| Пробел | Закрытие |
|--------|----------|
| ADR-0003, 0004 не созданы | T-002; создать при Phase 1B/2 |
| README, LICENSE, CHANGELOG | T-004, T-116, T-509 |
| TOOL_CATALOG | T-211 |

---

*См. [DOCUMENTATION_CLEANUP_PLAN.md](DOCUMENTATION_CLEANUP_PLAN.md) для действий.*
