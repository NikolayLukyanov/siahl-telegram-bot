"""Database middleware for injecting AsyncSession into handlers."""

from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to provide database session to handlers."""

    def __init__(self, session_pool: async_sessionmaker):
        """
        Initialize database middleware.

        Args:
            session_pool: SQLAlchemy async sessionmaker
        """
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Inject database session into handler data.

        Args:
            handler: Handler function
            event: Telegram event (message, callback, etc.)
            data: Handler data dictionary

        Returns:
            Handler result
        """
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)
