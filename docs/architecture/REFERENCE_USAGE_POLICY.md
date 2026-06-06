# Reference Usage Policy

**Date:** 2026-06-06
**Status:** Adopted
**Scope:** All phases of Proxmox-MCP development

---

## 1. Purpose

Formalise how and when the reference repositories (`RekklesNA/`, `bsahane/`) are consulted during development of the primary project (`Proxmox-MCP/`).

---

## 2. Ground Rules

1. **Reference repositories are not used continuously.** They are consulted on a targeted, as-needed basis only.

2. **Reference repositories are not the default source of architectural decisions.** The primary project develops independently. Reference code is one input among many (PVE API docs, ADRs, live validation, team expertise).

3. **The primary project evolves independently.** Design decisions are driven by:
   - Project-specific requirements (MCP-first, async, policy-driven)
   - PVE API behaviour discovered during live validation
   - Internal architecture decisions recorded in ADRs

4. **Comparative analysis is performed selectively** — at defined checkpoints rather than continuously.

---

## 3. Mandatory Comparative Analysis Points

Comparative analysis against at least one reference repository is required before:

| Trigger | Rationale |
|---------|-----------|
| Start of a new major phase | Ensure no missed patterns or endpoints |
| Designing mutate functionality | RekklesNA and bsahane both implement POST operations |
| Designing backup/snapshot tools | RekklesNA has production backup/restore/snapshot |
| Designing VM/LXC create/delete | Both references implement full lifecycle |
| Designing Job Store | RekklesNA JobStore is the primary reference |
| Designing Operator Layer | RekklesNA security model and command policy |
| Architectural uncertainty | Any case where existing patterns don't clearly guide the design |

---

## 4. Exemptions (No Comparative Analysis Required)

Comparative analysis is **not** required for:

| Type | Rationale |
|------|-----------|
| Small READ functions | Trivial, well-understood patterns |
| Local fixes | Not architectural |
| Bugfix-only changes | Reactive, not design-driven |
| Tests and documentation | Not production code |

---

## 5. Documentation Requirements

When comparative analysis is performed, the results must be recorded in a file at:

```
docs/archive/COMPARISON_<DOMAIN>_<DATE>.md
```

Each report must contain:

1. **What was compared** — specific files, functions, or patterns from each reference
2. **What was adopted** — concrete decisions taken from the reference
3. **What was rejected** — concrete decisions not taken, with reasons
4. **Rationale** — why each decision was made

---

## 6. Relationship to WORKSPACE_MAP.md

This policy supersedes the informal "research value" notes in `WORKSPACE_MAP.md` Section 6. The workspace boundary rules (read-only for references, read-write for primary) remain unchanged.

---

## 7. Enforcement

- This policy is advisory for Phase 1B.2 and earlier phases.
- Starting from Phase 1C (mutate operations), the mandatory analysis points in Section 3 become required before implementation begins.
- Non-compliance has no penalty but increases the risk of missed patterns or design rework.
