# MCP-Proxmox — Documentation Index

**Текущая фаза:** Phase 1C — **ACCEPTED WITH LIMITATIONS**, локальный релиз **v0.4.0-phase1c**, Closure 2026-11-10

**Следующий шаг:** публикация коммита и тега только после отдельного разрешения; push не выполнялся, следующая Phase не начата

---

## Architecture & Design

| Документ | Назначение |
|----------|------------|
| [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) v0.2 | Runtime, MCP, Policy, Domains, tiers |
| [architecture/MEMORY_KNOWLEDGE_MODEL.md](architecture/MEMORY_KNOWLEDGE_MODEL.md) v1.0 | Memory, Service, EntityRef, traverse |
| [adr/ADR_INDEX.md](adr/ADR_INDEX.md) | Индекс архитектурных решений (ADR) |
| [releases/IMPLEMENTATION_ROADMAP.md](releases/IMPLEMENTATION_ROADMAP.md) | Фазы 1A–6, MVP |
| [architecture/REFERENCE_USAGE_POLICY.md](architecture/REFERENCE_USAGE_POLICY.md) | Правила использования reference-репозиториев |

## Phase 1A — Infrastructure Read Layer

| Подраздел | Документы |
|-----------|-----------|
| Reports | [IMPLEMENTATION_PACKAGE](phase-1a/reports/IMPLEMENTATION_PACKAGE.md), [TASK_PLAN](phase-1a/reports/PHASE_1A_TASK_PLAN.md), [PROGRESS](phase-1a/reports/PHASE_1A_PROGRESS_REPORT.md), [RELEASE_CHECKLIST](phase-1a/reports/PHASE_1A_RELEASE_CHECKLIST.md), [INFRASTRUCTURE_READ_COMPLETION](phase-1a/reports/INFRASTRUCTURE_READ_COMPLETION_REPORT.md), [DOMAIN_READ_TOOLS](phase-1a/reports/DOMAIN_READ_TOOLS_REPORT.md), [T102](phase-1a/reports/T102_IMPLEMENTATION_REPORT.md), [T104](phase-1a/reports/T104_IMPLEMENTATION_REPORT.md), [TECH_DEBT](phase-1a/reports/TECHNICAL_DEBT_REMEDIATION_REPORT.md) |
| Validation | [LIVE_CLUSTER_CONFIG](phase-1a/validation/LIVE_CLUSTER_CONFIGURATION_GUIDE.md), [LIVE_MCP_VALIDATION](phase-1a/validation/LIVE_MCP_VALIDATION_REPORT.md), [VALIDATION_EXECUTION_PLAN](phase-1a/validation/LIVE_VALIDATION_EXECUTION_PLAN.md), [VALIDATION_REMEDIATION](phase-1a/validation/VALIDATION_REMEDIATION_REPORT.md) |
| Acceptance | [PHASE_1A_ACCEPTANCE](phase-1a/acceptance/PHASE_1A_ACCEPTANCE.md) |
| Releases | [RELEASE_NOTES_v0.1.0](../docs/releases/RELEASE_NOTES_v0.1.0-phase1a.md) |

## Phase 1B.1 — Task Domain Core (read-only)

| Подраздел | Документы |
|-----------|-----------|
| Design | [TASK_DOMAIN_DESIGN](phase-1b/phase-1b.1/design/PHASE_1B_TASK_DOMAIN_DESIGN.md) |
| Implementation | [IMPLEMENTATION_REPORT](phase-1b/phase-1b.1/implementation/PHASE_1B_IMPLEMENTATION_REPORT.md) |
| Validation | [LIVE_VALIDATION_PLAN](phase-1b/phase-1b.1/validation/PHASE_1B_LIVE_VALIDATION_PLAN.md), [LIVE_VALIDATION_REPORT](phase-1b/phase-1b.1/validation/PHASE_1B_LIVE_VALIDATION_REPORT.md), [VALIDATION_REMEDIATION](phase-1b/phase-1b.1/validation/PHASE_1B_VALIDATION_REMEDIATION_REPORT.md), [CONNECTIVITY_INVESTIGATION](phase-1b/phase-1b.1/validation/PHASE_1B_CONNECTIVITY_INVESTIGATION.md) |
| Acceptance | [PHASE_1B_ACCEPTANCE](phase-1b/phase-1b.1/acceptance/PHASE_1B_ACCEPTANCE.md) |

## Phase 1B.2 — Task Domain Extended

