#!/bin/bash
# GitHub repository setup script

REPO_NAME="siahl-telegram-bot"
GITHUB_USERNAME="NikolayLukyanov"

echo "Setting up GitHub repository: $REPO_NAME"
echo ""

# Check if gh CLI is installed
if command -v gh &> /dev/null; then
    echo "Using GitHub CLI to create repository..."
    gh repo create "$REPO_NAME" --public --source=. --remote=origin --push
    echo "✓ Repository created and pushed!"
else
    echo "GitHub CLI not found. Manual setup required:"
    echo ""
    echo "1. Create repository at: https://github.com/new"
    echo "   - Repository name: $REPO_NAME"
    echo "   - Description: Telegram bot for SIAHL with AI features"
    echo "   - Public repository"
    echo "   - DO NOT initialize with README, .gitignore, or license"
    echo ""
    echo "2. Then run these commands:"
    echo ""
    echo "   git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
fi
