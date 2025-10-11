# Issue Creation Plan for ToDoList.md Gaps

## Summary
This document outlines all GitHub issues that need to be created based on the ToDoList.md file. Each task marked TODO or with missing metadata requires a dedicated GitHub issue.

## Issues to Create

### Phase 1: Ingestion & Content Normalization (1 issue)

#### ING-007: Async Ingestion Worker
**Title:** ING-007: Async Ingestion Worker
**Labels:** phase:ingestion, area:backend, P2, TODO
**Description:**
Offload ingestion from request thread to improve API responsiveness.

**Acceptance Criteria:**
- Refresh endpoint enqueues job and returns 202 Accepted immediately
- Background worker processes ingestion jobs from queue
- Job status can be queried via API
- Failed jobs are retried with exponential backoff
- Error paths: queue full, worker crash, job timeout
- Edge cases: duplicate job submissions, worker restart during processing

**Test Plan:**
- **Unit Tests:**
  - `test_enqueue_ingestion_job` - Verify job is added to queue
  - `test_worker_processes_job` - Mock worker execution
  - `test_job_retry_logic` - Verify exponential backoff
- **Integration Tests:**
  - `test_end_to_end_async_ingestion` - Full flow from enqueue to completion
  - `test_queue_full_handling` - Verify graceful degradation
- **E2E Tests:**
  - Playwright test for UI showing job status

**Dependencies:**
- After ING-006 (Facebook Graph API Ingestion - DONE)
- May require decision on queue technology (Redis, Celery, etc.)

