@echo off
REM Quick start script for local development on Windows

echo ======================================
echo SIAHL Telegram Bot - Local Development
echo ======================================
echo.

REM Check if .env exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo [OK] .env created
    echo.
    echo [IMPORTANT] Edit .env and set your TELEGRAM_BOT_TOKEN
    echo Get token from @BotFather in Telegram
    echo.
    pause
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/5] Starting PostgreSQL database...
docker-compose up -d db

echo [2/5] Waiting for database to be healthy...
timeout /t 10 /nobreak >nul

:wait_db
docker-compose exec -T db pg_isready -U siahl_user -d siahl_bot >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto wait_db
)

echo [OK] Database is ready!
echo.

REM Check if poetry is installed
where poetry >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Poetry not found!
    echo Installing Poetry...
    pip install poetry
)

echo [3/5] Installing dependencies...
poetry install

echo [4/5] Running database migrations...
poetry run alembic upgrade head

echo.
echo [5/5] Starting the bot...
echo Press Ctrl+C to stop
echo.

REM Run the bot
poetry run python src/bot.py
