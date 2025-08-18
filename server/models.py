from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field, create_engine, Session, select

from .settings import DB_PATH


class Dream(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    audio_path: str
    transcript: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sleep_start: Optional[datetime] = None
    sleep_end: Optional[datetime] = None
    stress_level: Optional[int] = Field(default=None, ge=0, le=10)
    diet_tags: Optional[str] = None

    sentiment_compound: Optional[float] = None
    emotions_json: Optional[str] = None  # JSON string of emotion scores
    keywords_json: Optional[str] = None  # JSON string of keywords
    themes_json: Optional[str] = None    # JSON list of themes

    weather_json: Optional[str] = None   # JSON blob of weather features
    moon_phase: Optional[float] = None   # 0..29.53 age
    moon_phase_name: Optional[str] = None


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def get_all_dreams(limit: int = 100) -> List[Dream]:
    with get_session() as session:
        statement = select(Dream).order_by(Dream.created_at.desc()).limit(limit)
        return list(session.exec(statement))
