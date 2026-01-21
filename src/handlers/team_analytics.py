"""Team analytics command handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database.models import User, PlayerProfile, Team, PlayerTeam, TeamStatistic
from src.services.scraper.team_scraper import TeamScraper
from src.config import settings

router = Router()


@router.message(Command("myteam"))
async def cmd_myteam(message: Message, session: AsyncSession):
    """Handle /myteam command - show team statistics."""
    telegram_id = message.from_user.id

    # Get user with player profiles and teams
    result = await session.execute(
        select(User)
        .filter(User.telegram_id == telegram_id)
        .options(
            joinedload(User.player_profiles).joinedload(PlayerProfile.player_teams).joinedload(PlayerTeam.team)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.player_profiles:
        await message.answer(
            "❌ You haven't set up your profile yet!\n\n"
            "Use /start to get started.",
            parse_mode="HTML"
        )
        return

    # Get primary team or first team
    primary_team = None
    for profile in user.player_profiles:
        for pt in profile.player_teams:
            if pt.is_primary:
                primary_team = pt.team
                break
        if primary_team:
            break

    if not primary_team and user.player_profiles[0].player_teams:
        primary_team = user.player_profiles[0].player_teams[0].team

    if not primary_team:
        await message.answer(
            "❌ No team found for your profile.\n\n"
            "Please set up your profile again with /start",
            parse_mode="HTML"
        )
        return

    # Fetch fresh team stats
    await message.answer("🔍 Fetching team statistics...", parse_mode="HTML")

    try:
        scraper = TeamScraper()

        # Get team stats
        teams_data = await scraper.get_all_teams()
        team_info = next(
            (t for t in teams_data if t["team_id"] == primary_team.team_id),
            None
        )

        if not team_info:
            await message.answer(
                f"❌ Could not find statistics for {primary_team.team_name}.\n\n"
                "The team might not have played any games yet.",
                parse_mode="HTML"
            )
            return

        # Format team statistics
        wins = team_info.get("wins", 0)
        losses = team_info.get("losses", 0)
        ties = team_info.get("ties", 0)
        otl = team_info.get("otl", 0)
        points = team_info.get("points", 0)
        goals_for = team_info.get("goals_for", 0)
        goals_against = team_info.get("goals_against", 0)
        goal_diff = goals_for - goals_against
        division = team_info.get("division", "Unknown")

        # Calculate winning percentage
        total_games = wins + losses + ties + otl
        win_pct = (wins / total_games * 100) if total_games > 0 else 0
        avg_gf = goals_for / total_games if total_games > 0 else 0
        avg_ga = goals_against / total_games if total_games > 0 else 0
        form_status = "🔥 Hot Streak!" if wins >= losses else "📉 Needs Improvement"

        # Build response
        response = f"""
🏒 <b>{primary_team.team_name}</b>

<b>📊 Season Record</b>
Division: {division}
Record: {wins}-{losses}-{ties}-{otl}
Points: {points}
Win %: {win_pct:.1f}%

<b>⚽ Goals</b>
Goals For: {goals_for}
Goals Against: {goals_against}
Goal Differential: {goal_diff:+d}
Avg GF/Game: {avg_gf:.2f}
Avg GA/Game: {avg_ga:.2f}

<b>📈 Form</b>
{form_status}
Last 5 Games: <i>Coming soon</i>

<b>🎯 Your Ranking</b>
<i>Player rankings coming in next update!</i>

