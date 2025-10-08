# Ironclad DevOps Rulebook v2.1 — It Just Works

This repo hosts policy-as-code for atomic, TDD-first, shift-left security & observability.
- **Policy**: `devops_agent_policy.yaml`
- **Cursor rules**: `.cursorrules`
- **Prompts**: `gemini.md`, `agent.md`
- **CI**: `.github/workflows/ironclad.yml`
- **Scripts**: `scripts/enforce-coverage.js`, `scripts/assert-k6-p95.js`
- **PR template**: `.github/pull_request_template.md`

## Quick Start
1. Mark CI jobs as **required** in branch protection.
2. Use **feature flags** and **canary** for risky changes.
3. Keep tasks **1–4h**, TDD **red→green→refactor**, and **update docs**.
4. Budgets: Web LCP ≤ 2.5s, API p95 ≤ 300ms, Mobile 60fps (<1% jank).

*Ethos: build brick by brick, test by test, commit by commit—software that just works.*
