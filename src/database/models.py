"""SQLAlchemy database models for SIAHL Telegram Bot."""

from datetime import datetime, time
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    Date,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """Telegram users table."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    player_profiles = relationship("PlayerProfile", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="user", cascade="all, delete-orphan")


class PlayerProfile(Base):
    """Player profiles linking users to SIAHL players."""

    __tablename__ = "player_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    player_name = Column(String(255), nullable=False)
    league_id = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "player_name", "season", name="uq_user_player_season"),
    )

    # Relationships
    user = relationship("User", back_populates="player_profiles")
    player_teams = relationship("PlayerTeam", back_populates="player_profile", cascade="all, delete-orphan")


class Team(Base):
    """Teams from SIAHL league."""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, unique=True, nullable=False, index=True)  # SIAHL team ID
    team_name = Column(String(255), nullable=False)
    division = Column(String(100))
    season = Column(Integer, nullable=False)
    league_id = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("team_id", "season", name="uq_team_season"),
    )

    # Relationships
    player_teams = relationship("PlayerTeam", back_populates="team", cascade="all, delete-orphan")
    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")
    statistics = relationship("TeamStatistic", back_populates="team", cascade="all, delete-orphan")
    group_chats = relationship("GroupChat", back_populates="team", cascade="all, delete-orphan")


class PlayerTeam(Base):
    """Player-Team associations for multi-team support."""

    __tablename__ = "player_teams"

    id = Column(Integer, primary_key=True)
    player_profile_id = Column(Integer, ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    season = Column(Integer, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("player_profile_id", "team_id", "season", name="uq_player_team_season"),
    )

    # Relationships
    player_profile = relationship("PlayerProfile", back_populates="player_teams")
    team = relationship("Team", back_populates="player_teams")


class Game(Base):
    """Game schedule and results."""

    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, unique=True, nullable=False, index=True)  # SIAHL game ID
    season = Column(Integer, nullable=False)
    game_date = Column(Date, nullable=False, index=True)
    game_time = Column(Time, nullable=False)
    rink = Column(String(255))
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    home_score = Column(Integer)
    away_score = Column(Integer)
    game_type = Column(String(50))
    is_completed = Column(Boolean, default=False)
    locker_room_home = Column(String(50))
    locker_room_away = Column(String(50))
    last_updated = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_game_date", "game_date"),
        Index("idx_teams", "home_team_id", "away_team_id"),
    )

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    attendance_responses = relationship("AttendanceResponse", back_populates="game", cascade="all, delete-orphan")


class UserPreference(Base):
    """User notification and display preferences."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    game_day_notification_time = Column(Time, default=time(10, 0))
    game_day_notifications_enabled = Column(Boolean, default=True)
    pre_game_check_enabled = Column(Boolean, default=True)
    pre_game_check_hours = Column(Integer, default=3)
    post_game_summary_enabled = Column(Boolean, default=False)
    top_players_count = Column(Integer, default=3)
    timezone = Column(String(50), default="America/Los_Angeles")
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")


class StatsCache(Base):
    """Cache for scraped statistics."""

    __tablename__ = "stats_cache"

    id = Column(Integer, primary_key=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    cache_type = Column(String(50), nullable=False)  # 'team_stats', 'player_stats', 'standings', etc.
    data = Column(JSONB, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_cache_key", "cache_key"),
        Index("idx_expires_at", "expires_at"),
    )


class PlayerStatistic(Base):
    """Historical player performance data."""

    __tablename__ = "player_statistics"

    id = Column(Integer, primary_key=True)
    player_name = Column(String(255), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"))
    season = Column(Integer, nullable=False)
    games_played = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    points = Column(Integer, default=0)
    penalty_minutes = Column(Integer, default=0)
    plus_minus = Column(Integer, default=0)
    ppg = Column(Integer, default=0)  # Power play goals
    ppa = Column(Integer, default=0)  # Power play assists
    shg = Column(Integer, default=0)  # Shorthanded goals
    shots = Column(Integer, default=0)
    shooting_percentage = Column(Numeric(5, 2))
    last_updated = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("player_name", "team_id", "season", name="uq_player_team_season_stats"),
    )

    # Relationships
    team = relationship("Team")


class TeamStatistic(Base):
    """Historical team performance."""

    __tablename__ = "team_statistics"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    season = Column(Integer, nullable=False)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    otl = Column(Integer, default=0)  # Overtime losses
    points = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    pp_percentage = Column(Numeric(5, 2))  # Power play %
    pk_percentage = Column(Numeric(5, 2))  # Penalty kill %
    last_updated = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("team_id", "season", name="uq_team_season_stats"),
    )

    # Relationships
    team = relationship("Team", back_populates="statistics")