| Подраздел | Документы |
|-----------|-----------|
| Design | [PHASE_1B_2_DESIGN](phase-1b/phase-1b.2/design/PHASE_1B_2_DESIGN.md) |
| Implementation | [IMPLEMENTATION_REPORT](phase-1b/phase-1b.2/implementation/PHASE_1B_2_IMPLEMENTATION_REPORT.md), [LIVE_VALIDATION_PLAN](phase-1b/phase-1b.2/implementation/PHASE_1B_2_LIVE_VALIDATION_PLAN.md) |
| Validation | [LIVE_VALIDATION_REPORT](phase-1b/phase-1b.2/validation/PHASE_1B_2_LIVE_VALIDATION_REPORT.md), [CONNECTIVITY_CHECK](phase-1b/phase-1b.2/validation/PRE_VALIDATION_CONNECTIVITY_CHECK.md) |
| Acceptance | [PHASE_1B_2_ACCEPTANCE](phase-1b/phase-1b.2/acceptance/PHASE_1B_2_ACCEPTANCE.md) |

## Phase 1C — Task Mutate: ACCEPTED WITH LIMITATIONS

**Phase 1C v0.4.0 — локальный релиз, ACCEPTED WITH LIMITATIONS.** FA-01–FA-04 RESOLVED, 272 теста проходят, полный Live L1–L5 PASS. Пользовательская инструкция: [корневой README](../README.md), включая task_cancel, параметры и два режима READ_ONLY/OPERATOR. ADMIN — уровень инструментов, не режим конфигурации. Исторические потенциальные credentials остаются UNVERIFIED; Ruff/mypy baseline и прочие ограничения документированы. Рабочий READ_ONLY сохранён; исторические отчёты не переписываются. Push не выполнялся.

