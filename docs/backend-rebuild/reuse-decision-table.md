# Reuse Decision Table

| Existing Asset | Decision | Current Shape |
| --- | --- | --- |
| WeRSS source list endpoint | Reuse | Wrapped by `fetch_sources()` |
| WeRSS upstream content endpoint | Reuse behind connector | Wrapped by `fetch_posts()` |
| Old product content API | Delete | Public API is `/api/posts` |
| Old product content tables | Delete | Active tables are `posts`, `post_categories`, and `post_projections` |
| Old content-type filtering docs | Delete | Superseded by the iter-1 PRD |
| Old frontend design mocks | Delete | Frontend implementation is the active UI surface |
| Rule keyword classifier | Reuse and strengthen | Strong prescreen plus projection rules |
| Sync job records | Reuse and extend | Includes discard counts and per-stage items |
