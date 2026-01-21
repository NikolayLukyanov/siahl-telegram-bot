"""Main bot entry point.

This module initializes and runs the SIAHL Telegram bot.
"""

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from src.config import settings


async def on_startup(bot: Bot, db_engine) -> None:
    """
    Execute on bot startup.

    Args:
        bot: Bot instance
        db_engine: Database engine from workflow data
    """
    logger.info("Bot is starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"SIAHL Base URL: {settings.siahl_base_url}")

    # Set bot commands (Phase 2)
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="Set up your profile"),
        BotCommand(command="help", description="Show available commands"),
        BotCommand(command="myteam", description="View team statistics"),
        BotCommand(command="nextgame", description="Get next game info"),
        BotCommand(command="about", description="About this bot"),
    ])
    logger.info("Bot commands set successfully")

    # Initialize database (Phase 2)
    from src.database.connection import init_db
    await init_db(db_engine)
    logger.info("Database initialized successfully")

    # Start scheduler
    # TODO: Add scheduler initialization in Phase 3

    me = await bot.get_me()
    logger.info(f"Bot started as @{me.username} (ID: {me.id})")


async def on_shutdown(bot: Bot, db_engine) -> None:
    """
    Execute on bot shutdown.

    Args:
        bot: Bot instance
        db_engine: Database engine from workflow data
    """
    logger.info("Bot is shutting down...")

    # Stop scheduler
    # TODO: Add scheduler shutdown in Phase 3

    # Close database connections (Phase 2)
    if db_engine:
        await db_engine.dispose()
        logger.info("Database connections closed")

    logger.info("Bot shutdown complete")


async def main() -> None:
    """
    Main bot execution function.

    This function:
    1. Initializes the bot and dispatcher
    2. Registers handlers
    3. Starts polling
    """
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
    )

    # Optional file logging (disabled for now)
    # if hasattr(settings, 'log_file') and settings.log_file:
    #     logger.add(
    #         settings.log_file,
    #         rotation="10 MB",
    #         retention="1 week",
    #         format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    #         level=settings.log_level,
    #     )

    logger.info("Initializing bot...")

    # Initialize database (Phase 2)
    from src.database.connection import create_engine, create_session_pool

    db_engine = create_engine()
    session_pool = create_session_pool(db_engine)
    logger.info("Database engine created")

    # Initialize bot
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    # Initialize dispatcher with FSM storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Store engine in dispatcher workflow data for startup/shutdown
    dp.workflow_data.update(db_engine=db_engine)

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Register message handlers (Phase 2)
    from src.handlers import start_router, help_router, team_router
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(team_router)

    # Register middleware (Phase 2)
    from src.middleware import DatabaseMiddleware
    dp.update.middleware(DatabaseMiddleware(session_pool=session_pool))
    logger.info("Middleware registered")

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    except Exception as e:
        logger.exception(f"Critical error in bot polling: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
