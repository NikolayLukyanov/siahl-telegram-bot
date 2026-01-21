# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SIAHL Telegram Bot for San Jose Amateur Hockey League - provides smart notifications, team analytics, player stats, and AI-powered features for hockey players.

**Current Status:** Phase 2 Complete (User Onboarding & Basic Commands). See `IMPLEMENTATION_PLAN.md` for the 8-phase roadmap.

## Common Commands

```bash
# Install dependencies
poetry install

# Run the bot
poetry run bot
# or: python src/bot.py

# Run all tests with coverage
pytest tests/

# Run a single test file
pytest tests/unit/test_scrapers.py

# Run a specific test
pytest tests/unit/test_scrapers.py::test_function_name -v

# Lint
poetry run ruff check src/

# Type check
poetry run mypy src/

# Format code
poetry run black src/

# Database migrations
alembic upgrade head                          # Apply migrations
alembic revision --autogenerate -m "desc"     # Create new migration
alembic downgrade -1                          # Rollback one

# Docker local development
docker-compose up -d                          # Start services
docker-compose up -d --build                  # Rebuild and start
docker-compose logs -f bot                    # View logs
```

## Architecture

### Entry Point & Request Flow

```
src/bot.py (main)
    ├── Creates async PostgreSQL engine + session pool
    ├── Initializes Bot (aiogram) with HTML parse mode
    ├── Creates Dispatcher with MemoryStorage FSM
    ├── Registers routers: start_router, help_router, team_router
    └── Applies DatabaseMiddleware (injects session into handlers)

Telegram Update → DatabaseMiddleware → Router → Handler(message, state, session)
```

### Handler Pattern

Handlers receive database session via middleware injection:
```python
@router.message(Command("myteam"))
async def myteam_handler(message: Message, session: AsyncSession):
    # session is injected by DatabaseMiddleware
```

FSM states are defined in handler files and managed by aiogram's built-in FSM.

### Scraper Pattern

All scrapers extend `BaseScraper` which provides:
- Async aiohttp session management
- Rate limiting (configurable delay between requests)
- Retry logic with exponential backoff (3 retries max)
- 30-second request timeout

```python
# Example usage
async with TeamScraper() as scraper:
    teams = await scraper.get_all_teams()
```

### Database

- SQLAlchemy 2.0 async with asyncpg driver
- 13 tables (users, teams, games, player_profiles, player_teams, etc.)
- All models in `src/database/models.py`
- Migrations in `alembic/versions/`
- Connection pooling: pool_size=10, max_overflow=20

### Configuration

`src/config.py` uses Pydantic Settings loading from `.env`:
- Access via `from src.config import settings`
- Key settings: `telegram_bot_token`, `database_url`, `siahl_base_url`, `current_season`
- AI features require `anthropic_api_key` and `ai_features_enabled=true`

## Data Sources

SIAHL website at `https://stats.sharksice.timetoscore.com`:
- Team stats: `display-stats.php?league=1`
- Schedules: `display-schedule?team=TEAM_ID&season=SEASON`
- Locker rooms: `display-lr-assignments.php`

Rate limit scraping to 2 requests/sec. User-Agent: `SIAHL-Bot/1.0`.

## Code Style

- Line length: 120 characters (ruff + black)
- Type hints encouraged but `disallow_untyped_defs = false`
- Async throughout (aiogram, SQLAlchemy, aiohttp)
- Logging via loguru: `from loguru import logger`

## Testing

- pytest with asyncio_mode="auto"
- Coverage target: 80%+
- Use `aioresponses` for mocking HTTP, `freezegun` for time
- CI runs: ruff → mypy → black --check → pytest

## Key Files for Each Phase

- **Phase 1 (Done):** `database/models.py`, `services/scraper/*.py`
- **Phase 2 (Done):** `handlers/start.py` (FSM onboarding), `handlers/team_analytics.py`
- **Phase 3 (Next):** `scheduler/`, `services/notifications/`
- **Phase 7 (AI):** `services/dialogue/claude_client.py`, `services/dialogue/humor_generator.py`
