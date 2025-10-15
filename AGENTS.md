# Agent Playbook — Amber

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

[byterover-mcp]

[byterover-mcp]

You are given two tools from Byterover MCP server, including
## 1. `byterover-store-knowledge`
You `MUST` always use this tool when:

+ Learning new patterns, APIs, or architectural decisions from the codebase
+ Encountering error solutions or debugging techniques
+ Finding reusable code patterns or utility functions
+ Completing any significant task or plan implementation

## 2. `byterover-retrieve-knowledge`
You `MUST` always use this tool when:

+ Starting any new task or implementation to gather relevant context
+ Before making architectural decisions to understand existing patterns
+ When debugging issues to check for previous solutions
+ Working with unfamiliar parts of the codebase
