# Campus Opportunity Engine

Rule-first campus opportunity discovery system for WeChat official-account content.

## Read First

1. [Agent.md](./Agent.md)
2. [docs/INDEX.md](./docs/INDEX.md)
3. [docs/governance/DOCUMENT_REGISTRY.md](./docs/governance/DOCUMENT_REGISTRY.md)
4. [docs/backend-rebuild/iter-1-prd.md](./docs/backend-rebuild/iter-1-prd.md)

## Current Reality

- `posts` is the only product-facing content model.
- `articles` is only an upstream WeRSS endpoint name, not an internal table or API contract.
- Strong rule prescreening runs before raw payload storage, detail fetching, LLM extraction, projection, and persistence.
- Discarded recap, closure, congratulation, publicity-result, introduction, opinion, tutorial, record-only, and garbled-source content is recorded only in `discarded_posts`.
- The active public API is `/api/posts`, `/api/sources`, `/api/sync`, and `/api/health`.

## Local Verification

```bash
cd backend
pytest
```

```bash
cd frontend
npm run build
```
