"""Start command handler with user onboarding FSM."""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, PlayerProfile, Team, UserPreference
from src.services.scraper.team_scraper import TeamScraper
from src.config import settings

router = Router()


class OnboardingStates(StatesGroup):
    """FSM states for user onboarding."""
    waiting_for_player_name = State()
    waiting_for_team_selection = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Handle /start command - initiate onboarding."""
    telegram_id = message.from_user.id

    # Check if user already exists
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(User)
        .filter(User.telegram_id == telegram_id)
        .options(selectinload(User.player_profiles))
    )
    user = result.scalar_one_or_none()

    if user and user.player_profiles:
        # User already onboarded
        await message.answer(
            f"Welcome back, {user.first_name}! 🏒\n\n"
            f"You're all set up with {len(user.player_profiles)} team(s).\n\n"
            f"Use /help to see available commands."
        )
        return

    # Start onboarding
    await message.answer(
        "🏒 <b>Welcome to SIAHL Bot!</b>\n\n"
        "I'll help you track your hockey stats, get game reminders, "
        "and analyze your opponents.\n\n"
        "Let's get you set up! First, what's your <b>player name</b> "
        "as registered in SIAHL?\n\n"
        "<i>Example: John Doe</i>",
        parse_mode="HTML"
    )

    # Create user if doesn't exist
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    await state.set_state(OnboardingStates.waiting_for_player_name)


@router.message(OnboardingStates.waiting_for_player_name)
async def process_player_name(message: Message, state: FSMContext, session: AsyncSession):
    """Process player name and fetch teams."""
    player_name = message.text.strip()

    if not player_name or len(player_name) < 3:
        await message.answer(
            "❌ Please provide a valid player name (at least 3 characters).",
            parse_mode="HTML"
        )
        return

    await message.answer("🔍 Searching for teams...", parse_mode="HTML")

    try:
        # Fetch teams from SIAHL
        scraper = TeamScraper()

        teams_data = await scraper.get_all_teams()

        if not teams_data:
            await message.answer(
                "❌ No teams found in the current season. Please try again later.",
                parse_mode="HTML"
            )
            await state.clear()
            return

        # Store player name and teams in FSM context
        await state.update_data(
            player_name=player_name,
            teams=teams_data
        )

        # Create inline keyboard with team selection
        keyboard = []
        for idx, team in enumerate(teams_data[:20]):  # Limit to first 20 teams
            team_name = team.get("team_name", "Unknown Team")
            division = team.get("division", "")

            button_text = f"{team_name}"
            if division:
                button_text += f" ({division})"

            keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"select_team:{idx}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="❌ Cancel",
                callback_data="cancel_onboarding"
            )
        ])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await message.answer(
            f"🏒 <b>Found {len(teams_data)} teams!</b>\n\n"
            f"Select your team(s) for player <b>{player_name}</b>:\n\n"
            f"<i>(You can select multiple teams if you play for more than one)</i>",
            reply_markup=markup,
            parse_mode="HTML"
        )

        await state.set_state(OnboardingStates.waiting_for_team_selection)

    except Exception as e:
        await message.answer(
            f"❌ Error fetching teams: {str(e)}\n\n"
            f"Please try again with /start",
            parse_mode="HTML"
        )
        await state.clear()


@router.callback_query(F.data.startswith("select_team:"), OnboardingStates.waiting_for_team_selection)
async def process_team_selection(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Process team selection."""
    try:
        team_idx = int(callback.data.split(":")[1])

        # Get data from FSM
        data = await state.get_data()
        player_name = data.get("player_name")
        teams = data.get("teams", [])
        selected_teams = data.get("selected_teams", [])

        if team_idx >= len(teams):
            await callback.answer("❌ Invalid team selection", show_alert=True)
            return

        team_data = teams[team_idx]

        # Check if already selected
        if team_idx in selected_teams:
            await callback.answer("✅ Team already selected!", show_alert=True)
            return

        # Save team to database
        from sqlalchemy import select
        result = await session.execute(
            select(Team).filter(
                Team.team_id == team_data["team_id"],
                Team.season == settings.current_season
            )
        )
        team = result.scalar_one_or_none()

        if not team:
            team = Team(
                team_id=team_data["team_id"],
                team_name=team_data["team_name"],
                division=team_data.get("division"),
                season=settings.current_season,
                league_id=settings.default_league_id
            )
            session.add(team)
            await session.commit()
            await session.refresh(team)

        # Get user
        result = await session.execute(
            select(User).filter(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        # Create player profile
        player_profile = PlayerProfile(
            user_id=user.id,
            player_name=player_name,
            league_id=settings.default_league_id,
            season=settings.current_season,
            verified=False
        )
        session.add(player_profile)
        await session.commit()
        await session.refresh(player_profile)

        # Create player-team association
        from src.database.models import PlayerTeam
        player_team = PlayerTeam(
            player_profile_id=player_profile.id,
            team_id=team.id,
            season=settings.current_season,
            is_primary=len(selected_teams) == 0  # First team is primary
        )
        session.add(player_team)
        await session.commit()

        # Create default preferences if not exist
        if not user.preferences:
            preferences = UserPreference(user_id=user.id)
            session.add(preferences)
            await session.commit()

        selected_teams.append(team_idx)
        await state.update_data(selected_teams=selected_teams)

        await callback.answer(
            f"✅ Added {team_data['team_name']}!",
            show_alert=False
        )

        # Update message with option to add more or finish
        keyboard = [
            [
                InlineKeyboardButton(
                    text="✅ Finish Setup",
                    callback_data="finish_onboarding"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Add Another Team",
                    callback_data="add_another_team"
                )
            ]
        ]

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await callback.message.edit_text(
            f"🏒 <b>Team(s) Selected:</b>\n\n"
            + "\n".join([f"• {teams[idx]['team_name']}" for idx in selected_teams])
            + f"\n\n<i>Would you like to add another team or finish setup?</i>",
            reply_markup=markup,
            parse_mode="HTML"
        )

    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)


@router.callback_query(F.data == "finish_onboarding")
async def finish_onboarding(callback: CallbackQuery, state: FSMContext):
    """Finish onboarding process."""
    data = await state.get_data()
    selected_teams = data.get("selected_teams", [])

    if not selected_teams:
        await callback.answer("❌ Please select at least one team", show_alert=True)
        return

    await callback.message.edit_text(
        "✅ <b>Setup Complete!</b> 🎉\n\n"
        f"You've been added to {len(selected_teams)} team(s).\n\n"
        "You'll now receive:\n"
        "• Game day notifications (10 AM by default)\n"
        "• Pre-game locker room assignments\n"
        "• Post-game summaries (optional)\n\n"
        "Use /help to see all available commands!\n\n"
        "Use /settings to customize your notifications.",
        parse_mode="HTML"
    )

    await state.clear()


@router.callback_query(F.data == "add_another_team")
async def add_another_team(callback: CallbackQuery, state: FSMContext):
    """Show team selection again."""
    data = await state.get_data()
    teams = data.get("teams", [])
    selected_teams = data.get("selected_teams", [])

    # Create inline keyboard with remaining teams
    keyboard = []
    for idx, team in enumerate(teams[:20]):
        if idx in selected_teams:
            continue  # Skip already selected teams

        team_name = team.get("team_name", "Unknown Team")
        division = team.get("division", "")

        button_text = f"{team_name}"
        if division:
            button_text += f" ({division})"

        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"select_team:{idx}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="✅ Finish Setup",
            callback_data="finish_onboarding"
        )
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await callback.message.edit_text(
        "🏒 <b>Select another team:</b>\n\n"
        f"<i>Currently selected: {len(selected_teams)} team(s)</i>",
        reply_markup=markup,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cancel_onboarding")
async def cancel_onboarding(callback: CallbackQuery, state: FSMContext):
    """Cancel onboarding process."""
    await callback.message.edit_text(
        "❌ Onboarding cancelled.\n\n"
        "Use /start when you're ready to set up your profile.",
        parse_mode="HTML"
    )
    await state.clear()
