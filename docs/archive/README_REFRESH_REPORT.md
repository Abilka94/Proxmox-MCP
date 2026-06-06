# README Refresh Report

**Дата:** 2026-06-06
**Цель:** Приведение README.md в соответствие с состоянием проекта на теге v0.3.0-phase1b.2

---

## 1. Удалённые разделы

| Раздел | Причина |
|--------|---------|
| `Status: local Phase 1A bootstrap` | Проект на Phase 1B.2 ACCEPTED |
| `The first runnable MCP stdio server lands in T-104` | T-104 реализован, MCP-сервер работает с Phase 1A |

## 2. Добавленные разделы

| Раздел | Содержание |
|--------|------------|
| Current Status | Версия, фаза, target PVE, тесты (135/135), live validation |
| Features | 8 доменов: Cluster, Nodes, VMs, Containers, Storage, Network, Updates, Tasks |
| MCP Tools | 21 инструмент, сгруппированный по 9 доменам |
| Roadmap | 8 milestones с GitHub Markdown checkboxes (Phase 1A ✅ → Phase 5) |
| Project Status | `Stable Development` |

## 3. Обновлённые ссылки

| Ссылка | Изменение |
|--------|-----------|
| `docs/phase-1a/reports/` | Расширена на `docs/phase-1a/` и `docs/phase-1b/` |
| `docs/architecture/` | Добавлена `REFERENCE_USAGE_POLICY.md` |
| `docs/adr/ADR_INDEX.md` | Добавлена (была опущена) |
| `docs/releases/IMPLEMENTATION_ROADMAP.md` | Добавлена (была опущена) |

## 4. Roadmap milestones

| Milestone | Статус |
|-----------|--------|
| Phase 1A — MCP + PVE Core Read | ✅ Accepted (tag v0.1.0-phase1a) |
| Phase 1B.1 — Task Domain Core | ✅ Accepted (tag v0.2.0-phase1b.1) |
| Phase 1B.2 — Task Domain Extended | ✅ Accepted (tag v0.3.0-phase1b.2) |
| Phase 1C — Task Mutate | ⬜ Запланировано (POST operations) |
| Phase 2 — Knowledge Foundation | ⬜ Запланировано |
| Phase 3 — Service Layer | ⬜ Запланировано |
| Phase 4 — Diagnostic Operator | ⬜ Запланировано |
| Phase 5 — Controlled Actions | ⬜ Запланировано |

## 5. Оставшиеся пробелы

- **docs/README.md** по-прежнему указывает Phase 1B.2 как *(future)*. Требует отдельного обновления.
- **docs/releases/RELEASE_NOTES_v0.1.0-phase1a.md** — нет release notes для v0.2.0-phase1b.1 и v0.3.0-phase1b.2. Формально не входит в scope данного refresh.

## 6. Итог

| Параметр | Значение |
|----------|----------|
| Файлы изменены | `README.md` (переписан полностью) |
| Файлы созданы | `docs/archive/README_REFRESH_PLAN.md` |
| Файлы созданы | `docs/archive/README_REFRESH_REPORT.md` |
| Разделы удалено | 2 |
| Разделы добавлено | 5 |
| Ссылки обновлено | 4 |
| Roadmap milestones внесено | 8 |
| Требуется дополнительное обновление | `docs/README.md` (Phase 1B.2 из *(future)* в актуальный статус) |
