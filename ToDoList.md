# Amber Development Phased To‑Do List (Authoritative Roadmap)

This document is the SINGLE SOURCE OF TRUTH for all engineering tasks. It MUST be:
- Updated with every meaningful code change (add/change status, dates, notes)
- Followed with strict TDD (write failing test first, see TDD Template below)
- Reflected in commits (reference Task IDs in commit messages, e.g. `feat(ingest): add revision hash [ING-004]`)
- Aligned with agent-policy: atomic tasks, observable outcomes, repeatable verification.

Legend: 
Status Codes = TODO | WIP | BLOCKED | DONE | DEFERRED
Priority = P0 (critical), P1 (high), P2 (normal), P3 (nice-to-have)

---
## 0. TDD TEMPLATE (Apply to every task)
1. Define acceptance criteria (clear measurable result)
2. Write failing test(s) (unit/integration/e2e) referencing Task ID
3. Implement minimal code to pass
4. Run full relevant suite (backend: pytest, frontend: tsc + future jest, e2e: future playwright)
5. Refactor (remove duplication, improve clarity) without changing behavior
6. Update docs: this file + README/PRD if scope changed
7. Commit with Task ID; push
8. (If applicable) Add coverage / log instrumentation

---
## 1. PHASE OVERVIEW
| Phase | Goal | Start | End (Target) | Summary |
|-------|------|-------|--------------|---------|
| P0 | Stabilization & Non-destructive ingestion | DONE | DONE | Hash/revision, pagination, review flow |
| P1 | Observability & Quality Foundation | ACTIVE | TBD | Logging, metrics, sentiment scoring, TDD reinforcement |
| P2 | Analytics & Intelligent Datasets (Phase 2) | PLANNING | 2025-11-15 | Multi-leader analytics, bias mitigation, Genkit chatbot |
| P3 | Localization & UX Polish (Hindi + Language Indicators) | DONE | 2025-10-07 | Date formatting, badges, Hindi surfaces |
| P4 | Social Media API Integration (Meta / Facebook) | DONE | 2025-10-06 | Feature-flagged Graph ingestion, media/avatar persistence |
| P5 | Advanced Review & Moderation + Auth | PENDING |  | Role-based workflow, audit trail |
| P6 | Security & Hardening | PENDING |  | AuthN/Z, rate limiting, secret rotation |
| P7 | Performance & Scaling | PENDING |  | Caching, async ingestion, queue workers |
| P8 | ML / NLP Enhancements | PENDING |  | NER, stance detection, translation pipeline |
| Continuous | CI/CD Maturity | ACTIVE | Ongoing | Coverage gates, SAST, E2E, release tagging |

---
## 2. TASK INDEX (Grouped by Domain)

### 2.1 Ingestion & Content Normalization
| ID | Title | Description | Acceptance Criteria | Tests | Priority | Status | Notes |
|----|-------|-------------|---------------------|-------|----------|--------|-------|
| ING-001 | Non-destructive Post Sync | Preserve existing posts; upsert by link | Existing posts retained; revision increments on hash change | test_posts_pagination + new ingestion revision test | P0 | DONE | Implemented hash + revision |
| ING-002 | Language Tag Propagation | Article language flows into post metrics | metrics.language present for each ingested post | ingestion language unit test | P1 | DONE | Provided via news_sources changes |
| ING-003 | Remove Frontend Fallback | All data via backend API only | No runtime imports of deprecated newsFetcher | grep + boot smoke test | P0 | DONE | Deprecated module throws; Next.js hook now reads /api sources |
| ING-004 | Sentiment Score Storage | Numeric compound in metrics.sentimentScore | Value in [-1,1] & batch API returns score | test_ingest_sentiment_score + batch ordering test | P0 | DONE | Implemented VADER return_score |
| ING-005 | Add Hindi Locale Support | hl/gl/ceid configurable + UI indicator | API returns language meta + UI badge per post | new i18n test + component snapshot | P1 | DONE | Language badge + Hindi formatter wired into PostCard |
| ING-006 | Facebook Graph API Ingestion (Phase 1) | Fetch posts via Graph API for leaders w/ handles | For a test leader, >=1 post stored with origin=graph; avatar + media persisted | tests/test_facebook_ingestion.py | P1 | DONE | Feature-flagged graph ingest with media/avatar + news/sample fallback |
| ING-009 | Expand Leader Catalog & Dashboard Controls | Seed 11 leaders and expose roster with delete action on dashboard | Seeded handles list matches brief; dashboard roster lists leaders with remove control | tests/test_leader_seed.py + src/tests/dashboard.test.tsx + src/components/Dashboard.test.tsx | P1 | DONE | Sample fallback retained; roster reuses API delete flow |
| ING-007 | Async Ingestion Worker | Offload ingestion from request thread | Refresh endpoint enqueues job, returns 202 | queue test (mock) | P2 | TODO | After Graph API |
| ING-008 | Translation Pipeline (Optional) | (If ENABLE_TRANSLATION) store translated content | metrics.translation fields present | translation toggle test | P3 | DEFERRED | Pending clarity |

