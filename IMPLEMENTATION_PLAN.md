# SIAHL Telegram Bot - Implementation Plan

## Overview
Telegram bot для SIAHL San Jose Amateur Hockey League с умными уведомлениями, детальной аналитикой и визуализацией статистики.

**Tech Stack**: Python 3.11+, aiogram 3.x, PostgreSQL, Matplotlib, APScheduler, Railway.app, Claude API (Anthropic)

## Implementation Phases

### Phase 1: Core Infrastructure ✅ COMPLETED
**Critical Files**:
- `src/bot.py` - Bot initialization, dispatcher setup
- `src/database/models.py` - Complete SQLAlchemy schema
- `src/services/scraper/base_scraper.py` - Base async scraper
- `src/services/scraper/team_scraper.py` - Team data scraping
- `src/services/scraper/schedule_scraper.py` - Game schedules

**Deliverables**:
- ✅ Working database schema with migrations
- ✅ Functional scrapers for team/schedule data
- ✅ Basic bot responding to startup
- ✅ Docker containerization
- ✅ CI/CD pipeline

### Phase 2: User Onboarding & Basic Commands 🚧 IN PROGRESS
**Critical Files**:
- `src/handlers/start.py` - FSM onboarding flow
- `src/handlers/team_analytics.py` - `/myteam` command
- `src/database/repository.py` - DB access layer
- `src/utils/text_formatter.py` - Message formatting with emojis

**Deliverables**:
- Complete onboarding: name → team selection → verification
- `/myteam` showing W/L, player rankings
- User preferences storage
- `/help`, `/start`, `/team`, `/nextgame` commands

### Phase 3: Notifications System
**Critical Files**:
- `src/scheduler/scheduler.py` - APScheduler setup
- `src/scheduler/jobs/notifications.py` - Notification dispatch
- `src/services/notifications/game_day.py` - Morning notifications
- `src/services/scraper/locker_room_scraper.py` - Locker room parsing

**Deliverables**:
- Game day notifications at user's preferred time
- Pre-game locker room checks (3h, 1h before)
- Notification log tracking

### Phase 4: Analytics & Opponent Data
**Critical Files**:
- `src/services/scraper/player_scraper.py` - Player stats
- `src/handlers/opponent_analytics.py` - `/opponent` command
- `src/services/analytics/team_analytics.py` - Analytics engine
- `src/services/analytics/comparison.py` - H2H comparisons

**Deliverables**:
- Opponent analysis: W/L, top players
- Player stats lookup
- Head-to-head history

### Phase 5: Visualizations
**Critical Files**:
- `src/visualization/base_chart.py` - Matplotlib config
- `src/visualization/player_charts.py` - Player trend graphs
- `src/visualization/team_charts.py` - Team comparisons
- `src/visualization/comparison_charts.py` - Radar charts

**Deliverables**:
- Points accumulation line graphs
- Team W/L bar charts
- Player comparison radar charts
- Auto-send as images in Telegram

### Phase 6: Advanced Features
**Critical Files**:
- `src/services/analytics/momentum.py` - Form indicator
- `src/services/analytics/milestones.py` - Milestone tracking
- `src/services/analytics/patterns.py` - Pattern recognition
- `src/handlers/settings.py` - Comprehensive settings UI

**Deliverables**:
- Hot/Cold streak indicators
- Milestone notifications
- Pattern insights (day-of-week, rink, etc.)
- Rivalry detection

### Phase 7: Team Mode / Group Chat Features
**Critical Files**:
- `src/handlers/group_commands.py` - Group-specific commands
- `src/handlers/group_setup.py` - Group onboarding
- `src/services/group_notifications.py` - Group auto-posts
- `src/services/dialogue/conversation_handler.py` - Natural language Q&A
- `src/services/dialogue/humor_generator.py` - AI joke generation (Claude API)
- `src/middleware/group_filter.py` - Group vs private chat detection

**Deliverables**:
- Group chat detection and setup flow
- Game day/locker room auto-posts to groups
- Stats commands working in group context
- Basic dialogue: answer simple questions
- AI-generated hockey jokes (optional feature)
- Attendance tracking with inline buttons

### Phase 8: Testing & Deployment
**Critical Files**:
- `tests/unit/test_scrapers.py`
- `tests/integration/test_notifications.py`
- `docker/Dockerfile`
- `.github/workflows/ci.yml` and `deploy.yml`

**Deliverables**:
- 80%+ test coverage
- CI/CD pipeline operational
- Deployed to Railway.app
- Monitoring with Sentry