class NotificationLog(Base):
    """Track sent notifications."""

    __tablename__ = "notification_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"))
    notification_type = Column(String(50), nullable=False)  # 'game_day', 'pre_game', 'post_game'
    sent_at = Column(DateTime, default=func.now())
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    __table_args__ = (
        Index("idx_user_notification", "user_id", "notification_type", "sent_at"),
    )

    # Relationships
    user = relationship("User", back_populates="notifications")
    game = relationship("Game")


# Group Chat Models (Team Mode)

class GroupChat(Base):
    """Team group chat configurations."""

    __tablename__ = "group_chats"

    id = Column(Integer, primary_key=True)
    telegram_group_id = Column(BigInteger, unique=True, nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    group_title = Column(String(255))
    linked_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    team = relationship("Team", back_populates="group_chats")
    created_by = relationship("User")
    preferences = relationship("GroupPreference", back_populates="group", uselist=False, cascade="all, delete-orphan")
    attendance_responses = relationship("AttendanceResponse", back_populates="group", cascade="all, delete-orphan")
    conversation_context = relationship("ConversationContext", back_populates="group", cascade="all, delete-orphan")
    ai_usage = relationship("AIUsageLog", back_populates="group", cascade="all, delete-orphan")


class GroupPreference(Base):
    """Group notification and feature settings."""

    __tablename__ = "group_preferences"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("group_chats.id", ondelete="CASCADE"), unique=True, nullable=False)
    game_day_notifications = Column(Boolean, default=True)
    game_day_time = Column(Time, default=time(9, 0))
    pre_game_notifications = Column(Boolean, default=True)
    post_game_summaries = Column(Boolean, default=True)
    mention_all_members = Column(Boolean, default=False)
    ai_jokes_enabled = Column(Boolean, default=False)
    ai_dialogue_enabled = Column(Boolean, default=True)
    trash_talk_enabled = Column(Boolean, default=False)
    attendance_tracking_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    group = relationship("GroupChat", back_populates="preferences")


class AttendanceResponse(Base):
    """Player attendance tracking."""

    __tablename__ = "attendance_responses"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("group_chats.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False)  # 'going', 'not_going', 'maybe'
    responded_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("group_id", "game_id", "user_id", name="uq_group_game_user"),
    )

    # Relationships
    group = relationship("GroupChat", back_populates="attendance_responses")
    game = relationship("Game", back_populates="attendance_responses")
    user = relationship("User")


class ConversationContext(Base):
    """Conversation context for AI dialogue (with TTL)."""

    __tablename__ = "conversation_context"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("group_chats.id", ondelete="CASCADE"), nullable=False)
    message_text = Column(Text, nullable=False)
    user_id = Column(BigInteger)  # Telegram user ID (may not be in users table)
    username = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)  # TTL: 1 hour

    __table_args__ = (
        Index("idx_group_expires", "group_id", "expires_at"),
    )

    # Relationships
    group = relationship("GroupChat", back_populates="conversation_context")


class AIUsageLog(Base):
    """AI rate limiting tracking."""

    __tablename__ = "ai_usage_log"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("group_chats.id", ondelete="CASCADE"), nullable=False)
    request_type = Column(String(50), nullable=False)  # 'joke', 'dialogue', 'trash_talk'
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_group_date", "group_id", "created_at"),
    )

    # Relationships
    group = relationship("GroupChat", back_populates="ai_usage")
