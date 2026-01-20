"""Add initial database schema with all models

Revision ID: 001
Revises:
Create Date: 2026-01-19 16:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)

    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('team_name', sa.String(length=255), nullable=False),
        sa.Column('division', sa.String(length=100), nullable=True),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'season', name='uq_team_season')
    )
    op.create_index(op.f('ix_teams_team_id'), 'teams', ['team_id'], unique=True)

    # Create player_profiles table
    op.create_table(
        'player_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('player_name', sa.String(length=255), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'player_name', 'season', name='uq_user_player_season')
    )

    # Create player_teams table
    op.create_table(
        'player_teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_profile_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['player_profile_id'], ['player_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_profile_id', 'team_id', 'season', name='uq_player_team_season')
    )

    # Create games table
    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('game_date', sa.Date(), nullable=False),
        sa.Column('game_time', sa.Time(), nullable=False),
        sa.Column('rink', sa.String(length=255), nullable=True),
        sa.Column('home_team_id', sa.Integer(), nullable=True),
        sa.Column('away_team_id', sa.Integer(), nullable=True),
        sa.Column('home_score', sa.Integer(), nullable=True),
        sa.Column('away_score', sa.Integer(), nullable=True),
        sa.Column('game_type', sa.String(length=50), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('locker_room_home', sa.String(length=50), nullable=True),
        sa.Column('locker_room_away', sa.String(length=50), nullable=True),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_games_game_id'), 'games', ['game_id'], unique=True)
    op.create_index('idx_game_date', 'games', ['game_date'])
    op.create_index('idx_teams', 'games', ['home_team_id', 'away_team_id'])

    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('game_day_notification_time', sa.Time(), nullable=True),
        sa.Column('game_day_notifications_enabled', sa.Boolean(), nullable=True),
        sa.Column('pre_game_check_enabled', sa.Boolean(), nullable=True),
        sa.Column('pre_game_check_hours', sa.Integer(), nullable=True),
        sa.Column('post_game_summary_enabled', sa.Boolean(), nullable=True),
        sa.Column('top_players_count', sa.Integer(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create stats_cache table
    op.create_table(
        'stats_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('cache_type', sa.String(length=50), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key')
    )
    op.create_index('idx_cache_key', 'stats_cache', ['cache_key'])
    op.create_index('idx_expires_at', 'stats_cache', ['expires_at'])

    # Create player_statistics table
    op.create_table(
        'player_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_name', sa.String(length=255), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('games_played', sa.Integer(), nullable=True),
        sa.Column('goals', sa.Integer(), nullable=True),
        sa.Column('assists', sa.Integer(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('penalty_minutes', sa.Integer(), nullable=True),
        sa.Column('plus_minus', sa.Integer(), nullable=True),
        sa.Column('ppg', sa.Integer(), nullable=True),
        sa.Column('ppa', sa.Integer(), nullable=True),
        sa.Column('shg', sa.Integer(), nullable=True),
        sa.Column('shots', sa.Integer(), nullable=True),
        sa.Column('shooting_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_name', 'team_id', 'season', name='uq_player_team_season_stats')
    )

    # Create team_statistics table
    op.create_table(
        'team_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('games_played', sa.Integer(), nullable=True),
        sa.Column('wins', sa.Integer(), nullable=True),
        sa.Column('losses', sa.Integer(), nullable=True),
        sa.Column('ties', sa.Integer(), nullable=True),
        sa.Column('otl', sa.Integer(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('goals_for', sa.Integer(), nullable=True),
        sa.Column('goals_against', sa.Integer(), nullable=True),
        sa.Column('pp_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('pk_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'season', name='uq_team_season_stats')
    )

    # Create notification_log table
    op.create_table(
        'notification_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('sent_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_notification', 'notification_log', ['user_id', 'notification_type', 'sent_at'])

    # Create group_chats table
    op.create_table(
        'group_chats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_group_id', sa.BigInteger(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('group_title', sa.String(length=255), nullable=True),
        sa.Column('linked_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_chats_telegram_group_id'), 'group_chats', ['telegram_group_id'], unique=True)

    # Create group_preferences table
    op.create_table(
        'group_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('game_day_notifications', sa.Boolean(), nullable=True),
        sa.Column('game_day_time', sa.Time(), nullable=True),
        sa.Column('pre_game_notifications', sa.Boolean(), nullable=True),
        sa.Column('post_game_summaries', sa.Boolean(), nullable=True),
        sa.Column('mention_all_members', sa.Boolean(), nullable=True),
        sa.Column('ai_jokes_enabled', sa.Boolean(), nullable=True),
        sa.Column('ai_dialogue_enabled', sa.Boolean(), nullable=True),
        sa.Column('trash_talk_enabled', sa.Boolean(), nullable=True),
        sa.Column('attendance_tracking_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['group_chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id')
    )

    # Create attendance_responses table
    op.create_table(
        'attendance_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('responded_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['group_id'], ['group_chats.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'game_id', 'user_id', name='uq_group_game_user')
    )

    # Create conversation_context table
    op.create_table(
        'conversation_context',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['group_chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_group_expires', 'conversation_context', ['group_id', 'expires_at'])

    # Create ai_usage_log table
    op.create_table(
        'ai_usage_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['group_chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_group_date', 'ai_usage_log', ['group_id', 'created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_group_date', table_name='ai_usage_log')
    op.drop_table('ai_usage_log')

    op.drop_index('idx_group_expires', table_name='conversation_context')
    op.drop_table('conversation_context')

    op.drop_table('attendance_responses')
    op.drop_table('group_preferences')

    op.drop_index(op.f('ix_group_chats_telegram_group_id'), table_name='group_chats')
    op.drop_table('group_chats')

    op.drop_index('idx_user_notification', table_name='notification_log')
    op.drop_table('notification_log')

    op.drop_table('team_statistics')
    op.drop_table('player_statistics')

    op.drop_index('idx_expires_at', table_name='stats_cache')
    op.drop_index('idx_cache_key', table_name='stats_cache')
    op.drop_table('stats_cache')

    op.drop_table('user_preferences')

    op.drop_index('idx_teams', table_name='games')
    op.drop_index('idx_game_date', table_name='games')
    op.drop_index(op.f('ix_games_game_id'), table_name='games')
    op.drop_table('games')

    op.drop_table('player_teams')
    op.drop_table('player_profiles')

    op.drop_index(op.f('ix_teams_team_id'), table_name='teams')
    op.drop_table('teams')

    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_table('users')
