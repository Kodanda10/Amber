# Agent Playbook — Amber


> Plain English product blurb (SSOT excerpt)
>
> Social Media Extraction App — Chhattisgarh Leadership Intelligence
>
> We’re building a Social Media Extraction App that tracks the digital activity of MLAs, Opposition leaders, Collectors, and District profiles across platforms. Each social post is treated as an Event. From every post we automatically extract: What (topic/message), When (time/date), Where (location/district), Whom (people present/mentioned), and Said-What (core statement/quote). This turns unstructured posts into structured datasets and individual digital profiles (leader, officer, district). The system then generates analysis reports showing activity levels, trending issues, co-appearances, and geography-wise patterns—forming a complete social intelligence map for governance, politics, and public engagement.

## Current Objective (ING-006)
- Deliver Facebook Graph ingestion (Phase 1) under feature flag.
- Persist platform metadata: `platformPostId`, `mediaUrl`, `avatarUrl` in `Post.metrics`.
- Ensure frontend renders avatars + Hindi date badges via backend data.
- Document every change in ToDoList change log and reference TDD evidence.

## Operating Rules
1. **Plan → TDD → Implement → Verify → Document** in that order. Never skip red → green → refactor.
2. Touch one concern per task. Archive or remove legacy assets per current guidance (Vite stack fully removed; Next.js is canonical).
3. Keep coverage ≥ 85% lines / 70% branches; run `npm run test` and `python3 -m pytest` (scoped) locally before PR.
4. Update `ToDoList.md`, `GEMINI.md`, `PRD.md` for every scope change; keep acceptance checklist live.
5. Feature flag risky paths (`FACEBOOK_GRAPH_ENABLED`) and provide rollback notes in PR template.

## PR Workflow
- Create short-lived branch `feature/ing-006-graph`.
- Commit with Conventional Commit + task id (e.g., `feat(ingest): add graph client [ING-006]`).
- Push, open PR using `.github/pull_request_template.md` checklist.
- Request Codex/Copilot review; ensure Vercel preview deploys.
- On merge, toggle flag in env + monitor `/api/health` + metrics.

## Local Commands
```bash
# Backend tests
cd nextjs-app/backend
python3 -m pytest tests/test_facebook_ingestion.py

# Frontend tests
cd ../
npm run test

# Coverage (requires pytest-cov / vitest --coverage)
node ../scripts/enforce-coverage.js --summary coverage/coverage-summary.json
```

Keep this file synchronized with the policy repo (`.agent-policy`). EOF
