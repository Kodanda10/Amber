# Agent Playbook — Amber

## Current Objective (Phase 2 — Analytics & Intelligent Datasets)
- Finalize Phase 2 roadmap for analytics, smart datasets, and Genkit chatbot integration.
- Anchor implementation to the Project Dhruv reference (TDD-driven Hindi parsing dashboard with 48-post dataset, regex extraction, Devanagari UI, health checks, feature flags, CI gates).
- Ensure ToDoList, PRD, GEMINI, and related docs reflect ANA-001…ANA-007 atomic tasks with TDD steps.
- Prepare implementation guardrails (dedup enforcement, parser snapshot, bias mitigation) before coding starts.
- Keep documentation changes isolated on dedicated worktree/branch to avoid conflicts with other agents.

## Operating Rules
1. **Plan → TDD → Implement → Verify → Document** in that order. Never skip red → green → refactor.
2. Touch one concern per task. Archive or remove legacy assets per current guidance (Vite stack fully removed; Next.js is canonical).
3. Keep coverage ≥ 85% lines / 70% branches; run `npm run test` and `python3 -m pytest` (scoped) locally before PR.
4. Update `ToDoList.md`, `GEMINI.md`, `PRD.md` for every scope change; keep acceptance checklist live.
5. Feature flag risky paths (`FACEBOOK_GRAPH_ENABLED`, `SMART_DATASET_ENABLED`, `CHATBOT_ENABLED`) and provide rollback notes in PR template.

## PR Workflow
- Create short-lived branch `feature/ing-006-graph`.
- Commit with Conventional Commit + task id (e.g., `feat(ingest): add graph client [ING-006]`).
- Push, open PR using `.github/pull_request_template.md` checklist.
- Request Codex/Copilot review; ensure Vercel preview deploys.
- On merge, toggle flag in env + monitor `/api/health` + metrics.

## Local Commands
```bash
# Backend tests (baseline)
cd nextjs-app/backend && python3 -m pytest

# Targeted ANA suites (author first before implementation)
# python3 -m pytest tests/test_x_ingestion.py::test_duplicate_external_id_rejected
# node --run vitest src/tests/analytics-page.test.tsx

# Frontend tests
cd ../ && npm run test

# Coverage (requires pytest-cov / vitest --coverage)
node ../scripts/enforce-coverage.js --summary coverage/coverage-summary.json
```

Keep this file synchronized with the policy repo (`.agent-policy`). EOF