<i>Stats updated from SIAHL website</i>
        """

        # Create inline keyboard for more options
        keyboard = [
            [
                InlineKeyboardButton(
                    text="📅 Next Game",
                    callback_data=f"next_game:{primary_team.team_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Full Stats",
                    url=f"{settings.siahl_base_url}/display-schedule?team={primary_team.team_id}&season={settings.current_season}"
                )
            ]
        ]

        # Add team selection if user has multiple teams
        if len(user.player_profiles) > 1 or any(len(p.player_teams) > 1 for p in user.player_profiles):
            keyboard.append([
                InlineKeyboardButton(
                    text="🔄 Switch Team",
                    callback_data="switch_team"
                )
            ])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await message.answer(
            response,
            reply_markup=markup,
            parse_mode="HTML"
        )

        # Update team statistics in database
        team_stat = await session.execute(
            select(TeamStatistic)
            .filter(
                TeamStatistic.team_id == primary_team.id,
                TeamStatistic.season == settings.current_season
            )
        )
        team_stat = team_stat.scalar_one_or_none()

        if team_stat:
            # Update existing
            team_stat.games_played = total_games
            team_stat.wins = wins
            team_stat.losses = losses
            team_stat.ties = ties
            team_stat.otl = otl
            team_stat.points = points
            team_stat.goals_for = goals_for
            team_stat.goals_against = goals_against
        else:
            # Create new
            team_stat = TeamStatistic(
                team_id=primary_team.id,
                season=settings.current_season,
                games_played=total_games,
                wins=wins,
                losses=losses,
                ties=ties,
                otl=otl,
                points=points,
                goals_for=goals_for,
                goals_against=goals_against
            )
            session.add(team_stat)

        await session.commit()

    except Exception as e:
        await message.answer(
            f"❌ Error fetching team statistics: {str(e)}\n\n"
            "Please try again later.",
            parse_mode="HTML"
        )


@router.message(Command("nextgame"))
async def cmd_nextgame(message: Message, session: AsyncSession):
    """Handle /nextgame command - show next game info."""
    telegram_id = message.from_user.id

    # Get user with teams
    result = await session.execute(
        select(User)
        .filter(User.telegram_id == telegram_id)
        .options(
            joinedload(User.player_profiles).joinedload(PlayerProfile.player_teams).joinedload(PlayerTeam.team)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.player_profiles:
        await message.answer(
            "❌ You haven't set up your profile yet!\n\n"
            "Use /start to get started.",
            parse_mode="HTML"
        )
        return

    # Get primary team
    primary_team = None
    for profile in user.player_profiles:
        for pt in profile.player_teams:
            if pt.is_primary:
                primary_team = pt.team
                break
        if primary_team:
            break

    if not primary_team and user.player_profiles[0].player_teams:
        primary_team = user.player_profiles[0].player_teams[0].team

    if not primary_team:
        await message.answer(
            "❌ No team found for your profile.",
            parse_mode="HTML"
        )
        return

    await message.answer("🔍 Fetching next game...", parse_mode="HTML")

    try:
        # Fetch schedule
        from src.services.scraper.schedule_scraper import ScheduleScraper

        scraper = ScheduleScraper()

        games = await scraper.get_team_schedule(team_id=primary_team.team_id)

        # Find next upcoming game
        from datetime import datetime
        now = datetime.now()

        upcoming_games = [
            g for g in games
            if datetime.combine(g["game_date"], g["game_time"]) > now
        ]

        if not upcoming_games:
            await message.answer(
                f"📅 No upcoming games found for {primary_team.team_name}.\n\n"
                "The season might be over or the schedule hasn't been published yet.",
                parse_mode="HTML"
            )
            return

        # Get next game
        next_game = min(upcoming_games, key=lambda g: datetime.combine(g["game_date"], g["game_time"]))

        # Determine if home or away
        is_home = next_game.get("home_team_id") == primary_team.team_id
        opponent = next_game.get("away_team") if is_home else next_game.get("home_team")

        game_datetime = datetime.combine(next_game["game_date"], next_game["game_time"])

        response = f"""
🏒 <b>Next Game</b>

<b>📅 When</b>
{game_datetime.strftime("%A, %B %d, %Y")}
{game_datetime.strftime("%I:%M %p")}

<b>🏟️ Where</b>
{next_game.get("rink", "TBD")}

<b>🆚 Opponent</b>
{opponent or "TBD"}
{"(Home)" if is_home else "(Away)"}

<b>🚪 Locker Room</b>
<i>Check back 3 hours before game time</i>

<i>Good luck! 🍀</i>
        """

        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton(
                    text="📊 Opponent Stats",
                    callback_data=f"opponent_stats:{opponent}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗺️ Rink Directions",
                    url=f"https://www.google.com/maps/search/{next_game.get('rink', '').replace(' ', '+')}"
                )
            ]
        ]

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await message.answer(
            response,
            reply_markup=markup,
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(
            f"❌ Error fetching next game: {str(e)}\n\n"
            "Please try again later.",
            parse_mode="HTML"
        )
