# Настройка MCP-серверов для проекта

## Установленные сервера


| Сервер         | Команда                                          | Статус                  |
| -------------- | ------------------------------------------------ | ----------------------- |
| **fetch**      | `uvx mcp-server-fetch`                           | ✅ Работает              |
| **filesystem** | `npx -y @modelcontextprotocol/server-filesystem` | ✅ Работает              |
| **postgres**   | `uvx mcp-server-postgres`                        | ⏸️ Требует настройки БД |


## Конфигурация Qwen CLI

Файл: `~/.qwen/config.yaml` (Windows: `C:\Users\Антон\.qwen\config.yaml`)

### MCP-серверы

```yaml
mcpServers:
  filesystem:
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "C:\\Res\\Diplom\\data"
    disabled: false

  fetch:
    command: uvx
    args:
      - "mcp-server-fetch"
    disabled: false

  postgres:
    command: uvx
    args:
      - "mcp-server-postgres"
      - "--connection-string"
      - "postgresql://user:pass@localhost:5432/diplom"
    disabled: true  # Включить после настройки PostgreSQL
```

### Tools (скиллы для агента)

```yaml
tools:
  - search_market_prices    # Получение цен через fetch-MCP
  - query_cost_data         # Запрос себестоимости из PostgreSQL
  - read_local_specs        # Чтение локальных JSON-спецификаций
  - calculate_markup        # Расчёт наценки с учётом факторов
  - recommend_alternatives  # Подбор аналогов
```

## Тестирование

Запуск клиента:

```bash
cd C:\Res\Diplom
python agent_mcp.py
```

## Структура проекта

```
C:\Res\Diplom\
├── agent_mcp.py                 # MCP-клиент для тестирования серверов
├── project_spec.md              # Спецификация проекта
├── MCP_SETUP.md                 # Этот файл
├── data/                        # Разрешённая директория для filesystem сервера
│   └── gpu_specs.json           # Пример файла спецификаций
├── backend/
│   └── data_pipeline/           # Скрипты обработки данных
│       ├── __init__.py
│       ├── calc_markup.py       # Расчёт наценки
│       └── find_alternatives.py # Подбор аналогов
└── .qwen/
    └── config.yaml              # Конфигурация Qwen CLI
```

## Важные заметки

1. **PostgreSQL сервер** отключён по умолчанию. Для включения:
  - Установите PostgreSQL 15+
  - Создайте БД `diplom`
  - Обновите connection-string в config.yaml
  - Измените `disabled: true` на `false`
2. **filesystem сервер** ограничен директорией `C:\Res\Diplom\data` для безопасности
3. **Логирование** включено в `agent_mcp.py` для отладки вызовов инструментов
4. **Скрипты data_pipeline** принимают JSON через stdin или аргументы командной строки

## Следующие шаги

1. Настроить PostgreSQL и включить postgres сервер
2. Создать модели БД через SQLAlchemy
3. Реализовать FastAPI бэкенд
4. Разработать React фронтенд