### 2.2 Review & Moderation
| ID | Title | Description | Acceptance Criteria | Tests | Priority | Status | Notes |
|----|-------|-------------|---------------------|-------|----------|--------|-------|
| REV-001 | Basic Review Queue | Approve/Reject workflow implemented | API approve/reject updates state | test_review_workflow | P0 | DONE | Implemented |
| REV-002 | Reviewer Attribution | Capture reviewer identity | Response includes reviewer + timestamp | add reviewer test | P1 | TODO | Needs auth integration |
| REV-003 | Edit-in-Review | Inline edit + approve | PATCH updates content & marks approved | new edit test | P2 | TODO | |
| REV-004 | Audit Trail | Persist action history | history entries persisted per review item | audit model test | P2 | TODO | |

### 2.3 Observability & Quality
| ID | Title | Description | Acceptance Criteria | Tests | Priority | Status | Notes |
|----|-------|-------------|---------------------|-------|----------|--------|-------|
| OBS-001 | Structured Logging | JSON logs with requestId | request log contains method/path/status | test_request_logging_emits_json | P0 | DONE | Implemented |
| OBS-002 | Ingest Success Event | Emit structured ingest_success | log has leader, articles, durationMs | test_ingest_success_log_emitted | P0 | DONE | |
| OBS-003 | Add Error Event Shape | All exceptions -> error log w/ stack | failing route simulation logs error | error log test | P1 | DONE | Structured handler emits JSON error + pytest coverage |
| OBS-004 | Metrics Endpoint | Exposes ingest + uptime | /api/metrics returns expected keys | test_metrics_endpoint | P0 | DONE | |
| OBS-005 | Coverage Threshold | Enforce >=80% lines backend | pytest fails if <80% | CI run failing below threshold | P1 | TODO | Set once stable |
| OBS-006 | CodeQL Integration | Security static analysis | workflow passes & alerts show in GH | workflow file | P2 | TODO | |

### 2.4 Localization & UI
| ID | Title | Description | Acceptance Criteria | Tests | Priority | Status | Notes |
|----|-------|-------------|---------------------|-------|----------|--------|-------|
| L10N-001 | Hindi Date Formatting | Show dates in Hindi locale style | Example post displays Hindi month/Devanagari numerals | util unit test | P1 | DONE | |
| L10N-002 | Language Badge | Post card shows language chip | Badge rendered for multiple languages | component test | P1 | DONE | Dashboard + PostCard tests cover Hindi + English |
| L10N-003 | Toggle Locale Preference | User toggle hi/en | Setting persisted & reflected | preference test | P2 | TODO | |

### 2.5 Frontend Components & Data UX
| ID | Title | Description | Acceptance Criteria | Tests | Priority | Status | Notes |
|----|-------|-------------|---------------------|-------|----------|--------|-------|
| FE-CORE-001 | Post Sentiment Visualization | Show sentiment score intensity | UI gradient or bar reflects score | DOM test | P1 | TODO | |
| FE-CORE-002 | Infinite Scroll (Stable) | Already implemented; stabilize w/ tests | IntersectionObserver mocked & loads more | observer test | P1 | TODO | Add test |
| FE-CORE-003 | Error Boundary | Catch render errors gracefully | Throwing child replaced by fallback | boundary test | P2 | TODO | |

### 2.6 Security & Auth
| ID | Title | Description | Acceptance Criteria | Tests | Priority | Status | Notes |
|----|-------|-------------|---------------------|-------|----------|--------|-------|
| SEC-001 | Basic Auth Layer | JWT issuance + protected endpoints | Unauthorized returns 401; valid token passes | auth test | P1 | DONE | Tokenized /api/admin/ping with serializer |
| SEC-002 | Role-Based Access | reviewer vs admin | Role restrictions enforced on review actions | role test | P1 | TODO | |
| SEC-003 | Rate Limiting | Per-IP limit on refresh endpoints | Exceed limit returns 429 | rate limit test | P2 | TODO | |
| SEC-004 | Secrets Scan (CI) | Already added (Gitleaks) | CI artifact shows run | present in workflow | P1 | DONE | Non-blocking for now |

