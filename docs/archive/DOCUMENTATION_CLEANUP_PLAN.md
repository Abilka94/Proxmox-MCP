# Documentation Cleanup Plan

**Дата:** 2026-06-03  
**Статус:** План (автоматическое удаление **не** выполняется)  
**Основание:** [DOCUMENTATION_AUDIT.md](DOCUMENTATION_AUDIT.md)

---

## 1. Принципы

1. **Normative** документы остаются на верхнем уровне `docs/`.  
2. **Historical** — в `docs/archive/` с README-указателем.  
3. **Не удалять** без явного review; удаление — только если дубликат без ценности.  
4. После cleanup — обновить `ADR_INDEX`, root `README` (T-116).

---

## 2. Действия по документам

| Документ | Действие | Обоснование |
|----------|----------|-------------|
| `docs/ARCHITECTURE.md` | **Оставить без изменений** | SoT v0.2, normative |
| `docs/MEMORY_KNOWLEDGE_MODEL.md` | **Оставить без изменений** | SoT v1.0, normative |
| `docs/IMPLEMENTATION_ROADMAP.md` | **Оставить без изменений** | Active plan до v3.0 |
| `docs/implementation/IMPLEMENTATION_PACKAGE.md` | **Оставить** (новый) | Active, Phase 1A |
| `docs/implementation/PHASE_1A_TASK_PLAN.md` | **Оставить** (новый) | Active, tasks |
| `docs/audit/DOCUMENTATION_AUDIT.md` | **Оставить** | Meta, точка аудита |
| `docs/audit/DOCUMENTATION_CLEANUP_PLAN.md` | **Оставить** | Этот план |
| `docs/adr/ADR_INDEX.md` | **Оставить**; обновить при accept 0001/0002 | Active index |
| `docs/adr/template.md` | **Оставить** | Шаблон |
| `docs/adr/0001-implementation-language.md` | **Оставить** → accept T-000 | Draft → accepted |
| `docs/adr/0002-mcp-transport.md` | **Оставить** → accept T-001 | Draft → accepted |
| `docs/adr/0005…0010` | **Оставить без изменений** | Accepted normative |
| `docs/reviews/ARCHITECTURE_REVIEW_2026-06-03.md` | **Перенести в** `docs/archive/reviews/` | Historical; решения в ADR 0005+ и ARCHITECTURE v0.2 |
| `docs/recommendations/ARCHITECTURE_UPDATE_RECOMMENDATIONS.md` | **Перенести в** `docs/archive/recommendations/` | Historical; полностью отражено в ARCHITECTURE v0.2 §16 |
| `docs/TOOL_CATALOG.md` | **Создать позже** (T-211) | Placeholder не нужен |
| `docs/OPERATIONS.md` | **Создать позже** (Phase 1B) | — |
| Root `README.md` | **Создать** (T-116) | Entry point |

---

## 3. Не выполнять

| Действие | Почему |
|----------|--------|
| Удалять ARCHITECTURE_REVIEW | История решений полезна в archive |
| Удалять recommendations | Audit trail перехода v0.1→v0.2 |
| Объединять ARCHITECTURE + MEMORY | Разные SoT, разная аудитория |
| Объединять ROADMAP + TASK_PLAN | ROADMAP — стратегия; TASK_PLAN — исполнение |
| Переименовывать `pve_*` / менять scope | Вне cleanup |

---

## 4. Шаги выполнения cleanup (чеклист)

- [x] Создать `docs/archive/README.md` (индекс archive)  
- [x] Перенести reviews → `docs/archive/reviews/`  
- [x] Перенести recommendations → `docs/archive/recommendations/`  
- [x] Banner в archived файлах  
- [ ] Accept ADR-0001, ADR-0002 (T-000, T-001)  
- [ ] Обновить `ADR_INDEX.md` статусы 0001, 0002  
- [ ] В `ARCHITECTURE.md` §16 добавить ссылку на archive (опционально, одна строка)  
- [ ] Root README ссылка на docs/ (T-116)

---

## 5. Superseded-версии

| Версия | Статус | Где зафиксировано |
|--------|--------|------------------|
| ARCHITECTURE v0.1 | superseded | git history; не восстанавливать файл |
| MEMORY v0.1 | superseded | заменён v1.0 in-place |
| Recommendations doc | superseded | archive после cleanup |

Отдельный файл `ARCHITECTURE_v0.1.md` **не создавать** — достаточно git history.

---

## 6. После cleanup — актуальный набор для разработчика

```
docs/
├── ARCHITECTURE.md                 # normative
├── MEMORY_KNOWLEDGE_MODEL.md       # normative
├── IMPLEMENTATION_ROADMAP.md       # active
├── implementation/
│   ├── IMPLEMENTATION_PACKAGE.md
│   └── PHASE_1A_TASK_PLAN.md
├── audit/
│   ├── DOCUMENTATION_AUDIT.md
│   └── DOCUMENTATION_CLEANUP_PLAN.md
├── adr/
│   ├── ADR_INDEX.md
│   ├── template.md
│   └── 0001…0010
└── archive/
    ├── README.md
    ├── reviews/
    └── recommendations/
```

---

## 7. Риски cleanup

| Риск | Митигация |
|------|-----------|
| Сломанные ссылки на reviews/ | Grep repo; обновить ссылки в archive README |
| Потеря контекста Review | Archive, не delete |

---

*Выполнение cleanup — отдельный commit «docs: archive historical architecture drafts».*
