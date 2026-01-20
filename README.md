# SIAHL Telegram Bot

Telegram bot для SIAHL San Jose Amateur Hockey League с умными уведомлениями, детальной аналитикой и визуализацией статистики.

## Features

### Core Features
- **Personal Notifications**: Game day reminders, locker room assignments, pre-game checks
- **Team Analytics**: W/L records, player rankings, team stats
- **Opponent Scouting**: Detailed analysis of opponents with top players
- **Player Stats**: Personal performance tracking with visualizations
- **Advanced Analytics**: Performance momentum, rivalry detection, milestone tracking

### Team Mode (Group Chat Integration)
- **Auto-Posts**: Game reminders, locker room updates, post-game summaries
- **AI Dialogue**: Natural language Q&A powered by Claude API
- **AI Jokes**: Context-aware hockey humor (optional)
- **Attendance Tracking**: Who's coming to games (future)
- **Team Leaderboards**: Rankings and stats in group chat

## Tech Stack

- **Python 3.11+** with aiogram 3.x
- **PostgreSQL** for database
- **Matplotlib** for charts
- **APScheduler** for notifications
- **Claude API** (Anthropic) for AI features
- **Railway.app** for deployment

## Installation

### Prerequisites
- Python 3.11+ (managed with pyenv)
- Poetry for dependency management
- PostgreSQL 15+
- Telegram Bot Token (from @BotFather)
- Anthropic API Key (optional, for AI features)

### Setup

1. Install pyenv and Poetry:
```bash
# Install pyenv (macOS/Linux)
curl https://pyenv.run | bash

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Windows users: Use pyenv-win and install Poetry via pip
```

2. Clone the repository:
```bash
git clone https://github.com/yourusername/siahl-telegram-bot.git
cd siahl-telegram-bot
```

3. Set up Python version and install dependencies:
```bash
# Install Python 3.11.9 with pyenv
pyenv install 3.11.9

# Poetry will automatically use .python-version
poetry install

# Activate virtual environment
poetry shell
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the bot:
```bash
poetry run bot
# or
poetry shell
python src/bot.py
```

## Environment Variables

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/siahl_bot

# SIAHL League
SIAHL_BASE_URL=https://stats.sharksice.timetoscore.com
DEFAULT_LEAGUE_ID=1
CURRENT_SEASON=72

# AI Features (optional)
ANTHROPIC_API_KEY=your_anthropic_key_here
AI_FEATURES_ENABLED=true
AI_RATE_LIMIT_PER_GROUP=10

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn_here
```

## Development

### Running Tests
```bash
# All tests
pytest tests/

# With coverage
pytest --cov=src --cov-report=html tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/
```

### Code Quality
```bash
# Linting
poetry run ruff check src/

# Type checking
poetry run mypy src/

# Format code
poetry run black src/
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

### Docker
```bash
# Build image
docker build -t siahl-bot -f docker/Dockerfile .

# Run with docker-compose
docker-compose up -d
```

### Railway.app
1. Connect GitHub repository
2. Add environment variables
3. Deploy automatically on push to main

## Project Structure

```
siahl-telegram-bot/
├── src/
│   ├── bot.py                      # Entry point
│   ├── config.py                   # Configuration
│   ├── handlers/                   # Command handlers
│   ├── services/                   # Business logic
│   │   ├── scraper/               # Web scraping
│   │   ├── analytics/             # Analytics engine
│   │   ├── notifications/         # Notification logic
│   │   └── dialogue/              # AI dialogue
│   ├── visualization/             # Chart generation
│   ├── database/                  # SQLAlchemy models
│   ├── scheduler/                 # APScheduler jobs
│   └── utils/                     # Utilities
├── tests/                         # Test suite
├── docker/                        # Docker configs
└── .github/workflows/             # CI/CD
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- SIAHL San Jose for the hockey league
- Anthropic for Claude API
- aiogram community for the excellent Telegram framework
