# Backend

This backend now serves a rule-first opportunity engine on top of WeRSS upstream data.

## Architecture

```
WeRSS Cloud -> WerssConnector -> Prescreen + IngestionService -> SQLite -> /api/posts
```

Key runtime behavior:

- strong prescreen removes recap, closure, congratulation, publicity-result, introduction, opinion, tutorial, record-only, and garbled-hidden-source content before it enters the main pipeline
- only allowed content enters `raw_payloads`, `posts`, and `post_projections`
- optional LLM extraction can enrich summaries and candidate structured fields, but final ranking and participation state stay rule-derived

## Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

set BACKEND_UPSTREAM_BASE_URL=https://your-werss-instance.example.com
set BACKEND_UPSTREAM_USERNAME=your_username
set BACKEND_UPSTREAM_PASSWORD=your_password

python -m app.main
```

When upstream is not configured, the API still serves cached local data, but sync endpoints return `503`.

## Test

```bash
cd backend
pytest
```

## Environment Variables

| Variable | Description | Default |
| --- | --- | --- |
| `BACKEND_HOST` | Listen host | `0.0.0.0` |
| `BACKEND_PORT` | Listen port | `8002` |
| `BACKEND_DATABASE_URL` | Database URL | `sqlite:///.run/backend.db` |
| `BACKEND_UPSTREAM_BASE_URL` | WeRSS cloud API base URL | (empty) |
| `BACKEND_UPSTREAM_USERNAME` | WeRSS username | (empty) |
| `BACKEND_UPSTREAM_PASSWORD` | WeRSS password | (empty) |
| `BACKEND_SYNC_INTERVAL_MINUTES` | Sync interval | `10` |
| `BACKEND_POST_FETCH_LIMIT` | Posts fetched per source | `500` |
| `BACKEND_SOURCE_FETCH_LIMIT` | Max sources | `500` |
| `BACKEND_ENABLE_SCHEDULER` | Enable scheduled sync | `true` |
| `BACKEND_UPSTREAM_REFRESH_ENABLED` | Refresh upstream WeRSS sources before scheduled deep sync | `true` |
| `BACKEND_UPSTREAM_REFRESH_INTERVAL_MINUTES` | Upstream refresh interval | `60` |
| `BACKEND_UPSTREAM_REFRESH_START_PAGE` | WeRSS refresh start page | `0` |
| `BACKEND_UPSTREAM_REFRESH_END_PAGE` | WeRSS refresh end page | `10` |
| `BACKEND_UPSTREAM_REFRESH_REQUEST_DELAY_SECONDS` | Delay between source refresh requests | `1.0` |
| `BACKEND_UPSTREAM_REFRESH_SETTLE_SECONDS` | Wait time before downstream sync | `300` |
| `BACKEND_LLM_ENABLED` | Enable optional LLM extraction | `false` |
| `BACKEND_LLM_BASE_URL` | OpenAI-compatible LLM base URL | (empty) |
| `BACKEND_LLM_API_KEY` | LLM API key | (empty) |
| `BACKEND_LLM_MODEL` | LLM model name | (empty) |
| `BACKEND_LLM_TIMEOUT_SECONDS` | LLM timeout seconds | `30` |
| `BACKEND_LLM_PROMPT_VERSION` | Stored prompt version | `iter1-v1` |
| `BACKEND_LLM_MAX_INPUT_CHARS` | Max chars sent to LLM | `6000` |
| `BACKEND_LLM_QUEUE_ENABLED` | Enable DB-backed LLM task queue | `true` |
| `BACKEND_LLM_WORKER_INTERVAL_SECONDS` | LLM worker poll interval | `20` |
| `BACKEND_LLM_WORKER_BATCH_SIZE` | LLM tasks claimed per worker tick | `2` |
| `BACKEND_LLM_WORKER_MAX_ATTEMPTS` | Max retries per LLM task | `3` |
