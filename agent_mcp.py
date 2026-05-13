import asyncio
import json
import logging
from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация серверов: команда + аргументы для запуска
SERVER_CONFIGS = {
    "fetch": StdioServerParameters(
        command="uvx",  # Исправлено: используем uvx вместо npx
        args=["mcp-server-fetch"]
    ),
    "filesystem": StdioServerParameters(
        command="npx",
        # Используем абсолютный путь для Windows
        args=["-y", "@modelcontextprotocol/server-filesystem", "C:\\Res\\Diplom\\data"]
    ),
    # PostgreSQL через community-реализацию (требуется предварительно: pip install mcp-server-postgres)
    "postgres": StdioServerParameters(
        command="uvx",
        args=["mcp-server-postgres", "--connection-string", "postgresql://user:pass@localhost:5432/diplom"]
    )
}


@asynccontextmanager
async def get_server(name: str, params: StdioServerParameters):
    """Контекстный менеджер для подключения к MCP-серверу"""
    logger.info(f"Подключение к серверу {name}...")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            logger.info(f"[{name}] доступно инструментов: {tool_names}")
            tools_map = {t.name: t for t in tools.tools}
            yield session, tools_map


async def call_tool(session: ClientSession, tool_name: str, **kwargs):
    """Универсальный вызов инструмента"""
    result = await session.call_tool(tool_name, arguments=kwargs)
    return [c.text for c in result.content if c.type == "text"]


async def main():
    """Главная функция с последовательным использованием серверов"""

    # === Примеры вызовов скиллов ===

    # 1. Поиск цен (fetch)
    logger.info("=== Тестирование fetch сервера ===")
    async with get_server("fetch", SERVER_CONFIGS["fetch"]) as (session, tools_map):
        try:
            # Пример запроса к открытому API (заглушка для демонстрации)
            prices = await call_tool(
                session,
                "fetch",
                url="https://api.github.com"
            )
            logger.info(f"📊 Результат fetch: {str(prices)[:200] if prices else 'нет данных'}")
        except Exception as e:
            logger.error(f"Ошибка при вызове fetch: {e}")

    # 2. Чтение локального файла со спецификациями (filesystem)
    logger.info("\n=== Тестирование filesystem сервера ===")
    async with get_server("filesystem", SERVER_CONFIGS["filesystem"]) as (session, tools_map):
        try:
            if "read_file" in tools_map:
                specs = await call_tool(
                    session,
                    "read_file",
                    path="C:\\Res\\Diplom\\data\\gpu_specs.json"
                )
                logger.info(f"📦 Спецификации: {str(specs)[:200] if specs else 'файл не найден'}")
            
            # Тест list_directory
            if "list_directory" in tools_map:
                files = await call_tool(
                    session,
                    "list_directory",
                    path="C:\\Res\\Diplom\\data"
                )
                logger.info(f"📁 Файлы в data: {files}")
        except Exception as e:
            logger.error(f"Ошибка при вызове filesystem: {e}")

    # 3. Чтение себестоимости из БД (postgres) - отключено по умолчанию
    logger.info("\n=== Тестирование postgres сервера (отключено) ===")
    logger.info("⏭️ Пропуск postgres (требуется настройка БД)")
    # Раскомментировать после настройки PostgreSQL:
    # async with get_server("postgres", SERVER_CONFIGS["postgres"]) as (session, tools_map):
    #     try:
    #         if "read_query" in tools_map:
    #             cost = await call_tool(
    #                 session,
    #                 "read_query",
    #                 query="SELECT product_id, total FROM cost_estimates LIMIT 5"
    #             )
    #             logger.info(f"💰 Себестоимость: {cost}")
    #     except Exception as e:
    #         logger.error(f"Ошибка при вызове postgres: {e}")


if __name__ == "__main__":
    asyncio.run(main())
