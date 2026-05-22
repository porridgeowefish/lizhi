# Rebuild Constraints

## Naming

- Use `post` for internal domain, database, API, frontend, and docs.
- Keep upstream WeRSS endpoint names contained inside `WerssConnector`.
- Do not reintroduce public article routes, serializers, or frontend helpers.

## Pipeline

- Prescreen must remain before raw storage and LLM.
- Discarded content must not enter `raw_payloads`, `posts`, or `post_projections`.
- LLM output is candidate data only.
- Ranking and participation status stay rule-derived.

## Documentation

- Durable decisions live in Markdown.
- HTML is allowed only for short-lived alignment surfaces.
- Obsolete alignment drafts and mocks should be deleted when they compete with current source-of-truth docs.