**Context:** See [ToDoList.md](ToDoList.md#21-ingestion--content-normalization)

---

### Phase 2: Review & Moderation (3 issues)

#### REV-002: Reviewer Attribution
**Title:** REV-002: Reviewer Attribution
**Labels:** phase:review, area:backend, P1, TODO
**Description:**
Capture and persist reviewer identity for all review actions to enable accountability and audit trails.

**Acceptance Criteria:**
- API responses include `reviewer` field with user identifier
- Response includes `reviewed_at` timestamp
- Reviewer identity extracted from auth token
- Historical reviews preserve reviewer information
- Error paths: missing auth, invalid token, anonymous access
- Edge cases: user deletion, role changes during review

**Test Plan:**
- **Unit Tests:**
  - `test_extract_reviewer_from_token` - Parse JWT claims
  - `test_persist_reviewer_attribution` - DB storage
  - `test_anonymous_review_rejected` - Auth enforcement
- **Integration Tests:**
  - `test_review_workflow_with_attribution` - Full approve/reject with reviewer
  - `test_reviewer_query_filters` - Filter reviews by reviewer
- **E2E Tests:**
  - Playwright test verifying reviewer name in UI

**Dependencies:**
- BLOCKED by auth integration (needs SEC-001 completion for token infrastructure)

**Context:** See [ToDoList.md](ToDoList.md#22-review--moderation)

---

#### REV-003: Edit-in-Review
**Title:** REV-003: Edit-in-Review
**Labels:** phase:review, area:backend, P2, TODO
**Description:**
Allow reviewers to edit post content inline during review process before approval.

**Acceptance Criteria:**
- PATCH `/api/review/{id}` updates content fields
- Edited content marked as modified with original preserved
- Approve action after edit persists changes
- Edit history tracked (who, when, what changed)
- Error paths: concurrent edits, invalid content, too large edits
- Edge cases: reverting edits, multiple edit iterations

**Test Plan:**
- **Unit Tests:**
  - `test_patch_review_content` - Update content via PATCH
  - `test_preserve_original_content` - Original saved
  - `test_edit_conflicts` - Concurrent modification handling
- **Integration Tests:**
  - `test_edit_and_approve_flow` - Full workflow
  - `test_edit_history_persistence` - Audit trail verification
- **E2E Tests:**
  - Playwright test for inline editing in review UI

**Dependencies:**
- None (can be implemented independently)

**Context:** See [ToDoList.md](ToDoList.md#22-review--moderation)

---

#### REV-004: Audit Trail
**Title:** REV-004: Audit Trail
**Labels:** phase:review, area:backend, P2, TODO
**Description:**
Persist complete action history for all review items to enable forensics and compliance.

**Acceptance Criteria:**
- All review actions stored in `audit_log` table
- Each entry includes: action type, timestamp, user, before/after state
- API endpoint `/api/audit/{review_id}` returns history
- Retention policy configurable (default 2 years)
- Error paths: storage failure, query timeout
- Edge cases: bulk actions, system-initiated changes

**Test Plan:**
- **Unit Tests:**
  - `test_audit_entry_creation` - Record action
  - `test_audit_query` - Retrieve history
  - `test_audit_retention_policy` - Cleanup old entries
- **Integration Tests:**
  - `test_full_review_audit_trail` - Multiple actions recorded
  - `test_concurrent_audit_writes` - Thread safety
- **E2E Tests:**
  - Playwright test viewing audit log in UI

**Dependencies:**
- REV-002 (Reviewer Attribution) for complete context

**Context:** See [ToDoList.md](ToDoList.md#22-review--moderation)

---

### Phase 3: Observability & Quality (2 issues)

#### OBS-005: Coverage Threshold
**Title:** OBS-005: Coverage Threshold  
**Labels:** phase:observability, area:backend, P1, TODO
**Description:**
Enforce minimum 80% line coverage threshold in CI to maintain code quality.

**Acceptance Criteria:**
- Pytest fails if coverage drops below 80% lines
- CI job reports coverage percentage
- Coverage report uploaded as artifact
- Exclusions documented (.coveragerc)
- Error paths: coverage tool failure
- Edge cases: new uncovered code, flaky tests

**Test Plan:**
- **Unit Tests:**
  - `test_coverage_calculation` - Verify math
  - `test_threshold_enforcement` - Simulate below threshold
- **Integration Tests:**
  - `test_ci_coverage_gate` - Mock CI run with low coverage
  - `test_coverage_report_generation` - Artifact creation
- **E2E Tests:**
  - Manual CI run verification

**Dependencies:**
- Set once test suite is stable (current coverage must be measured first)

**Context:** See [ToDoList.md](ToDoList.md#23-observability--quality)

---

#### OBS-006: CodeQL Integration
**Title:** OBS-006: CodeQL Integration
**Labels:** phase:observability, area:ci, P2, TODO
**Description:**
Integrate GitHub CodeQL for automated security static analysis.

**Acceptance Criteria:**
- CodeQL workflow file `.github/workflows/codeql.yml` present
- Workflow runs on push and PR
- Security alerts visible in GitHub Security tab
- CodeQL scans Python and JavaScript/TypeScript
- Error paths: scan timeout, false positives
- Edge cases: new vulnerability types, config updates

**Test Plan:**
- **Unit Tests:**
  - N/A (infrastructure)
- **Integration Tests:**
  - `test_codeql_workflow_syntax` - YAML validation
- **E2E Tests:**
  - Manual workflow trigger and results inspection

**Dependencies:**
- None (can be added independently)

**Context:** See [ToDoList.md](ToDoList.md#23-observability--quality)

---

### Phase 4: Localization & UI (1 issue)

#### L10N-003: Toggle Locale Preference
**Title:** L10N-003: Toggle Locale Preference
**Labels:** phase:localization, area:frontend, P2, TODO
**Description:**
Allow users to toggle between Hindi and English locales with preference persistence.

**Acceptance Criteria:**
- UI toggle button in header/settings
- Setting persisted to localStorage or user profile
- All dates, badges, and text respect locale
- Default to browser language if available
- Error paths: storage failure, invalid locale
- Edge cases: mid-session change, no storage available

**Test Plan:**
- **Unit Tests:**
  - `test_locale_toggle_state` - Toggle logic
  - `test_locale_persistence` - Storage operations
  - `test_locale_fallback` - Default behavior
- **Integration Tests:**
  - `test_locale_affects_all_components` - System-wide application
- **E2E Tests:**
  - Playwright test toggling locale and verifying UI updates

**Dependencies:**
- L10N-001 (Hindi Date Formatting - DONE)
- L10N-002 (Language Badge - DONE)

**Context:** See [ToDoList.md](ToDoList.md#24-localization--ui)

---

### Phase 5: Frontend Components & Data UX (3 issues)

#### FE-CORE-001: Post Sentiment Visualization
**Title:** FE-CORE-001: Post Sentiment Visualization
**Labels:** phase:frontend, area:frontend, P1, TODO
**Description:**
Visualize sentiment score intensity using gradients or bars in post cards.

**Acceptance Criteria:**
- Sentiment score displayed visually (bar, gradient, or icon)
- Color coding: green (positive), gray (neutral), red (negative)
- Intensity reflects score magnitude [-1, 1]
- Accessible (ARIA labels, keyboard navigation)
- Error paths: missing score, invalid score
- Edge cases: score exactly 0, extreme values

**Test Plan:**
- **Unit Tests:**
  - `test_sentiment_color_mapping` - Score to color logic
  - `test_sentiment_bar_width` - Visual calculations
  - `test_accessibility_attributes` - ARIA labels present
- **Integration Tests:**
  - `test_sentiment_in_post_card` - Component rendering
- **E2E Tests:**
  - Playwright visual regression test for sentiment display

**Dependencies:**
- ING-004 (Sentiment Score Storage - DONE)

**Context:** See [ToDoList.md](ToDoList.md#25-frontend-components--data-ux)

---

#### FE-CORE-002: Infinite Scroll (Stable)
**Title:** FE-CORE-002: Infinite Scroll (Stable)
**Labels:** phase:frontend, area:frontend, P1, TODO
**Description:**
Stabilize existing infinite scroll implementation with comprehensive test coverage.

**Acceptance Criteria:**
- IntersectionObserver properly mocked in tests
- Scroll triggers load more posts
- Loading state displayed during fetch
- No duplicate posts loaded
- Error paths: fetch failure, empty next page
- Edge cases: rapid scrolling, network flakiness

**Test Plan:**
- **Unit Tests:**
  - `test_intersection_observer_mock` - Observer setup
  - `test_load_more_trigger` - Scroll detection
  - `test_deduplicate_posts` - Prevent duplicates
- **Integration Tests:**
  - `test_infinite_scroll_flow` - Full scroll interaction
  - `test_scroll_error_handling` - Network failure recovery
- **E2E Tests:**
  - Playwright test scrolling through multiple pages

**Dependencies:**
- None (already implemented, needs tests)

**Context:** See [ToDoList.md](ToDoList.md#25-frontend-components--data-ux)

---

#### FE-CORE-003: Error Boundary
**Title:** FE-CORE-003: Error Boundary
**Labels:** phase:frontend, area:frontend, P2, TODO
**Description:**
Implement React Error Boundary to gracefully handle component render errors.

**Acceptance Criteria:**
- Error boundary wraps critical components
- Fallback UI displays user-friendly message
- Errors logged to observability system
- Boundary doesn't catch event handler errors
- Error paths: nested boundaries, repeated errors
- Edge cases: error during fallback render

**Test Plan:**
- **Unit Tests:**
  - `test_error_boundary_catches_error` - Error caught
  - `test_fallback_ui_rendered` - Fallback display
  - `test_error_logged` - Logging integration
- **Integration Tests:**
  - `test_throwing_component` - Component that throws
  - `test_boundary_reset` - Recovery mechanism
- **E2E Tests:**
  - Playwright test triggering error and verifying fallback

**Dependencies:**
- OBS-003 (Error logging infrastructure - DONE)

**Context:** See [ToDoList.md](ToDoList.md#25-frontend-components--data-ux)

---

### Phase 6: Security & Auth (2 issues)

#### SEC-002: Role-Based Access
**Title:** SEC-002: Role-Based Access
**Labels:** phase:security, area:backend, P1, TODO
**Description:**
Implement role-based access control distinguishing reviewer and admin roles.

**Acceptance Criteria:**
- Roles stored in user model: `reviewer`, `admin`
- Role restrictions enforced on review endpoints
- Admins can perform all actions, reviewers limited
- Role checked on every protected endpoint
- Error paths: missing role, invalid role, privilege escalation attempt
- Edge cases: role changes mid-session, multiple roles

**Test Plan:**
- **Unit Tests:**
  - `test_role_extraction` - Parse role from token
  - `test_role_authorization` - Permission checking
  - `test_unauthorized_role_access` - Rejection
- **Integration Tests:**
  - `test_reviewer_limited_access` - Reviewer can't admin
  - `test_admin_full_access` - Admin can do everything
- **E2E Tests:**
  - Playwright test with different role logins

**Dependencies:**
- SEC-001 (Basic Auth Layer - DONE)

**Context:** See [ToDoList.md](ToDoList.md#26-security--auth)

---

#### SEC-003: Rate Limiting
**Title:** SEC-003: Rate Limiting
**Labels:** phase:security, area:backend, P2, TODO
**Description:**
Implement per-IP rate limiting on refresh and ingestion endpoints to prevent abuse.

**Acceptance Criteria:**
- Rate limit: 10 requests per minute per IP on `/api/refresh`
- Exceed limit returns 429 Too Many Requests
- Rate limit info in response headers (X-RateLimit-*)
- Different limits for authenticated vs anonymous
- Error paths: Redis unavailable, IP spoofing
- Edge cases: distributed IPs, legitimate bursts

**Test Plan:**
- **Unit Tests:**
  - `test_rate_limit_counter` - Counting logic
  - `test_rate_limit_exceeded` - 429 response
  - `test_rate_limit_reset` - Window expiration
- **Integration Tests:**
  - `test_rapid_requests` - Send 11 requests quickly
  - `test_authenticated_higher_limit` - Different limits by auth
- **E2E Tests:**
  - Manual load testing with rate limit verification

**Dependencies:**
- May require Redis decision for distributed rate limiting

**Context:** See [ToDoList.md](ToDoList.md#26-security--auth)

---

### Phase 7: Analytics & Derived Metrics (3 issues)

#### ANA-001: Sentiment Trend Rollups
**Title:** ANA-001: Sentiment Trend Rollups
**Labels:** phase:analytics, area:backend, P2, TODO
**Description:**
Aggregate daily sentiment scores per leader for trend analysis.

**Acceptance Criteria:**
- `/api/analytics/sentiment` returns day buckets
- Each bucket: date, leader_id, avg_sentiment, post_count
- Data cached/materialized for performance
- Supports date range filtering
- Error paths: no data for range, invalid date format
- Edge cases: timezone handling, partial days

**Test Plan:**
- **Unit Tests:**
  - `test_daily_aggregation` - Grouping logic
  - `test_sentiment_average_calculation` - Math correctness
  - `test_date_range_filtering` - Query filtering
- **Integration Tests:**
  - `test_analytics_endpoint` - Full API response
  - `test_aggregation_performance` - Query speed
- **E2E Tests:**
  - Playwright test viewing sentiment trends in UI

**Dependencies:**
- BLOCKED by analytics storage decision (same DB vs warehouse)

**Context:** See [ToDoList.md](ToDoList.md#27-analytics--derived-metrics)

---

#### ANA-002: Post Velocity Metric
**Title:** ANA-002: Post Velocity Metric
**Labels:** phase:analytics, area:backend, P2, TODO
**Description:**
Calculate posts per leader over 7-day rolling window to track activity levels.

**Acceptance Criteria:**
- Metric: `posts_per_7d` per leader
- API endpoint `/api/analytics/velocity` returns values
- Rolling window updates daily
- Historical velocity tracked
- Error paths: insufficient data, date gaps
- Edge cases: new leaders, deleted posts

**Test Plan:**
- **Unit Tests:**
  - `test_rolling_window_calculation` - 7-day logic
  - `test_velocity_with_gaps` - Missing data handling
  - `test_new_leader_velocity` - Bootstrap case
- **Integration Tests:**
  - `test_velocity_endpoint` - Full API response
  - `test_velocity_time_series` - Historical data
- **E2E Tests:**
  - Playwright test viewing velocity charts

**Dependencies:**
- None (can use existing post data)

**Context:** See [ToDoList.md](ToDoList.md#27-analytics--derived-metrics)

---

#### ANA-003: Revision Change Count
**Title:** ANA-003: Revision Change Count
**Labels:** phase:analytics, area:backend, P2, TODO
**Description:**
Count content revisions per leader to track content volatility.

**Acceptance Criteria:**
- Endpoint `/api/analytics/revisions` exposes counts
- Metric: total revisions per leader
- Includes revision timestamps
- Supports filtering by date range
- Error paths: missing revision data, corrupt hashes
- Edge cases: mass revisions, reverted changes

**Test Plan:**
- **Unit Tests:**
  - `test_revision_counting` - Aggregation logic
  - `test_revision_filtering` - Date range
  - `test_no_revisions_case` - Zero revisions handling
- **Integration Tests:**
  - `test_revisions_endpoint` - Full API response
  - `test_revision_consistency` - Data integrity
- **E2E Tests:**
  - Playwright test viewing revision metrics

**Dependencies:**
- ING-001 (revision tracking - DONE)

**Context:** See [ToDoList.md](ToDoList.md#27-analytics--derived-metrics)

---

### Phase 8: Performance & Scaling (3 issues)

#### PERF-001: Query Index Review
**Title:** PERF-001: Query Index Review
**Labels:** phase:performance, area:backend, P2, TODO
**Description:**
Add database indices on frequently queried columns to optimize performance.

**Acceptance Criteria:**
- Indices added on: `timestamp`, `leader_id`, `status`
- EXPLAIN plans show index usage
- Query performance improved (measure with timing tests)
- No negative impact on write performance
- Error paths: index corruption, lock timeout during creation
- Edge cases: large table migration, composite indices

**Test Plan:**
- **Unit Tests:**
  - `test_query_uses_index` - EXPLAIN analysis
  - `test_index_selectivity` - Effectiveness measurement
- **Integration Tests:**
  - `test_query_performance` - Before/after timing
  - `test_write_performance_maintained` - No degradation
- **E2E Tests:**
  - Manual load testing with profiling

**Dependencies:**
- None (can be added anytime, recommend after data volume grows)

**Context:** See [ToDoList.md](ToDoList.md#28-performance--scaling)

---

#### PERF-002: Caching Layer (Read)
**Title:** PERF-002: Caching Layer (Read)
**Labels:** phase:performance, area:backend, P2, TODO
**Description:**
Implement caching layer (in-memory or Redis) for dashboard reads.

**Acceptance Criteria:**
- `/api/dashboard` responses cached
- Cache hit ratio metric exposed
- TTL configurable (default 5 minutes)
- Cache invalidation on data updates
- Error paths: cache unavailable, stale data
- Edge cases: cache stampede, partial updates

**Test Plan:**
- **Unit Tests:**
  - `test_cache_hit` - Verify cached response
  - `test_cache_miss` - Verify fetch and store
  - `test_cache_invalidation` - Update clears cache
- **Integration Tests:**
  - `test_cache_hit_ratio` - Metric calculation
  - `test_cache_fallback` - Redis down scenario
- **E2E Tests:**
  - Manual load testing with cache profiling

**Dependencies:**
- BLOCKED by cache technology decision (Redis vs in-process)

**Context:** See [ToDoList.md](ToDoList.md#28-performance--scaling)

---

#### PERF-003: Async Fetch Batch
**Title:** PERF-003: Async Fetch Batch
**Labels:** phase:performance, area:backend, P3, TODO
**Description:**
Parallelize ingestion fetches to reduce wall-clock time.

**Acceptance Criteria:**
- Multiple leader fetches run concurrently
- Wall time reduced vs sequential baseline
- Configurable concurrency limit (default 5)
- Error handling doesn't block other fetches
- Error paths: partial failures, timeout one source
- Edge cases: too many concurrent requests, rate limit hit

**Test Plan:**
- **Unit Tests:**
  - `test_concurrent_fetch` - Parallel execution
  - `test_partial_failure_handling` - Some succeed, some fail
  - `test_concurrency_limit` - Max concurrent respected
- **Integration Tests:**
  - `test_wall_time_reduction` - Timing comparison
  - `test_error_isolation` - One failure doesn't stop others
- **E2E Tests:**
  - Manual timing tests with real API calls

**Dependencies:**
- ING-006 (Graph API ingestion - DONE)

**Context:** See [ToDoList.md](ToDoList.md#28-performance--scaling)

---

### Phase 9: E2E & QA Automation (3 issues)

#### E2E-001: Playwright Bootstrap
**Title:** E2E-001: Playwright Bootstrap
**Labels:** phase:e2e, area:qa, P1, TODO
**Description:**
Set up Playwright for end-to-end testing with basic smoke test.

**Acceptance Criteria:**
- `playwright.yml` workflow in CI
- Smoke test: load dashboard and scroll
- CI run outputs trace artifact
- Tests run on PR and main push
- Error paths: browser crash, network timeout
- Edge cases: flaky tests, screenshot diffs

**Test Plan:**
- **Unit Tests:**
  - N/A (infrastructure)
- **Integration Tests:**
  - `test_playwright_config` - Config validation
- **E2E Tests:**
  - `smoke.spec.ts` - Load dashboard, verify title, scroll

**Dependencies:**
- None (can be added independently)

**Context:** See [ToDoList.md](ToDoList.md#29-e2e--qa-automation)

---

#### E2E-002: Review Flow E2E
**Title:** E2E-002: Review Flow E2E
**Labels:** phase:e2e, area:qa, P1, TODO
**Description:**
Playwright test covering approve and reject review workflows.

**Acceptance Criteria:**
- Test scenario: login, navigate to review queue, approve/reject post
- Visual trace captured
- Assertions on UI state and API responses
- Tests both approval and rejection paths
- Error paths: network failure during action
- Edge cases: concurrent reviews, stale data

**Test Plan:**
- **Unit Tests:**
  - N/A (E2E test)
- **Integration Tests:**
  - N/A (E2E test)
- **E2E Tests:**
  - `review-flow.spec.ts` - Full approve/reject scenarios

**Dependencies:**
- E2E-001 (Playwright bootstrap)
- REV-001 (Review workflow - DONE)

**Context:** See [ToDoList.md](ToDoList.md#29-e2e--qa-automation)

---

#### E2E-003: Leader CRUD E2E
**Title:** E2E-003: Leader CRUD E2E
**Labels:** phase:e2e, area:qa, P2, TODO
**Description:**
Playwright test for adding and deleting leaders with persistence verification.

**Acceptance Criteria:**
- Test scenario: add new leader, verify in list, delete, verify removed
- Both DOM and API state verified
- Tests handle async operations correctly
- Error paths: duplicate leader, invalid handle
- Edge cases: rapid add/delete, concurrent modifications

**Test Plan:**
- **Unit Tests:**
  - N/A (E2E test)
- **Integration Tests:**
  - N/A (E2E test)
- **E2E Tests:**
  - `leader-crud.spec.ts` - Full CRUD lifecycle

**Dependencies:**
- E2E-001 (Playwright bootstrap)
- ING-009 (Leader dashboard - DONE)

**Context:** See [ToDoList.md](ToDoList.md#29-e2e--qa-automation)

---

### Phase 10: CI/CD Maturity (3 issues)

#### CI-002: Backend Coverage Gate
**Title:** CI-002: Backend Coverage Gate
**Labels:** phase:ci, area:backend, P1, TODO
**Description:**
Fail CI if backend test coverage drops below 80% threshold.

**Acceptance Criteria:**
- Pytest exits non-zero if coverage <80%
- Coverage report visible in CI logs
- Badge in README shows coverage percentage
- Exclusions documented in `.coveragerc`
- Error paths: coverage tool malfunction
- Edge cases: new code without tests, flaky coverage calculation

**Test Plan:**
- **Unit Tests:**
  - `test_coverage_threshold_check` - Verify exit code logic
- **Integration Tests:**
  - `test_ci_fails_low_coverage` - Simulate <80% scenario
- **E2E Tests:**
  - Manual CI run with intentionally low coverage

**Dependencies:**
- OBS-005 (Coverage threshold - prerequisite for implementation)

**Context:** See [ToDoList.md](ToDoList.md#210-cicd-maturity)

---

#### CI-004: CodeQL Workflow
**Title:** CI-004: CodeQL Workflow
**Labels:** phase:ci, area:security, P2, TODO
**Description:**
Add CodeQL static analysis workflow for automated security scanning.

**Acceptance Criteria:**
- `.github/workflows/codeql.yml` present and runs
- Alerts visible in GitHub Security tab
- Scans Python and JavaScript/TypeScript code
- Runs on push and PR
- Error paths: scan timeout, config errors
- Edge cases: false positives, new query packs

**Test Plan:**
- **Unit Tests:**
  - N/A (infrastructure)
- **Integration Tests:**
  - `test_codeql_workflow_syntax` - Validate YAML
- **E2E Tests:**
  - Manual trigger and verify results in Security tab

**Dependencies:**
- OBS-006 (CodeQL Integration - same task)

**Context:** See [ToDoList.md](ToDoList.md#210-cicd-maturity)

---

#### CI-005: Lint Blocking Mode
**Title:** CI-005: Lint Blocking Mode
**Labels:** phase:ci, area:quality, P1, TODO
**Description:**
Make Ruff and ESLint required CI checks that block PR merges on violations.

**Acceptance Criteria:**
- PR fails if `ruff check .` has violations
- PR fails if `npm run lint` has errors
- Status checks required in branch protection
- Lint errors clearly reported in CI logs
- Error paths: linter crash, config errors
- Edge cases: auto-fixable issues, ignore patterns

**Test Plan:**
- **Unit Tests:**
  - N/A (infrastructure)
- **Integration Tests:**
  - `test_lint_failure_blocks_pr` - Verify PR status
- **E2E Tests:**
  - Manual PR with lint violations to verify blocking

**Dependencies:**
- None (linters already present, just needs enforcement)

**Context:** See [ToDoList.md](ToDoList.md#210-cicd-maturity)

---

## Open Questions (3 issues)

### QUESTION: Auth Provider Decision
**Title:** QUESTION: Auth provider (custom JWT vs external IdP)
**Labels:** question, help wanted, blocked, phase:security
**Description:**
Need to decide between implementing custom JWT-based authentication or integrating an external Identity Provider (IdP) like Auth0, Okta, or Firebase Auth.

**Considerations:**
- **Custom JWT:**
  - Pros: Full control, no external dependencies, simpler initial setup
  - Cons: Security responsibility, need to implement refresh tokens, password reset, 2FA
- **External IdP:**
  - Pros: Battle-tested security, built-in features (2FA, social login), reduced maintenance
  - Cons: External dependency, cost, vendor lock-in, integration complexity

**Decision Needed By:** Before starting SEC-001 implementation

**Blocked Tasks:** SEC-001 (partially blocked - basic JWT already implemented), SEC-002, REV-002

**Discussion Points:**
1. What are the security requirements for this application?
2. What is the expected user base size?
3. Do we need social login or enterprise SSO?
4. What is the budget for authentication services?
5. What is the team's expertise in security?

**Context:** See [ToDoList.md](ToDoList.md#7-open-questions)

---

### QUESTION: Cache Technology Decision
**Title:** QUESTION: Cache technology (Redis vs in-process)
**Labels:** question, help wanted, blocked, phase:performance
**Description:**
Need to decide on caching technology for the read caching layer.

**Considerations:**
- **Redis (External):**
  - Pros: Distributed, shared across instances, persistence options, rich data structures
  - Cons: External dependency, deployment complexity, network latency, cost
- **In-Process (e.g., Node cache, Python lru_cache):**
  - Pros: Zero latency, no external deps, simple setup, no cost
  - Cons: Not shared across instances, lost on restart, memory limited per instance

**Decision Needed By:** Prior to PERF-002 implementation

**Blocked Tasks:** PERF-002 (Caching Layer), potentially SEC-003 (Rate Limiting)

**Discussion Points:**
1. Will the application run on multiple instances (horizontal scaling)?
2. What is the cache hit ratio requirement?
3. What is the acceptable cache staleness window?
4. What is the deployment environment (cloud, on-prem)?
5. What is the budget for caching infrastructure?

**Recommendation:** If planning to scale horizontally, use Redis. If single-instance or cost-sensitive, start with in-process and migrate later.

**Context:** See [ToDoList.md](ToDoList.md#7-open-questions)

---

### QUESTION: Analytics Storage Decision
**Title:** QUESTION: Analytics storage (same DB vs warehouse)
**Labels:** question, help wanted, blocked, phase:analytics
**Description:**
Need to decide where to store analytics data and aggregations.

**Considerations:**
- **Same Database (PostgreSQL/MySQL):**
  - Pros: Simple, no data sync, single source of truth
  - Cons: Performance impact on OLTP, limited analytics features, query complexity
- **Data Warehouse (BigQuery, Redshift, Snowflake):**
  - Pros: Optimized for analytics, scalable, advanced features (window functions, columnar storage)
  - Cons: Data pipeline needed, sync lag, cost, operational complexity

**Decision Needed By:** Before Phase P5 (Analytics Layer implementation)

**Blocked Tasks:** ANA-001 (Sentiment Trend Rollups), ANA-002 (Post Velocity Metric), ANA-003 (Revision Change Count)

**Discussion Points:**
1. What is the expected data volume and query complexity?
2. What are the analytics latency requirements (real-time vs batch)?
3. Who will consume the analytics (internal tools vs user-facing dashboards)?
4. What is the budget for data infrastructure?
5. What is the team's expertise in data engineering?

**Recommendation:** Start with same DB using materialized views for aggregations. Migrate to warehouse if query performance becomes an issue (typically > 100M rows).

**Context:** See [ToDoList.md](ToDoList.md#7-open-questions)

---

## Summary Statistics

**Total Issues to Create:** 27

**By Phase:**
- Ingestion: 1 issue
- Review & Moderation: 3 issues
- Observability & Quality: 2 issues
- Localization & UI: 1 issue
- Frontend Components: 3 issues
- Security & Auth: 2 issues
- Analytics: 3 issues (BLOCKED)
- Performance & Scaling: 3 issues (1 BLOCKED)
- E2E & QA: 3 issues
- CI/CD Maturity: 3 issues
- Open Questions: 3 issues

**By Priority:**
- P1 (High): 11 issues
- P2 (Normal): 15 issues
- P3 (Nice-to-have): 1 issue
- Questions: 3 issues

**By Status:**
- TODO: 24 issues
- Questions (BLOCKED): 3 issues

**Reference:** [ToDoList.md](ToDoList.md)
