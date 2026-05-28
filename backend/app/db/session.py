from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.db.base import Base


def build_engine(settings: Settings):
    is_sqlite = settings.database_url.startswith("sqlite")
    connect_args = {"check_same_thread": False, "timeout": 5} if is_sqlite else {}
    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "", 1)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(settings.database_url, connect_args=connect_args)
    if is_sqlite:
        _configure_sqlite(engine)
    return engine


def _configure_sqlite(engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def build_session_factory(settings: Settings) -> tuple[object, sessionmaker[Session]]:
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)
    _ensure_schema_columns(engine)
    _drop_legacy_tables(engine)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _ensure_schema_columns(engine) -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if "sources" not in existing_tables:
        return

    source_columns = {column["name"] for column in inspector.get_columns("sources")}
    missing_source_columns = {
        "last_seen_published_at": "DATETIME",
        "last_seen_upstream_post_id": "VARCHAR(255) DEFAULT ''",
    }
    with engine.begin() as connection:
        for column_name, column_type in missing_source_columns.items():
            if column_name not in source_columns:
                connection.execute(text(f"ALTER TABLE sources ADD COLUMN {column_name} {column_type}"))


def _drop_legacy_tables(engine) -> None:
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    legacy_tables = [name for name in ("article_categories", "articles") if name in existing]
    if not legacy_tables:
        return

    with engine.begin() as connection:
        for table in legacy_tables:
            connection.execute(text(f"DROP TABLE IF EXISTS {table}"))
