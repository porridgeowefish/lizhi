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


class LlmStatus(StrEnum):
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    FALLBACK = "fallback"


class TimeStatus(StrEnum):
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    EXPIRED = "expired"
    UNDATED = "undated"


class TimelinessLevel(StrEnum):
    NORMAL = "normal"
    LOW = "low"
    HIDDEN = "hidden"


class ParticipationStatus(StrEnum):
    PARTICIPABLE = "participable"
    UNCERTAIN = "uncertain"
    NON_PARTICIPABLE = "non_participable"


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


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD = "dead"
    CANCELLED = "cancelled"


class JobType(StrEnum):
    REFRESH_SOURCE = "refresh_source"
    SYNC_SOURCE_POSTS = "sync_source_posts"
    FETCH_CONTENT = "fetch_content"
    LLM_POST = "llm_post"
    CLEANUP_JOBS = "cleanup_jobs"


class SyncStage(StrEnum):
    FETCH_SOURCES = "fetch_sources"
    FETCH_POSTS = "fetch_posts"
    PRESCREEN = "prescreen"
    STORE_RAW_PAYLOAD = "store_raw_payload"
    FETCH_DETAIL = "fetch_detail"
    NORMALIZE = "normalize"
    LLM_EXTRACT = "llm_extract"
    PROJECT = "project"
    PERSIST = "persist"


class DiscardReason(StrEnum):
    RECAP = "recap"
    CLOSURE = "closure"
    CONGRATULATION = "congratulation"
    PUBLICITY_RESULT = "publicity_result"
    INTRODUCTION = "introduction"
    OPINION = "opinion"
    TUTORIAL = "tutorial"
    RECORD_ONLY = "record_only"
    GARBLED_HIDDEN_SOURCE = "garbled_hidden_source"
    NON_CAMPUS = "non_campus"
