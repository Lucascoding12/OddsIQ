"""
SQLAlchemy ORM models.

Keep models thin — no business logic here, just schema.
"""
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Game(Base):
    """A sporting event polled from The Odds API."""
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Odds API game ID
    sport_key: Mapped[str] = mapped_column(String, index=True)
    sport_title: Mapped[str] = mapped_column(String)
    home_team: Mapped[str] = mapped_column(String)
    away_team: Mapped[str] = mapped_column(String)
    commence_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    snapshots: Mapped[list["OddsSnapshot"]] = relationship(back_populates="game")


class OddsSnapshot(Base):
    """
    A snapshot of bookmaker odds for one game at a point in time.
    Raw odds stored as JSON so we don't need to normalize every market type.
    """
    __tablename__ = "odds_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), index=True)
    bookmaker: Mapped[str] = mapped_column(String, index=True)
    market: Mapped[str] = mapped_column(String)  # h2h, spreads, totals
    odds_data: Mapped[dict] = mapped_column(JSON)  # raw outcomes list
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    game: Mapped["Game"] = relationship(back_populates="snapshots")


class Bet(Base):
    """User-logged bet for PnL tracking."""
    __tablename__ = "bets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Using email as the user identifier until full auth is built.
    # Each browser session stores email in localStorage; the frontend sends it
    # as the X-User-Email header on every bets request.
    user_email: Mapped[str] = mapped_column(String, index=True, default="anonymous")
    date: Mapped[str] = mapped_column(String)
    sport: Mapped[str] = mapped_column(String)
    game: Mapped[str] = mapped_column(String)
    bet_type: Mapped[str] = mapped_column(String)
    odds: Mapped[float] = mapped_column(Float)
    stake: Mapped[float] = mapped_column(Float)
    result: Mapped[str] = mapped_column(String, default="pending")  # win | loss | pending
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    closing_odds: Mapped[float | None] = mapped_column(Float, nullable=True)
    clv: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Alert(Base):
    """User-configured price alert."""
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sport: Mapped[str] = mapped_column(String)
    team: Mapped[str] = mapped_column(String)
    market: Mapped[str] = mapped_column(String, default="h2h")
    target_odds: Mapped[float] = mapped_column(Float)
    direction: Mapped[str] = mapped_column(String, default="above")  # above | below
    active: Mapped[bool] = mapped_column(default=True)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
