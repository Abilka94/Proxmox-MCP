# README Refresh Plan

**Дата:** 2026-06-06
**Цель:** Привести README.md в соответствие с состоянием проекта на теге v0.3.0-phase1b.2

---

## 1. Аудит текущего README.md

### 1.1 Устаревшие разделы

| Раздел | Проблема | Действие |
|--------|----------|----------|
| `Status: local Phase 1A bootstrap` | Проект на Phase 1B.2 ACCEPTED (три завершённые фазы) | Заменить на актуальный статус |
| `The first runnable MCP stdio server lands in T-104` | T-104 давно реализован, MCP-сервер работает | Удалить |

### 1.2 Отсутствующие разделы (необходимо добавить)

| Раздел | Причина |
|--------|---------|
| Current Status | Нужен актуальный статус проекта (версия, фаза, тесты, live validation) |
| Features | Список реализованных возможностей по доменам |
| MCP Tools | Перечень 21 MCP-инструмента с группировкой по доменам |
| Roadmap | Дорожная карта с checkbox (Phase 1A ✅ → Phase 5) |
| Documentation | Обновлённые ссылки на все разделы docs/ |
| Project Status | Финальный статус (Stable Development) |

### 1.3 Ссылки, требующие обновления

| Текущая ссылка | Проблема | Новая ссылка |
|----------------|----------|---------------|
| `docs/phase-1a/reports/` | Только Phase 1A | Добавить `docs/phase-1b/` |
| Нет ссылки на Phase 1B docs | Отсутствует | `docs/phase-1b/` |

### 1.4 Ссылки, не требующие изменений

| Ссылка | Статус |
|--------|--------|
| `docs/README.md` | Работает, но требует собственного обновления (вне scope данного README refresh) |
| `docs/architecture/ARCHITECTURE.md` | Работает, релевантна |
| `docs/architecture/REFERENCE_USAGE_POLICY.md` | Будет добавлена |

## 2. План изменений

| Шаг | Действие | Файл |
|-----|----------|------|
| 1 | Заменить заголовок статуса на актуальный | README.md |
| 2 | Добавить Current Status с версией, фазой, тестами | README.md |
| 3 | Добавить Features (8 доменов) | README.md |
| 4 | Добавить MCP Tools (21 инструмент, сгруппированный) | README.md |
| 5 | Добавить Roadmap с checkbox (Phase 1A–5) | README.md |
| 6 | Обновить Documentation ссылки | README.md |
| 7 | Обновить Development команды | README.md |
| 8 | Добавить Project Status | README.md |
| 9 | Создать отчёт refresh | docs/archive/README_REFRESH_REPORT.md |

## 3. Не входит в scope

- Обновление `docs/README.md` (требует отдельного согласования)
- Изменение любого кода
- Создание или изменение release notes
- Обновление архитектурных документов
- Phase 1C
