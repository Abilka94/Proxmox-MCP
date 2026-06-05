# ADR-0002: Primary MCP Transport

**Статус:** accepted  
**Дата:** 2026-06-03  
**Зависит от:** [ADR-0001](0001-implementation-language.md) (accepted)

## Контекст

MCP-сервер взаимодействует с клиентами (Cursor, Claude Desktop, Open WebUI, MCP Inspector) через транспорт. Варианты:

| Transport | Типичное использование |
|-----------|------------------------|
| **stdio** | Локальный subprocess, Cursor, CLI |
| **SSE** | HTTP remote, некоторые UI рядом с сервером |
| **Streamable HTTP** | Новые клиенты MCP (эволюция протокола) |

ARCHITECTURE §3.2: stdio — приоритет v1; SSE — по ADR-0002.

## Решение

### Phase 1A (v0.1.0-alpha)

**Primary transport: stdio**

- Единственный обязательный транспорт для релиза Phase 1A.  
- Entrypoint: `python -m mcp_proxmox` без HTTP-портов.  
- Документация quickstart — stdio first.

### Phase 1B+ (backlog)

**Secondary transport: SSE** (опционально)

- Реализовать после стабилизации stdio (ROADMAP T-600).  
- Bind `127.0.0.1` only по умолчанию.  
- Отдельный ADR amendment при добавлении Streamable HTTP, если потребуется клиентами.

### Не в v1

- Streamable HTTP — оценить при запросе интеграторов; не блокирует 1A.

## Обоснование stdio-first

1. **Простота deploy:** нет открытых портов; меньше attack surface.  
2. **Cursor / IDE:** нативная модель subprocess.  
3. **Phase 1A scope:** минимум moving parts (ROADMAP Technical Debt).  
4. **Docker:** stdio через `docker run -i` или compose с `stdin_open: true` — документировать в deploy/.

## Конфигурация (концепт)

```yaml
mcp:
  transport: stdio          # stdio | sse (future)
  # sse:
  #   host: 127.0.0.1
  #   port: 8007
```

В Phase 1A секция `sse` игнорируется или отсутствует.

## Последствия

### Положительные

- Быстрее T-104 (MCP bootstrap).  
- Проще CI (нет HTTP server в integration).

### Отрицательные

- Open WebUI remote MCP может требовать SSE — mitigated Phase 1B (T-600).  
- Примеры compose в deploy/ должны описать оба паттерна когда SSE готов.

### Нейтральные

- Python MCP SDK поддерживает stdio из коробки.

## Критерии готовности (при принятии)

- [ ] T-104 реализует только stdio  
- [ ] README: пример `mcpServers` для Cursor с command + args  
- [ ] T-600 заведён в backlog для SSE

## Связанные документы

- [ARCHITECTURE.md](../ARCHITECTURE.md) §3.2, §3.5  
- [IMPLEMENTATION_PACKAGE.md](../implementation/IMPLEMENTATION_PACKAGE.md)  
- [IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md) — T-001, T-600

## Статус принятия

Принято для Phase 1A; T-001 закрыт.
