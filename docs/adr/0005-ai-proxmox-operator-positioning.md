# ADR-0005: Позиционирование — AI Infrastructure Operator для Proxmox VE

**Статус:** accepted  
**Дата:** 2026-06-03

## Контекст

Review Report предложил эволюцию в универсальный Infrastructure Operator Framework. Продуктовая цель — глубокий **AI-ассистент сисадмина** именно для Proxmox, пригодный для OSS без размывания доменной модели PVE.

Оператор не должен предполагать конкретную инсталляцию (число нод, имена VM, набор сервисов).

## Решение

1. Проект — **специализированный AI Infrastructure Operator для Proxmox VE**, не framework.  
2. **Единственная** платформа v1 — Proxmox VE (LXC, QEMU/KVM, PVE API, PVE RBAC).  
3. Сохраняются **нативные** сущности: Cluster, Node, LXC, VM, Storage, Network, Task, Backup, Update.  
4. Оператор **instance-agnostic**: топология и inventory определяются через API при подключении.  
5. Публичный MCP-контракт остаётся в пространстве имён **`pve_*`** / **`pve://`**.

## Последствия

### Положительные

- Чёткий message для OSS и contributors.  
- Глубина интеграции с PVE без costs абстракций Workload/Provider.

### Отрицательные

- Портирование на VMware/K8s — отдельный проект, не в scope.

### Нейтральные

- ARCHITECTURE.md v0.2 переписывает §1; Review Report C-01–C-04 не применяются.

## Связанные документы

- `docs/reviews/ARCHITECTURE_REVIEW_2026-06-03.md`  
- `docs/recommendations/ARCHITECTURE_UPDATE_RECOMMENDATIONS.md`