## Core Features

### 1. User Onboarding
- При `/start` запросить имя игрока (зарегистрированное в лиге)
- Выбор команд (поддержка нескольких команд одновременно)
- Верификация существования игрока через парсинг сайта лиги
- Настройка базовых предпочтений (время уведомлений, часовой пояс)

### 2. Game Day Notifications (10 AM по умолчанию, настраивается)
**Что отправляется**:
- 🏒 Информация об игре: дата, время, ринг, противник
- 📊 Inline кнопки для детальной аналитики:
  - "Моя команда" → статистика, рейтинг игрока по очкам/пенальти
  - "Противник" → W/L, топ-3 по очкам/пенальти/посещаемости
  - "Head-to-Head" → история встреч текущего сезона

**Визуализация**:
- Графики Matplotlib: тренды очков, сравнение команд
- Rich text с эмодзи (🔥 hot streak, 📉 cold streak)
- Табличные данные в монофонте

### 3. Pre-Game Locker Room Check (за 3/1 час до игры, настраивается)
- Парсинг https://stats.sharksice.timetoscore.com/display-lr-assignments.php
- Уведомление с рингом и раздевалкой (например: "San Jose Sharks - S2")
- Обновление если раздевалка изменилась с момента предыдущей проверки

### 4. Team Analytics (`/myteam`)
**Статистика своей команды**:
- W/L/T/OTL в текущем сезоне
- Позиция в дивизионе, очки
- Goals For/Against, разница голов
- Power Play / Penalty Kill %

**Рейтинг игрока внутри команды**:
- По очкам (Goals + Assists)
- По пенальти (Penalty Minutes)
- Plus/Minus

### 5. Opponent Analytics (`/opponent` или кнопка в уведомлении)
**Анализ противника**:
- W/L record в сезоне
- Топ-3 игрока по очкам (настраивается N)
- Топ-3 по пенальти
- Топ-3 по посещаемости (Games Played)
- Recent form (последние 5 игр)

### 6. Personal Player Stats (`/mystats`)
- GP, Goals, Assists, Points
- Shooting % (Goals/Shots)
- PPG, PPA, SHG (специальные команды)
- Plus/Minus
- График накопления очков за сезона
- Тренды производительности

## Additional Features (Инновационный функционал)

### 7. Advanced Analytics
- **Performance Momentum** 🔥: Индикатор формы (Hot/Cold/Steady)
- **Rivalry Detector** ⚔️: Автоопределение частых противников
- **Milestone Tracker** 🎯: Отслеживание приближающихся вех
- **Clutch Performance** 💪: Статистика в close games
- **Attendance Impact** 📈: "Team is 8-2 when you play"
- **Pattern Recognition** 🧠: Производительность по дням недели/рингам

### 8. Enhanced Visualizations
- **Heat Maps**: Performance по неделям сезона
- **Radar Charts**: Сравнение игрока с топ-игроками
- **Season Arc**: Проекция финальной позиции

### 9. Social Features
- **Leaderboards** 🏆: Рейтинги команды с эмодзи бейджами
- **Shareable Graphics** 📸: Auto-generated player cards
- **Season Predictions** 🔮: "On pace for 45 points this season"

### 10. Smart Commands
**Schedule Management**:
- `/schedule` - расписание команды
- `/nextgame` - следующая игра с анализом
- `/calendar` - экспорт в iCal

**Player Lookup**:
- `/playerstats [name]` - поиск любого игрока лиги
- `/compare [player1] [player2]` - сравнение игроков

**Settings**:
- `/settings` - настройки уведомлений, timezone
- `/timezone` - выбор часового пояса
- `/notifications` - вкл/выкл типов уведомлений

### 11. Post-Game Features (Optional)
- Post-Game Summary (опционально)
- Топ-перформеры игры
- Влияние на standings
- Playoff implications

### 12. Team Mode (Group Chat Integration) 🏒👥

**Core Features**:
- **Game Day Reminders**: Автопост в группу утром в день игры
- **Locker Room Updates**: За 3/1 час до игры
- **Post-Game Auto-Summary**: Автопост после завершения

**On-Demand Stats**:
- `/teamstats` - Полная статистика команды
- `/nextgame` - Информация о следующей игре
- `/standings` - Позиция в дивизионе
- `/roster` - Список игроков
- `/schedule` - Ближайшие 5 игр

