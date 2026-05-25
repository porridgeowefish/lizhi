# Deployment Notes

This document records operational lessons from deploying the backend and frontend.

## 2026-05-25 Sort And Count Fix

### What Happened

- A backend fix was implemented and verified locally, but the frontend screenshot still showed old behavior.
- The page was reading from the cloud service, while the edited code was only present in the local workspace.
- The visible symptom was that expired opportunities still appeared at the top when sorting by deadline.

### Lesson

- Local code changes do not affect the live site until the cloud deployment script runs successfully.
- After behavior fixes that affect frontend-visible data, always verify the live API, not only local tests.
- The opportunity list count is `/api/posts.total`, which counts default-visible posts after backend filters.
- Expired actionable posts should remain visible with lower priority; they must not be hidden merely because the deadline passed.

### Required Verification

For a backend/frontend deployment, run these checks in order:

1. Run local tests:
   `python -m pytest backend\tests -q`
2. Build the frontend:
   `npm.cmd run build` from `frontend/`
3. Deploy to cloud using the configured host.
4. Verify cloud health:
   `GET http://<host>/api/health`
5. Verify live deadline sorting:
   `GET http://<host>/api/posts?limit=8&sort=deadline`
6. Confirm the first page starts with upcoming deadlines, not already expired deadlines.

### Secret Handling

- Server credentials belong only in local ignored files such as `.run/server-config.local.json`.
- Do not copy passwords into tracked docs, scripts, READMEs, issues, or commits.
- Do not upload local credential files as part of the cloud deploy bundle.
