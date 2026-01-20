"""Help command handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command - show available commands."""
    help_text = """
🏒 <b>SIAHL Bot - Available Commands</b>

<b>📋 Getting Started</b>
/start - Set up your profile and select team(s)
/help - Show this help message

<b>📊 Team & Stats</b>
/myteam - View your team's statistics and your rankings
/nextgame - Get info about your next game
/schedule - View upcoming games (coming soon)
/mystats - View your personal player statistics (coming soon)

<b>🔍 Opponent Analysis</b>
/opponent - Analyze your next opponent (coming soon)
/compare - Compare players (coming soon)

<b>⚙️ Settings</b>
/settings - Configure notification preferences (coming soon)
/timezone - Set your timezone (coming soon)
/notifications - Manage notification types (coming soon)

<b>🔔 Notifications</b>
You'll receive:
• <b>Game Day Reminders</b> (10 AM by default)
• <b>Pre-Game Locker Room</b> assignments (3h before game)
• <b>Post-Game Summaries</b> (optional)

<b>💡 Tips</b>
• You can add multiple teams if you play for more than one
• All times are in your configured timezone (PST by default)
• Use inline buttons in notifications for quick access to stats

<b>🤝 Team Mode (Group Chats)</b>
Add me to your team's group chat for:
• Automatic game day posts
• Team stats commands
• AI-powered Q&A (coming soon)
• Attendance tracking (coming soon)

<i>Need help? Contact support or report issues on GitHub.</i>
    """

    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("about"))
async def cmd_about(message: Message):
    """Handle /about command - show bot info."""
    about_text = """
🏒 <b>SIAHL Telegram Bot</b>

<b>Version:</b> 1.0.0 (Phase 2)
<b>League:</b> SIAHL San Jose Amateur Hockey League

<b>Features:</b>
✅ Automated game day notifications
✅ Pre-game locker room assignments
✅ Team statistics and analytics
✅ Player performance tracking
✅ Opponent scouting reports
✅ Advanced analytics & visualizations

<b>Tech Stack:</b>
• Python 3.11+ with aiogram 3.x
• PostgreSQL database
• Matplotlib for visualizations
• APScheduler for notifications
• Claude API for AI features

<b>Data Source:</b>
All data is scraped from the official SIAHL website:
https://stats.sharksice.timetoscore.com

<b>Privacy:</b>
• Your data is stored securely
• We only collect necessary information
• No data sharing with third parties
• GDPR compliant

<b>Open Source:</b>
This bot is open source! Check out the code:
https://github.com/NikolayLukyanov/siahl-telegram-bot

<i>Built with ❤️ for SIAHL players</i>
    """

    await message.answer(about_text, parse_mode="HTML")
