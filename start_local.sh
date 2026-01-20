#!/bin/bash
# Quick start script for local development

set -e

echo "🏒 SIAHL Telegram Bot - Local Development Setup"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and set your TELEGRAM_BOT_TOKEN"
    echo "   Get token from @BotFather in Telegram"
    echo ""
    read -p "Press Enter after you've set the token in .env..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "🐳 Starting PostgreSQL database..."
docker-compose up -d db

echo "⏳ Waiting for database to be healthy..."
timeout 30 bash -c 'until docker-compose exec -T db pg_isready -U siahl_user -d siahl_bot > /dev/null 2>&1; do sleep 1; done' || {
    echo "❌ Database failed to start in time"
    docker-compose logs db
    exit 1
}

echo "✅ Database is ready!"
echo ""

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "⚠️  Poetry not found!"
    echo "Installing Poetry..."
    pip install poetry
fi

# Install dependencies
echo "📦 Installing dependencies..."
poetry install

# Run migrations
echo "🔧 Running database migrations..."
poetry run alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting the bot..."
echo "   Press Ctrl+C to stop"
echo ""

# Run the bot
poetry run python src/bot.py