### 2.7 Analytics & Intelligent Datasets (Phase 2)
> Mirrors the Project Dhruv reference: a TDD-first Next.js dashboard parsing OP Choudhary’s Sept 1–6 2025 X posts into when/where/what/which/how, rendering Devanagari tables with Noto Sans and enforcing CI gates (coverage ≥85%/≥70%, a11y, perf, security, SBOM, docs). Each ANA task must follow the same red→green→refactor discipline with commit/push+green CI before proceeding.

| ID | Title | Description | Acceptance Criteria | Tests (write failing first) | Priority | Status | Notes |
|----|-------|-------------|---------------------|-----------------------------|----------|--------|-------|
| ANA-001 | Cross-platform Dedup Guard | Enforce unique posts across all sources | Unique constraint + ingestion skip with metrics | `tests/test_x_ingestion.py::test_duplicate_external_id_rejected`, `tests/test_facebook_ingestion.py::test_duplicate_platform_post_id_ignored` | P0 | TODO | Feature gate: `SMART_DATASET_ENABLED` |
| ANA-002 | Parser Snapshot Persistence | Store Dhruv-style parsed summary per post | `Post.metrics.parsed` populated + backfill idempotent | `tests/test_post_parser.py::test_hindi_date_and_entities`, `tests/test_backfill_parsed_posts.py::test_idempotent_backfill` | P0 | TODO | Parser module under `backend/parsers/` |
| ANA-003 | Leader Insights Dataset | Nightly rollups + bias indicators | `/api/analytics/leader/<id>` returns insights & bias flags | `tests/test_leader_insights.py::test_metrics_rollup`, `tests/test_bias_monitor.py::test_skew_alert_triggered` | P0 | TODO | Requires scheduler hook |
| ANA-004 | Smart Dataset Builder | Export per-leader + unified datasets with registry | Dataset files written + metadata recorded | `tests/test_dataset_builder.py::test_generates_per_leader_files`, `tests/test_dataset_registry.py::test_metadata_recorded` | P1 | TODO | Output stored in `analytics/datasets/` |
| ANA-005 | Genkit RAG Pipeline | Google Genkit embeddings + chatbot API | Genkit flow produces answers w/ citations | `genkit/tests/pipeline.test.ts::test_embedding_job_runs`, `tests/test_chatbot_route.py::test_response_contains_sources` | P1 | TODO | Feature flag: `CHATBOT_ENABLED` |
| ANA-006 | Analytics Hub UI | Dhruv-style tables + filters + chatbot widget | Page renders per-leader/all views & interacts with chatbot | `src/tests/analytics-page.test.tsx::renders_filtered_leader_table`, `src/tests/chatbot-widget.test.tsx::submits_query_and_streams_answer` | P1 | TODO | Next.js route `/analytics` |
| ANA-007 | Bias Mitigation & CI Gate | Bias metrics surfaced + enforced in CI | `/api/metrics` exposes bias summary + CI job fails on breach | `tests/test_bias_ci_gate.py::test_pipeline_fails_on_threshold`, `src/tests/analytics-page.test.tsx::shows_bias_banner` | P1 | TODO | Bias threshold configured via env |

### 2.8 Performance & Scaling
| ID | Title | Description | Acceptance Criteria | Tests | Priority | Status | Notes |
|----|-------|-------------|---------------------|-------|----------|--------|-------|
| PERF-001 | Query Index Review | Add indices for timestamp, leader_id | EXPLAIN shows index usage | perf test (timed) | P2 | TODO | |
| PERF-002 | Caching Layer (Read) | In-memory or Redis for /api/dashboard | Cache hit ratio metric | cache test | P2 | TODO | |
| PERF-003 | Async Fetch Batch | Parallel ingestion to reduce latency | Wall time reduced vs baseline | timing test | P3 | TODO | |

### 2.9 E2E & QA Automation
| ID | Title | Description | Acceptance Criteria | Tests | Priority | Status | Notes |
|----|-------|-------------|---------------------|-------|----------|--------|-------|
| E2E-001 | Playwright Bootstrap | Basic smoke: load dashboard & scroll | CI run outputs trace | playwright.yml + test | P1 | TODO | |
| E2E-002 | Review Flow E2E | Approve + Reject scenario | Visual trace & assertions green | playwright test | P1 | TODO | |
| E2E-003 | Leader CRUD E2E | Add/Delete leader persisted | DOM + API state verified | playwright test | P2 | TODO | |