| Подраздел | Документы |
|-----------|-----------|
| Comparative Analysis | [Сравнение reference](phase-1c/comparative-analysis/COMPARISON_TASK_MUTATION_2026-06-06.md) — исторический анализ; уточнения в отчёте revision |
| Gap Analysis | [Исходный gap-анализ](phase-1c/gap-analysis/GAP_ANALYSIS_TASK_MUTATION.md) |
| Design | [Текущий дизайн v0.3](phase-1c/design/PHASE_1C_DESIGN.md), [снимок v0.2](phase-1c/design/PHASE_1C_DESIGN_v0.2.md), [инженерный отчёт revision](phase-1c/design/PHASE_1C_DESIGN_REVISION_REPORT_v0.3.md) |
| Implementation | [Implementation v0.3](phase-1c/implementation/PHASE_1C_IMPLEMENTATION_REPORT.md), [история v0.2](phase-1c/implementation/PHASE_1C_IMPLEMENTATION_REPORT_v0.2.md), [исходный tracked diff](phase-1c/implementation/PHASE_1C_PRE_V03_TRACKED.patch) |
| Review | [Final Implementation Review v0.3](phase-1c/review/PHASE_1C_FINAL_IMPLEMENTATION_REVIEW.md) — подтверждённые замечания и окончательный пакет исправлений |
| Remediation | [Final Remediation FR-01–FR-03](phase-1c/implementation/PHASE_1C_FINAL_REMEDIATION_REPORT.md) — изменения, доказательства закрытия и результаты локальных проверок |
| Live Validation Stage A | [Отчёт этапа A](phase-1c/validation/PHASE_1C_LIVE_VALIDATION_STAGE_A_REPORT.md) — среда, READ-диагностика, права и условия допуска к B |
| Connectivity Recheck | [Повторная READ-диагностика](phase-1c/validation/PHASE_1C_PVE_CONNECTIVITY_RECHECK_REPORT.md) — HTTP 200, PVE 9.2.21, четыре online-ноды и эффективные права |
| Test Task Selection | [Выбор тестовой задачи](phase-1c/validation/PHASE_1C_TEST_TASK_SELECTION_REPORT.md) — READ-состояние 7500T, сравнение кандидатов и условный сценарий B; 5800H только резерв, CeleronG3930/7700T запрещены для тестовых изменений |
| Administrator Check | [Проверка прав и VM 301](phase-1c/validation/PHASE_1C_ADMINISTRATOR_PERMISSIONS_CHECK_REPORT.md) — 2026-11-09: Administrator/privsep/VM.PowerMgmt подтверждены, VM stopped, READ_ONLY сохранён |
| VM301 Diagnostics | [Диагностика остановки VM 301](phase-1c/validation/PHASE_1C_VM301_STOP_DIAGNOSTIC_REPORT.md) — task/syslog/RRD, загрузка ноды 6 ноября и границы достоверности вывода |
| Live Validation B | [Отчёт одного теста](phase-1c/validation/PHASE_1C_LIVE_VALIDATION_STAGE_B_REPORT.md), [безопасные evidence](phase-1c/validation/PHASE_1C_STAGE_B_EVIDENCE.json) — PASS, один POST/DELETE, VM running, READ_ONLY восстановлен |
| Acceptance | [Final Acceptance Report](phase-1c/acceptance/PHASE_1C_FINAL_ACCEPTANCE_REPORT.md) — REJECTED; матрица требований, фактические проверки, security/Git findings и условия завершения |
| Remediation FA-01 / FA-02 | [Отчёт удаления диагностических скриптов](phase-1c/acceptance/PHASE_1C_FA01_FA02_REMEDIATION_REPORT.md) — оба findings RESOLVED в согласованном объёме; зависимости, секреты, полный pytest и остаточные риски |
| Security Remediation 19.3 | [Отчёт обезличивания S2/S4](phase-1c/acceptance/PHASE_1C_SECURITY_REMEDIATION_19_3_REPORT.md) — SANITIZED в рабочем документе/index, история не изменена; повторный scan и pytest |
| Combined Remediation FA-03 / FA-04 | [Инженерный отчёт и повторная Acceptance](phase-1c/acceptance/PHASE_1C_FA03_FA04_COMBINED_REMEDIATION_REPORT.md) — FA-04 RESOLVED, FA-03 PARTIALLY RESOLVED, REJECTED |
| Remaining Live Scenarios | [План оставшихся L1–L5](phase-1c/validation/PHASE_1C_REMAINING_LIVE_SCENARIOS_PLAN.md) — спецификация выполненного пакета; новое выполнение требует нового разрешения |
| Complete Live Validation | [Отчёт L1–L5](phase-1c/validation/PHASE_1C_COMPLETE_LIVE_VALIDATION_REPORT.md), [JSON evidence](phase-1c/validation/PHASE_1C_COMPLETE_LIVE_VALIDATION_EVIDENCE.json) — все PASS; 2 POST/2 DELETE, VM running, READ_ONLY восстановлен; не Final Acceptance |
| Final Acceptance & Closure | [Итоговый Closure Report](phase-1c/acceptance/PHASE_1C_CLOSURE_REPORT.md) — ACCEPTED WITH LIMITATIONS; FA-01–FA-04 RESOLVED, утверждённый manifest из 47 файлов, v0.4.0-phase1c |
| Validation | [Аудит Codex](phase-1c/validation/PHASE_1C_CODEX_AUDIT_REPORT.md), [Pre-Validation Report](phase-1c/validation/PRE_VALIDATION_MUTATE_CHECK.md), [план v0.3](phase-1c/validation/PHASE_1C_LIVE_VALIDATION_PLAN.md), [снимок прежнего плана](phase-1c/validation/PHASE_1C_LIVE_VALIDATION_PLAN_v0.2.md) |

Правила этапов: [PROJECT_WORKFLOW_RULES.md](architecture/PROJECT_WORKFLOW_RULES.md).

## Archive

| Раздел | Документы |
|--------|-----------|
| Reports | [CODEBASE_AUDIT](archive/CODEBASE_AUDIT_REPORT.md), [COMPETITIVE_ANALYSIS](archive/COMPETITIVE_ANALYSIS.md), [CONFIGURATION_DISCOVERY](archive/CONFIGURATION_DISCOVERY_REPORT.md) |
| Reviews | [ARCHITECTURE_REVIEW_2026-06-03](archive/reviews/ARCHITECTURE_REVIEW_2026-06-03.md), [INDEPENDENT_PROJECT_REVIEW](archive/reviews/INDEPENDENT_PROJECT_REVIEW.md) |
| Audit | [DOCUMENTATION_AUDIT](archive/DOCUMENTATION_AUDIT.md), [DOCUMENTATION_CLEANUP_PLAN](archive/DOCUMENTATION_CLEANUP_PLAN.md), [REFERENCE_USAGE_AUDIT](archive/REFERENCE_USAGE_AUDIT.md) |
| Refresh | [README_REFRESH_PLAN](archive/README_REFRESH_PLAN.md), [README_REFRESH_REPORT](archive/README_REFRESH_REPORT.md) |
| Recommendations | [ARCHITECTURE_UPDATE_RECOMMENDATIONS](archive/recommendations/ARCHITECTURE_UPDATE_RECOMMENDATIONS.md) |
