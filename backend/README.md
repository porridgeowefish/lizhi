# Backend

This is the current backend service workspace.

## Architecture

Backend connects directly to WeRSS cloud via `WerssConnector`. No intermediary service layer.

```
WeRSS Cloud  →  WerssConnector  →  IngestionService  →  SQLite (backend.db)  →  REST API
```

## Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Configure upstream (required for sync)
set BACKEND_UPSTREAM_BASE_URL=https://your-werss-instance.example.com
set BACKEND_UPSTREAM_USERNAME=your_username
set BACKEND_UPSTREAM_PASSWORD=your_password

python -m app.main
```

When upstream is not configured, the API still serves cached data from the local database, but sync endpoints return `503`.

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
| `BACKEND_DATABASE_URL` | Database URL | `sqlite:///data/backend.db` |
| `BACKEND_UPSTREAM_BASE_URL` | WeRSS cloud API base URL | (empty) |
| `BACKEND_UPSTREAM_USERNAME` | WeRSS username | (empty) |
| `BACKEND_UPSTREAM_PASSWORD` | WeRSS password | (empty) |
| `BACKEND_SYNC_INTERVAL_MINUTES` | Sync interval | `10` |
| `BACKEND_ARTICLE_FETCH_LIMIT` | Articles per source | `50` |
| `BACKEND_SOURCE_FETCH_LIMIT` | Max sources | `100` |
| `BACKEND_ENABLE_SCHEDULER` | Enable scheduled sync | `true` |