**Social Features**:
- **AI-Generated Hockey Humor** 🤖😄 (Claude API)
- **Basic Dialogue & Interaction** 💬: Natural language Q&A
- **Attendance Tracking** 📊 (future)
- **Team Polls** 🗳️ (future)
- **Trash Talk Mode** 🔥💬 (future, optional)

## Tech Stack Details

### Database Schema (PostgreSQL)
**Key tables**:
- `users` - Telegram user info
- `player_profiles` - Link users to SIAHL players
- `teams` - Team data from league
- `player_teams` - Multi-team associations
- `games` - Schedule and results
- `user_preferences` - Notification settings
- `stats_cache` - Scraped data cache (JSONB)
- `player_statistics` - Historical player stats
- `team_statistics` - Historical team stats
- `notification_log` - Sent notifications tracking
- `group_chats` - Team group chat configurations
- `group_preferences` - Group notification/feature settings
- `attendance_responses` - Player attendance tracking
- `conversation_context` - Last N messages for dialogue (TTL: 1 hour)

### Data Sources
**SIAHL Website URLs**:
- Team List: `https://stats.sharksice.timetoscore.com/display-stats.php?league=1`
- Team Schedule/Stats: `display-schedule?team=TEAM_ID&season=SEASON&league=LEAGUE&stat_class=CLASS`
- Locker Rooms: `https://stats.sharksice.timetoscore.com/display-lr-assignments.php`

**Scraping Strategy**:
- aiohttp + BeautifulSoup4 for async HTML parsing
- Rate limiting: 2 requests/sec
- Retry logic with exponential backoff (3 retries max)
- Cache scraped data (TTL: 1h short-term, 6h stats, 24h historical)

### Notification Scheduler (APScheduler)
**Jobs**:
- Daily Cache Refresh (2 AM PST)
- Game Day Check (every 1 min)
- Pre-Game Check (every 15 min)
- Post-Game Monitor (every 30 min)

### AI Integration (Claude API for Team Mode)
**Use Cases**:
- Hockey Humor Generation 🤖
- Natural Language Dialogue 💬
- Trash Talk Generator (optional) 🔥

**Implementation**:
- Model: `claude-3-5-haiku-20241022` (fast & cheap)
- Cost Optimization: Pattern matching first, Claude fallback
- Rate limit: Max 10 AI calls per group per day

## Deployment

### Platform: Railway.app
**Infrastructure**:
- Docker container: Python 3.11, 512 MB RAM (1 GB recommended)
- PostgreSQL 15 managed service, 1 GB storage
- Single instance (stateless except DB)
- Health check endpoint
- Sentry for error tracking

### Environment Variables
```bash
TELEGRAM_BOT_TOKEN=your_token
DATABASE_URL=postgresql://...
SIAHL_BASE_URL=https://stats.sharksice.timetoscore.com
DEFAULT_LEAGUE_ID=1
CURRENT_SEASON=72
ANTHROPIC_API_KEY=your_anthropic_key_here
AI_FEATURES_ENABLED=true
AI_RATE_LIMIT_PER_GROUP=10
```

## Testing Strategy
- pytest with >80% coverage
- Unit tests: Scrapers, analytics, visualizations
- Integration tests: Database, notifications
- E2E tests: User flows (onboarding, commands)

## Success Metrics

### User Engagement
- Target: 70% of users check notifications weekly
- Target: 50 DAU within first month
- Target: Average 5 commands per user per week

### Technical Performance
- Notification delivery: >95% success rate
- Scraping uptime: >99%
- Cache hit ratio: >85%
- Average response time: <2 seconds

## Estimated Costs

### Monthly Operating Costs:
- Railway.app: $5-10 (Hobby plan with PostgreSQL)
- Sentry: Free tier (up to 5k events/month)
- Claude API (Team Mode with AI): ~$2-5/month for 10-20 groups
- **Total**: ~$6-11/month (without AI), ~$8-16/month (with AI features)

### Scaling costs (1000+ users):
- Railway.app Professional: ~$20/month
- Redis caching (if needed): +$5/month
- Claude API (100+ groups): ~$10-15/month
- **Total**: ~$35-40/month

## Next Steps

1. ✅ Create GitHub repo `siahl-telegram-bot`
2. ✅ Set up basic project structure
3. ✅ Implement Phase 1 (Core Infrastructure)
4. 🚧 Implement Phase 2 (User Onboarding & Basic Commands)
5. Gradually add features by phases
6. Deploy to Railway.app
7. Invite first beta-testers from the league

Ready to build! 🏒🚀
