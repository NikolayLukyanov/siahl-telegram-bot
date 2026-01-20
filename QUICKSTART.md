# Quick Start Guide - Local Testing

## Prerequisites
- Docker & Docker Compose installed ✅
- Telegram Bot Token (from @BotFather)

## Step 1: Get Telegram Bot Token

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Follow instructions:
   - Bot name: `SIAHL Test Bot` (or any name)
   - Bot username: `siahl_test_bot` (must end with `_bot`)
4. Copy the **token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Create .env file

```bash
# In the project root directory
cp .env.example .env
```

Then edit `.env` and set:
```bash
# Required: Your bot token from BotFather
TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE

# Database (Docker will handle this automatically)
DATABASE_URL=postgresql+asyncpg://siahl_user:changeme@localhost:5432/siahl_bot

# Optional: Set DB password (or use default 'changeme')
DB_PASSWORD=changeme

# Everything else can stay default for testing
```

## Step 3: Start PostgreSQL Database

```bash
# Start only the database
docker-compose up -d db

# Check if database is running
docker-compose ps
```

You should see:
```
NAME             STATUS         PORTS
siahl-bot-db    Up (healthy)   0.0.0.0:5432->5432/tcp
```

## Step 4: Install Python Dependencies

```bash
# Check Python version (need 3.11+)
python --version

# Install Poetry if not installed
pip install poetry

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

## Step 5: Run Database Migrations

```bash
# Apply migrations to create tables
alembic upgrade head
```

You should see:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Add initial database schema with all models
```

## Step 6: Start the Bot

```bash
# Make sure you're in poetry shell
poetry shell

# Run the bot
python src/bot.py
```

You should see:
```
2026-01-19 18:30:00 | INFO     | Initializing bot...
2026-01-19 18:30:00 | INFO     | Database engine created
2026-01-19 18:30:01 | INFO     | Bot started as @your_bot_username (ID: 123456789)
2026-01-19 18:30:01 | INFO     | Starting bot polling...
```

## Step 7: Test the Bot

1. Open Telegram
2. Search for your bot by username
3. Send `/start`
4. Follow the onboarding flow!

## Available Commands (Phase 2)

- `/start` - Set up your profile
- `/help` - Show available commands
- `/myteam` - View team statistics
- `/nextgame` - Get next game info
- `/about` - About the bot

## Troubleshooting

### Database Connection Error
```bash
# Check if database is running
docker-compose ps

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Bot Token Invalid
- Double check token in `.env` file
- Make sure no extra spaces or quotes
- Get new token from @BotFather if needed

### Import Errors
```bash
# Make sure you're in poetry shell
poetry shell

# Reinstall dependencies
poetry install
```

### Alembic Migration Errors
```bash
# Check current migration status
alembic current

# If stuck, reset migrations (WARNING: deletes data!)
alembic downgrade base
alembic upgrade head
```

## Stop Everything

```bash
# Stop the bot: Ctrl+C in terminal

# Stop database
docker-compose down

# Stop and remove volumes (deletes database data!)
docker-compose down -v
```

## Alternative: Run Everything in Docker

If you want to run the bot in Docker too:

```bash
# Build and start both database and bot
docker-compose up --build

# View logs
docker-compose logs -f bot

# Stop everything
docker-compose down
```

**Note:** When running in Docker, you'll need to rebuild the image after code changes:
```bash
docker-compose up --build bot
```

## Next Steps

After testing Phase 2 functionality:
- Phase 3: Notifications System (game day reminders, locker room checks)
- Phase 4: Opponent Analytics
- Phase 5: Visualizations (charts with Matplotlib)

## Useful Commands

```bash
# View running containers
docker-compose ps

# View bot logs
docker-compose logs -f bot

# Access database
docker-compose exec db psql -U siahl_user -d siahl_bot

# Run tests
pytest tests/

# Lint code
ruff check src/

# Type check
mypy src/
```

Good luck testing! 🏒🚀
