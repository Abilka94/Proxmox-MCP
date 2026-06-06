# Release Notes — v0.1.0-phase1a

**Дата:** 2026-06-06
**Milestone:** Phase 1A — Infrastructure Read Layer

---

## Основные достижения

Реализован и подтверждён на реальном кластере **Infrastructure Read Layer** — набор из 16 read-only MCP инструментов, обеспечивающих полную наблюдаемость кластера Proxmox VE. Все инструменты зарегистрированы в MCP registry, покрыты модульными тестами (91 тест) и проверены на трёхнодовом кластере PVE 8.x с реальным API-токеном.

Архитектура проекта: Domain Layer → PVE Client (async httpx) → Pydantic models → MCP Tool Registry. Все инструменты имеют уровень доступа `ToolTier.READ` и безопасны для использования в режиме `READ_ONLY`.

---

## Реализованные возможности

### 8 доменов, 16 MCP инструментов

| Домен | Инструменты | Описание |
|-------|-------------|----------|
| Cluster | `cluster_info` | Информация о кластере, состав нод |
| Nodes | `list_nodes`, `node_status` | Список нод и детальный статус каждой |
| VMs | `vm_list`, `vm_status`, `vm_config` | Виртуальные машины: список, статус, конфигурация |
| Containers | `container_list`, `container_status`, `container_config` | LXC контейнеры: список, статус, конфигурация |
| Storage | `storage_list`, `storage_status`, `storage_content` | Хранилища: список, статус, содержимое (ISO, шаблоны, бэкапы) |
| Network | `network_list` | Сетевые интерфейсы на каждой ноде |
| Updates | `node_updates`, `cluster_updates` | APT-обновления на нодах и по кластеру в целом |
| System | `server_info` | Метаданные сервера (версия, режим политики) |

### Ключевые архитектурные решения

- **Единый async HTTP client** на базе `httpx` для всех PVE API-запросов
- **Pydantic v2 модели** для типизированного парсинга ответов PVE API
- **FakePveClient** в тестах — лёгкие fake-классы вместо моков, изолирующие MCP-слой от реального API
- **ToolTier.READ** для всех инструментов — гарантия read-only режима на уровне Policy Engine
- **Грациозная деградация** в `cluster_updates` — при недоступности обновлений на отдельных нодах возвращаются частичные результаты с маркером ошибки

---

## Результаты Live Validation

### Connection Validation

```
config loaded: connection=local
connected: 3 node(s)
  - pve (online)
  - pve3 (online)
  - pve2 (online)
```

### MCP Tool Validation

```
16 passed, 3 failed (permissions), 0 skipped / 19 total
```

Все инструменты, не требующие расширенных прав токена, успешно отработали на реальном кластере.

---

## Исправленные дефекты

| Дефект | Причина | Исправление |
|--------|---------|-------------|
| `container_list` → HTTP 400 | PVE 8.x не поддерживает параметр `type=lxc` | `pve/client/core.py`: запрос через `type=vm` + фильтрация по полю `type=lxc` |
| `network_list` → ValidationError | Поле `families` описано как `str`, но PVE возвращает `list[str]` | `pve/models/responses.py`: тип изменён на `list[str] \| None` |

---

## Известные ограничения

1. **`node_updates` требует PVEAuditor** — API-токен должен иметь право `Sys.Audit` на `/`. Дефолтный read-only токен не может выполнять этот запрос.
2. **Нет авто-загрузки `.env`** — Python-код не загружает `.env`-файлы. Переменные окружения должны быть установлены внешними средствами (shell, Docker, systemd).
3. **`pydantic-settings` не используется** — зависимость присутствует в `pyproject.toml`, но не задействована. Прямого маппинга `env var → config key` нет.
4. **`verify_ssl` и `timeout` статичны** — задаются только в YAML, не переопределяются через переменные окружения.

---

## Требуемые права токена

Минимальная рекомендуемая роль для работы всех read-only инструментов — **PVEAuditor** (встроенная роль Proxmox VE). Подробная таблица привилегий — в `PHASE_1A_ACCEPTANCE.md`.

---

## Направление следующей фазы

**Phase 1B: Orchestrator Layer** — реализация многошаговых операций (создание VM, оркестрация бэкапов, batch-операции). Потребуется:
- Orchestrator service с шаговым исполнителем (step sequencer)
- Отслеживание состояния задач (job id, progress, result)
- MCP-обёртки для оркестрируемых операций
- Аудит и уведомления о выполнении

---

## Состав релиза

- 19 изменённых файлов исходного кода и тестов
- 12 новых файлов (документация, скрипты валидации, отчёты)
- 91 модульный тест (100% pass)
- Подтверждение на реальном кластере: 3 ноды, PVE 8.x

## Phase 1A Status: ACCEPTED
