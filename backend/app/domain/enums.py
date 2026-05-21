from enum import StrEnum


class SourceStatus(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class ContentStatus(StrEnum):
    READY = "ready"
    MISSING = "missing"
    FAILED = "failed"


class ContentType(StrEnum):
    ACTIONABLE = "actionable"
    REFERENCE = "reference"
    NON_ACTIONABLE = "non_actionable"
    UNKNOWN = "unknown"


class DisplayLevel(StrEnum):
    NORMAL = "normal"
    LOW = "low"
    HIDDEN = "hidden"


class IngestionStatus(StrEnum):
    NEW = "new"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


class SyncTriggerType(StrEnum):
    STARTUP = "startup"
    MANUAL = "manual"
    SCHEDULE = "schedule"


class SyncStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL_FAILED = "partial_failed"
    FAILED = "failed"


class SyncStage(StrEnum):
    FETCH_SOURCES = "fetch_sources"
    FETCH_ARTICLES = "fetch_articles"
    NORMALIZE = "normalize"
    PERSIST = "persist"