### 2.10 CI/CD Maturity
| ID | Title | Description | Acceptance Criteria | Tests | Priority | Status | Notes |
|----|-------|-------------|---------------------|-------|----------|--------|-------|
| CI-001 | TypeScript Strict Pass | --noEmit passes | `npx tsc --noEmit` zero errors | CI step | P0 | DONE | Added to workflow |
| CI-002 | Backend Coverage Gate | Fail <80% | Pytest exit non-zero below threshold | coverage gate test | P1 | TODO | |
| CI-003 | Frontend Unit Test Setup | Add jest/vitest + sample test | `npm test` runs in CI | workflow addition | P1 | DONE | |
| CI-004 | CodeQL Workflow | CodeQL job visible in Actions | alerts page accessible | workflow test | P2 | TODO | |
| CI-005 | Lint Blocking Mode | Ruff & ESLint as required checks | PR fails on lint errors | PR status | P1 | TODO | |

---
## 3. CURRENT SNAPSHOT
- Phase Active: P1 (Observability & Quality) with Phase 2 (Analytics & Intelligent Datasets) in planning kickoff.
- Highest Priority Upcoming: ANA-001 (dedup guard), ANA-002 (parser snapshot), SEC-002 (role guard).
- Test Coverage: Backend ≥85% (pytest), frontend Vitest suite green; new ANA specs to be authored before implementation.
- Logging: Structured request + ingest success + global error handler emitting JSON payloads; ANA-001 will add dedup counters.

---
## 4. NEXT ACTION QUEUE (Short Horizon)
1. ANA-001 (Implement dedup unique index + ingestion guards, TDD with failing pytest cases).
2. ANA-002 (Author parser module + tests, backfill command).
3. SEC-002 (Role-based access guardrails on review actions).
4. CI-002 (Backend coverage gate enforcement).

---
## 5. CHANGE LOG (Manual Updates)
| Date | Change | Tasks Affected | Author | Notes |
|------|--------|---------------|--------|-------|
| 2025-10-04 | Initial roadmap file created | All | system | Baseline established |
| 2025-10-04 | Frontend tracker now fetches dashboard + leader actions via API | ING-003 | codex | Enables real posts flowing from backend ingest |
| 2025-10-04 | Archived legacy Vite prototype; Next.js app is canonical | CI-003 | codex | Legacy Vite assets moved to archive/vite-app |
| 2025-10-07 | Removed Vite archive to avoid stack confusion | CI-003 | codex | Repository now only contains Next.js implementation |
| 2025-10-04 | Added shared Hindi date formatter for frontend tests | L10N-001 | codex | Util + Vitest spec under src/utils |
| 2025-10-04 | Localized PostCard with Hindi badges & dates | ING-005 | codex | UI now highlights language metadata |
| 2025-10-04 | Began Facebook Graph ingestion implementation | ING-006 | codex | Feature-flagged plan drafted; TDD underway |
| 2025-10-05 | Completed language badge rollout across dashboard | L10N-002 | codex | Vitest covers badges + summary module |
| 2025-10-05 | Added admin JWT skeleton and ping endpoint | SEC-001 | codex | Unauthorized/authorized tests in suite |
| 2025-10-06 | Feature-flagged Graph ingest + expanded leader roster | ING-006, ING-009 | codex | pytest (tests/test_facebook_ingestion.py, tests/test_leader_seed.py) + vitest (src/tests/dashboard.test.tsx) |
| 2025-10-07 | Frontend consumes Graph media/avatar; admin token issuance endpoint; structured error handler | ING-006, SEC-001, OBS-003 | codex | Vitest (`src/components/PostCard.test.tsx`), pytest (`tests/test_auth.py`, `tests/test_observability_and_ingest.py`) |
| 2025-10-13 | Phase 2 analytics & Genkit roadmap documented | ANA-001…ANA-007 | codex | Updated PRD, ToDoList, GEMINI, AGENTS for Phase 2 plan |

---
## 6. MAINTENANCE RULES
- DO NOT remove a task; mark DEFERRED or DONE (preserve history).
- Every new endpoint or model field MUST map to a task row before merge.
- Every commit touching logic MUST reference >=1 Task ID.
- If scope creeps, add a new row BEFORE implementation completion.
- Keep PRD and this list consistent (sync weekly or when major scope changes).

---
## 7. OPEN QUESTIONS
| Question | Blocked Task | Proposed Resolution Deadline |
|----------|--------------|------------------------------|
| Auth provider (custom JWT vs external IdP) | SEC-001 | Before starting SEC-001 |
| Cache technology (Redis vs in-process) | PERF-002 | Prior to implementation |
| Analytics storage (same DB vs warehouse) | ANA-001 | Before Phase P5 |

---
## 8. BACKLOG (Not Yet Prioritized)
- Webhook ingestion adapter framework
- Multi-tenant org boundary (org_id columns)
- Feature flags system
- Post content embeddings & semantic similarity search
- Real-time updates via WebSocket or SSE

---
_End of authoritative task file. Update diligently._
