#!/bin/bash
# GitHub Issue Creation Script for Amber Roadmap Gaps
# This script creates 29 issues based on ToDoList.md analysis
# Requires: gh CLI (GitHub CLI) to be installed and authenticated

set -e

REPO="Kodanda10/Amber"
TODOLIST_URL="https://github.com/Kodanda10/Amber/blob/roadmap/fill-gaps/ToDoList.md"

echo "🚀 Creating 29 GitHub issues for Amber Roadmap Gaps..."
echo "Repository: $REPO"
echo ""

# Function to create an issue
create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"
    
    echo "Creating issue: $title"
    gh issue create \
        --repo "$REPO" \
        --title "$title" \
        --body "$body" \
        --label "$labels"
    echo "✓ Created"
    echo ""
}

# ============================================================================
# PHASE 1: INGESTION (1 issue)
# ============================================================================

create_issue \
    "ING-007: Async Ingestion Worker" \
    "Offload ingestion from request thread to improve API responsiveness.

**Acceptance Criteria:**
- Refresh endpoint enqueues job and returns 202 Accepted immediately
- Background worker processes ingestion jobs from queue
- Job status can be queried via API
- Failed jobs are retried with exponential backoff
- **Error paths:** queue full, worker crash, job timeout
- **Edge cases:** duplicate job submissions, worker restart during processing

**Test Plan:**
- **Unit Tests:**
  - \`test_enqueue_ingestion_job\` - Verify job is added to queue
  - \`test_worker_processes_job\` - Mock worker execution
  - \`test_job_retry_logic\` - Verify exponential backoff
- **Integration Tests:**
  - \`test_end_to_end_async_ingestion\` - Full flow from enqueue to completion
  - \`test_queue_full_handling\` - Verify graceful degradation
- **E2E Tests:**
  - Playwright test for UI showing job status

**Dependencies:**
- After ING-006 (Facebook Graph API Ingestion - DONE)

**Context:** See [ToDoList.md]($TODOLIST_URL#21-ingestion--content-normalization)" \
    "phase:ingestion,area:backend,P2,TODO"

# ============================================================================
# PHASE 2: REVIEW & MODERATION (3 issues)
# ============================================================================

create_issue \
    "REV-002: Reviewer Attribution" \
    "Capture and persist reviewer identity for all review actions.

**Acceptance Criteria:**
- API responses include \`reviewer\` field with user identifier
- Response includes \`reviewed_at\` timestamp
- Reviewer identity extracted from auth token
- Historical reviews preserve reviewer information
- **Error paths:** missing auth, invalid token, anonymous access
- **Edge cases:** user deletion, role changes during review

**Test Plan:**
- **Unit Tests:**
  - \`test_extract_reviewer_from_token\` - Parse JWT claims
  - \`test_persist_reviewer_attribution\` - DB storage
  - \`test_anonymous_review_rejected\` - Auth enforcement
- **Integration Tests:**
  - \`test_review_workflow_with_attribution\` - Full approve/reject with reviewer
  - \`test_reviewer_query_filters\` - Filter reviews by reviewer
- **E2E Tests:**
  - Playwright test verifying reviewer name in UI

**Dependencies:**
- ⚠️ **BLOCKED:** Needs auth integration (SEC-001 completion)

**Context:** See [ToDoList.md]($TODOLIST_URL#22-review--moderation)" \
    "phase:review,area:backend,P1,TODO,blocked"

create_issue \
    "REV-003: Edit-in-Review" \
    "Allow reviewers to edit post content inline during review process.

**Acceptance Criteria:**
- PATCH \`/api/review/{id}\` updates content fields
- Edited content marked as modified with original preserved
- Approve action after edit persists changes
- Edit history tracked (who, when, what changed)
- **Error paths:** concurrent edits, invalid content, too large edits
- **Edge cases:** reverting edits, multiple edit iterations

**Test Plan:**
- **Unit Tests:**
  - \`test_patch_review_content\` - Update content via PATCH
  - \`test_preserve_original_content\` - Original saved
  - \`test_edit_conflicts\` - Concurrent modification handling
- **Integration Tests:**
  - \`test_edit_and_approve_flow\` - Full workflow
  - \`test_edit_history_persistence\` - Audit trail verification
- **E2E Tests:**
  - Playwright test for inline editing in review UI

**Context:** See [ToDoList.md]($TODOLIST_URL#22-review--moderation)" \
    "phase:review,area:backend,P2,TODO"

create_issue \
    "REV-004: Audit Trail" \
    "Persist complete action history for all review items.

**Acceptance Criteria:**
- All review actions stored in \`audit_log\` table
- Each entry includes: action type, timestamp, user, before/after state
- API endpoint \`/api/audit/{review_id}\` returns history
- Retention policy configurable (default 2 years)
- **Error paths:** storage failure, query timeout
- **Edge cases:** bulk actions, system-initiated changes

**Test Plan:**
- **Unit Tests:**
  - \`test_audit_entry_creation\` - Record action
  - \`test_audit_query\` - Retrieve history
  - \`test_audit_retention_policy\` - Cleanup old entries
- **Integration Tests:**
  - \`test_full_review_audit_trail\` - Multiple actions recorded
  - \`test_concurrent_audit_writes\` - Thread safety
- **E2E Tests:**
  - Playwright test viewing audit log in UI

**Dependencies:**
- REV-002 (Reviewer Attribution) for complete context

**Context:** See [ToDoList.md]($TODOLIST_URL#22-review--moderation)" \
    "phase:review,area:backend,P2,TODO"

# ============================================================================
# PHASE 3: OBSERVABILITY (2 issues)
# ============================================================================

create_issue \
    "OBS-005: Coverage Threshold" \
    "Enforce minimum 80% line coverage threshold in CI.

**Acceptance Criteria:**
- Pytest fails if coverage drops below 80% lines
- CI job reports coverage percentage
- Coverage report uploaded as artifact
- Exclusions documented (.coveragerc)
- **Error paths:** coverage tool failure
- **Edge cases:** new uncovered code, flaky tests

**Test Plan:**
- **Unit Tests:**
  - \`test_coverage_calculation\` - Verify math
  - \`test_threshold_enforcement\` - Simulate below threshold
- **Integration Tests:**
  - \`test_ci_coverage_gate\` - Mock CI run with low coverage
  - \`test_coverage_report_generation\` - Artifact creation

**Dependencies:**
- Set once test suite is stable

**Context:** See [ToDoList.md]($TODOLIST_URL#23-observability--quality)" \
    "phase:observability,area:backend,P1,TODO"

create_issue \
    "OBS-006: CodeQL Integration" \
    "Integrate GitHub CodeQL for automated security static analysis.

**Acceptance Criteria:**
- CodeQL workflow file \`.github/workflows/codeql.yml\` present
- Workflow runs on push and PR
- Security alerts visible in GitHub Security tab
- CodeQL scans Python and JavaScript/TypeScript
- **Error paths:** scan timeout, false positives
- **Edge cases:** new vulnerability types, config updates

**Test Plan:**
- **Integration Tests:**
  - \`test_codeql_workflow_syntax\` - YAML validation
- **E2E Tests:**
  - Manual workflow trigger and results inspection

**Context:** See [ToDoList.md]($TODOLIST_URL#23-observability--quality)" \
    "phase:observability,area:ci,P2,TODO"

# ============================================================================
# PHASE 4: LOCALIZATION (1 issue)
# ============================================================================

create_issue \
    "L10N-003: Toggle Locale Preference" \
    "Allow users to toggle between Hindi and English locales.

**Acceptance Criteria:**
- UI toggle button in header/settings
- Setting persisted to localStorage or user profile
- All dates, badges, and text respect locale
- Default to browser language if available
- **Error paths:** storage failure, invalid locale
- **Edge cases:** mid-session change, no storage available

**Test Plan:**
- **Unit Tests:**
  - \`test_locale_toggle_state\` - Toggle logic
  - \`test_locale_persistence\` - Storage operations
  - \`test_locale_fallback\` - Default behavior
- **Integration Tests:**
  - \`test_locale_affects_all_components\` - System-wide application
- **E2E Tests:**
  - Playwright test toggling locale and verifying UI updates

**Dependencies:**
- L10N-001 (DONE), L10N-002 (DONE)

**Context:** See [ToDoList.md]($TODOLIST_URL#24-localization--ui)" \
    "phase:localization,area:frontend,P2,TODO"

# ============================================================================
# PHASE 5: FRONTEND (3 issues)
# ============================================================================

create_issue \
    "FE-CORE-001: Post Sentiment Visualization" \
    "Visualize sentiment score intensity in post cards.

**Acceptance Criteria:**
- Sentiment score displayed visually (bar, gradient, or icon)
- Color coding: green (positive), gray (neutral), red (negative)
- Intensity reflects score magnitude [-1, 1]
- Accessible (ARIA labels, keyboard navigation)
- **Error paths:** missing score, invalid score
- **Edge cases:** score exactly 0, extreme values

**Test Plan:**
- **Unit Tests:**
  - \`test_sentiment_color_mapping\` - Score to color logic
  - \`test_sentiment_bar_width\` - Visual calculations
  - \`test_accessibility_attributes\` - ARIA labels present
- **Integration Tests:**
  - \`test_sentiment_in_post_card\` - Component rendering
- **E2E Tests:**
  - Playwright visual regression test

**Dependencies:**
- ING-004 (DONE)

**Context:** See [ToDoList.md]($TODOLIST_URL#25-frontend-components--data-ux)" \
    "phase:frontend,area:frontend,P1,TODO"

create_issue \
    "FE-CORE-002: Infinite Scroll (Stable)" \
    "Stabilize existing infinite scroll with test coverage.

**Acceptance Criteria:**
- IntersectionObserver properly mocked in tests
- Scroll triggers load more posts
- Loading state displayed during fetch
- No duplicate posts loaded
- **Error paths:** fetch failure, empty next page
- **Edge cases:** rapid scrolling, network flakiness

**Test Plan:**
- **Unit Tests:**
  - \`test_intersection_observer_mock\` - Observer setup
  - \`test_load_more_trigger\` - Scroll detection
  - \`test_deduplicate_posts\` - Prevent duplicates
- **Integration Tests:**
  - \`test_infinite_scroll_flow\` - Full scroll interaction
  - \`test_scroll_error_handling\` - Network failure recovery
- **E2E Tests:**
  - Playwright test scrolling through multiple pages

**Context:** See [ToDoList.md]($TODOLIST_URL#25-frontend-components--data-ux)" \
    "phase:frontend,area:frontend,P1,TODO"

create_issue \
    "FE-CORE-003: Error Boundary" \
    "Implement React Error Boundary for graceful error handling.

**Acceptance Criteria:**
- Error boundary wraps critical components
- Fallback UI displays user-friendly message
- Errors logged to observability system
- Boundary doesn't catch event handler errors
- **Error paths:** nested boundaries, repeated errors
- **Edge cases:** error during fallback render

**Test Plan:**
- **Unit Tests:**
  - \`test_error_boundary_catches_error\` - Error caught
  - \`test_fallback_ui_rendered\` - Fallback display
  - \`test_error_logged\` - Logging integration
- **Integration Tests:**
  - \`test_throwing_component\` - Component that throws
  - \`test_boundary_reset\` - Recovery mechanism
- **E2E Tests:**
  - Playwright test triggering error

**Dependencies:**
- OBS-003 (DONE)

**Context:** See [ToDoList.md]($TODOLIST_URL#25-frontend-components--data-ux)" \
    "phase:frontend,area:frontend,P2,TODO"

# ============================================================================
# PHASE 6: SECURITY (2 issues)
# ============================================================================

create_issue \
    "SEC-002: Role-Based Access" \
    "Implement role-based access control (reviewer vs admin).

**Acceptance Criteria:**
- Roles stored in user model: \`reviewer\`, \`admin\`
- Role restrictions enforced on review endpoints
- Admins can perform all actions, reviewers limited
- Role checked on every protected endpoint
- **Error paths:** missing role, invalid role, privilege escalation
- **Edge cases:** role changes mid-session, multiple roles

**Test Plan:**
- **Unit Tests:**
  - \`test_role_extraction\` - Parse role from token
  - \`test_role_authorization\` - Permission checking
  - \`test_unauthorized_role_access\` - Rejection
- **Integration Tests:**
  - \`test_reviewer_limited_access\` - Reviewer can't admin
  - \`test_admin_full_access\` - Admin can do everything
- **E2E Tests:**
  - Playwright test with different role logins

**Dependencies:**
- SEC-001 (DONE)

**Context:** See [ToDoList.md]($TODOLIST_URL#26-security--auth)" \
    "phase:security,area:backend,P1,TODO"

create_issue \
    "SEC-003: Rate Limiting" \
    "Implement per-IP rate limiting on refresh endpoints.

**Acceptance Criteria:**
- Rate limit: 10 requests per minute per IP on \`/api/refresh\`
- Exceed limit returns 429 Too Many Requests
- Rate limit info in response headers (X-RateLimit-*)
- Different limits for authenticated vs anonymous
- **Error paths:** Redis unavailable, IP spoofing
- **Edge cases:** distributed IPs, legitimate bursts

**Test Plan:**
- **Unit Tests:**
  - \`test_rate_limit_counter\` - Counting logic
  - \`test_rate_limit_exceeded\` - 429 response
  - \`test_rate_limit_reset\` - Window expiration
- **Integration Tests:**
  - \`test_rapid_requests\` - Send 11 requests quickly
  - \`test_authenticated_higher_limit\` - Different limits
- **E2E Tests:**
  - Manual load testing

**Context:** See [ToDoList.md]($TODOLIST_URL#26-security--auth)" \
    "phase:security,area:backend,P2,TODO"

# ============================================================================
# PHASE 7: ANALYTICS (3 issues)
# ============================================================================

create_issue \
    "ANA-001: Sentiment Trend Rollups" \
    "Aggregate daily sentiment scores per leader.

**Acceptance Criteria:**
- \`/api/analytics/sentiment\` returns day buckets
- Each bucket: date, leader_id, avg_sentiment, post_count
- Data cached/materialized for performance
- Supports date range filtering
- **Error paths:** no data for range, invalid date format
- **Edge cases:** timezone handling, partial days

**Test Plan:**
- **Unit Tests:**
  - \`test_daily_aggregation\` - Grouping logic
  - \`test_sentiment_average_calculation\` - Math correctness
  - \`test_date_range_filtering\` - Query filtering
- **Integration Tests:**
  - \`test_analytics_endpoint\` - Full API response
  - \`test_aggregation_performance\` - Query speed
- **E2E Tests:**
  - Playwright test viewing sentiment trends

**Dependencies:**
- ⚠️ **BLOCKED:** Analytics storage decision needed

**Context:** See [ToDoList.md]($TODOLIST_URL#27-analytics--derived-metrics)" \
    "phase:analytics,area:backend,P2,TODO,blocked"

create_issue \
    "ANA-002: Post Velocity Metric" \
    "Calculate posts per leader over 7-day rolling window.

**Acceptance Criteria:**
- Metric: \`posts_per_7d\` per leader
- API endpoint \`/api/analytics/velocity\` returns values
- Rolling window updates daily
- Historical velocity tracked
- **Error paths:** insufficient data, date gaps
- **Edge cases:** new leaders, deleted posts

**Test Plan:**
- **Unit Tests:**
  - \`test_rolling_window_calculation\` - 7-day logic
  - \`test_velocity_with_gaps\` - Missing data handling
  - \`test_new_leader_velocity\` - Bootstrap case
- **Integration Tests:**
  - \`test_velocity_endpoint\` - Full API response
  - \`test_velocity_time_series\` - Historical data
- **E2E Tests:**
  - Playwright test viewing velocity charts

**Context:** See [ToDoList.md]($TODOLIST_URL#27-analytics--derived-metrics)" \
    "phase:analytics,area:backend,P2,TODO"

create_issue \
    "ANA-003: Revision Change Count" \
    "Count content revisions per leader.

**Acceptance Criteria:**
- Endpoint \`/api/analytics/revisions\` exposes counts
- Metric: total revisions per leader
- Includes revision timestamps
- Supports filtering by date range
- **Error paths:** missing revision data, corrupt hashes
- **Edge cases:** mass revisions, reverted changes

**Test Plan:**
- **Unit Tests:**
  - \`test_revision_counting\` - Aggregation logic
  - \`test_revision_filtering\` - Date range
  - \`test_no_revisions_case\` - Zero revisions handling
- **Integration Tests:**
  - \`test_revisions_endpoint\` - Full API response
  - \`test_revision_consistency\` - Data integrity
- **E2E Tests:**
  - Playwright test viewing revision metrics

**Dependencies:**
- ING-001 (DONE)

**Context:** See [ToDoList.md]($TODOLIST_URL#27-analytics--derived-metrics)" \
    "phase:analytics,area:backend,P2,TODO"

# ============================================================================
# PHASE 8: PERFORMANCE (3 issues)
# ============================================================================

create_issue \
    "PERF-001: Query Index Review" \
    "Add database indices on frequently queried columns.

**Acceptance Criteria:**
- Indices added on: \`timestamp\`, \`leader_id\`, \`status\`
- EXPLAIN plans show index usage
- Query performance improved
- No negative impact on write performance
- **Error paths:** index corruption, lock timeout
- **Edge cases:** large table migration, composite indices

**Test Plan:**
- **Unit Tests:**
  - \`test_query_uses_index\` - EXPLAIN analysis
  - \`test_index_selectivity\` - Effectiveness measurement
- **Integration Tests:**
  - \`test_query_performance\` - Before/after timing
  - \`test_write_performance_maintained\` - No degradation

**Context:** See [ToDoList.md]($TODOLIST_URL#28-performance--scaling)" \
    "phase:performance,area:backend,P2,TODO"

create_issue \
    "PERF-002: Caching Layer (Read)" \
    "Implement caching layer for dashboard reads.

**Acceptance Criteria:**
- \`/api/dashboard\` responses cached
- Cache hit ratio metric exposed
- TTL configurable (default 5 minutes)
- Cache invalidation on data updates
- **Error paths:** cache unavailable, stale data
- **Edge cases:** cache stampede, partial updates

**Test Plan:**
- **Unit Tests:**
  - \`test_cache_hit\` - Verify cached response
  - \`test_cache_miss\` - Verify fetch and store
  - \`test_cache_invalidation\` - Update clears cache
- **Integration Tests:**
  - \`test_cache_hit_ratio\` - Metric calculation
  - \`test_cache_fallback\` - Redis down scenario

**Dependencies:**
- ⚠️ **BLOCKED:** Cache technology decision needed

**Context:** See [ToDoList.md]($TODOLIST_URL#28-performance--scaling)" \
    "phase:performance,area:backend,P2,TODO,blocked"

create_issue \
    "PERF-003: Async Fetch Batch" \
    "Parallelize ingestion fetches to reduce latency.

**Acceptance Criteria:**
- Multiple leader fetches run concurrently
- Wall time reduced vs sequential baseline
- Configurable concurrency limit (default 5)
- Error handling doesn't block other fetches
- **Error paths:** partial failures, timeout one source
- **Edge cases:** too many concurrent requests, rate limit hit

**Test Plan:**
- **Unit Tests:**
  - \`test_concurrent_fetch\` - Parallel execution
  - \`test_partial_failure_handling\` - Some succeed, some fail
  - \`test_concurrency_limit\` - Max concurrent respected
- **Integration Tests:**
  - \`test_wall_time_reduction\` - Timing comparison
  - \`test_error_isolation\` - One failure doesn't stop others

**Dependencies:**
- ING-006 (DONE)

**Context:** See [ToDoList.md]($TODOLIST_URL#28-performance--scaling)" \
    "phase:performance,area:backend,P3,TODO"

# ============================================================================
# PHASE 9: E2E TESTING (3 issues)
# ============================================================================

create_issue \
    "E2E-001: Playwright Bootstrap" \
    "Set up Playwright for end-to-end testing.

**Acceptance Criteria:**
- \`playwright.yml\` workflow in CI
- Smoke test: load dashboard and scroll
- CI run outputs trace artifact
- Tests run on PR and main push
- **Error paths:** browser crash, network timeout
- **Edge cases:** flaky tests, screenshot diffs

**Test Plan:**
- **E2E Tests:**
  - \`smoke.spec.ts\` - Load dashboard, verify title, scroll

**Context:** See [ToDoList.md]($TODOLIST_URL#29-e2e--qa-automation)" \
    "phase:e2e,area:qa,P1,TODO"

create_issue \
    "E2E-002: Review Flow E2E" \
    "Playwright test for approve and reject workflows.

**Acceptance Criteria:**
- Test scenario: login, navigate to review queue, approve/reject post
- Visual trace captured
- Assertions on UI state and API responses
- Tests both approval and rejection paths
- **Error paths:** network failure during action
- **Edge cases:** concurrent reviews, stale data

**Test Plan:**
- **E2E Tests:**
  - \`review-flow.spec.ts\` - Full approve/reject scenarios

**Dependencies:**
- E2E-001, REV-001 (DONE)

**Context:** See [ToDoList.md]($TODOLIST_URL#29-e2e--qa-automation)" \
    "phase:e2e,area:qa,P1,TODO"

create_issue \
    "E2E-003: Leader CRUD E2E" \
    "Playwright test for adding and deleting leaders.

**Acceptance Criteria:**
- Test scenario: add new leader, verify in list, delete, verify removed
- Both DOM and API state verified
- Tests handle async operations correctly
- **Error paths:** duplicate leader, invalid handle
- **Edge cases:** rapid add/delete, concurrent modifications

**Test Plan:**
- **E2E Tests:**
  - \`leader-crud.spec.ts\` - Full CRUD lifecycle

**Dependencies:**
- E2E-001, ING-009 (DONE)

**Context:** See [ToDoList.md]($TODOLIST_URL#29-e2e--qa-automation)" \
    "phase:e2e,area:qa,P2,TODO"

# ============================================================================
# PHASE 10: CI/CD (3 issues)
# ============================================================================

create_issue \
    "CI-002: Backend Coverage Gate" \
    "Fail CI if backend coverage drops below 80%.

**Acceptance Criteria:**
- Pytest exits non-zero if coverage <80%
- Coverage report visible in CI logs
- Badge in README shows coverage percentage
- Exclusions documented in \`.coveragerc\`
- **Error paths:** coverage tool malfunction
- **Edge cases:** new code without tests, flaky calculation

**Test Plan:**
- **Unit Tests:**
  - \`test_coverage_threshold_check\` - Verify exit code
- **Integration Tests:**
  - \`test_ci_fails_low_coverage\` - Simulate <80%

**Dependencies:**
- OBS-005

**Context:** See [ToDoList.md]($TODOLIST_URL#210-cicd-maturity)" \
    "phase:ci,area:backend,P1,TODO"

create_issue \
    "CI-004: CodeQL Workflow" \
    "Add CodeQL static analysis workflow.

**Acceptance Criteria:**
- \`.github/workflows/codeql.yml\` present and runs
- Alerts visible in GitHub Security tab
- Scans Python and JavaScript/TypeScript code
- Runs on push and PR
- **Error paths:** scan timeout, config errors
- **Edge cases:** false positives, new query packs

**Test Plan:**
- **Integration Tests:**
  - \`test_codeql_workflow_syntax\` - Validate YAML

**Dependencies:**
- OBS-006

**Context:** See [ToDoList.md]($TODOLIST_URL#210-cicd-maturity)" \
    "phase:ci,area:security,P2,TODO"

create_issue \
    "CI-005: Lint Blocking Mode" \
    "Make Ruff and ESLint required CI checks.

**Acceptance Criteria:**
- PR fails if \`ruff check .\` has violations
- PR fails if \`npm run lint\` has errors
- Status checks required in branch protection
- Lint errors clearly reported in CI logs
- **Error paths:** linter crash, config errors
- **Edge cases:** auto-fixable issues, ignore patterns

**Test Plan:**
- **Integration Tests:**
  - \`test_lint_failure_blocks_pr\` - Verify PR status

**Context:** See [ToDoList.md]($TODOLIST_URL#210-cicd-maturity)" \
    "phase:ci,area:quality,P1,TODO"

# ============================================================================
# OPEN QUESTIONS (3 issues)
# ============================================================================

create_issue \
    "QUESTION: Auth provider (custom JWT vs external IdP)" \
    "Decision needed on authentication architecture.

**Considerations:**

**Custom JWT:**
- ✅ Full control, no external dependencies
- ❌ Security responsibility, manual implementation of refresh tokens, password reset, 2FA

**External IdP (Auth0, Okta, Firebase):**
- ✅ Battle-tested security, built-in features (2FA, social login)
- ❌ External dependency, cost, vendor lock-in

**Decision Needed By:** Before SEC-001 continuation

**Blocked Tasks:**
- SEC-001 (partially - basic JWT done)
- SEC-002 (Role-Based Access)
- REV-002 (Reviewer Attribution)

**Discussion Points:**
1. Security requirements?
2. Expected user base size?
3. Need social login or enterprise SSO?
4. Budget for auth services?
5. Team's security expertise?

**Context:** See [ToDoList.md]($TODOLIST_URL#7-open-questions)" \
    "question,help wanted,blocked,phase:security"

create_issue \
    "QUESTION: Cache technology (Redis vs in-process)" \
    "Decision needed on caching implementation.

**Considerations:**

**Redis (External):**
- ✅ Distributed, shared across instances, persistence, rich data structures
- ❌ External dependency, deployment complexity, network latency, cost

**In-Process (Node cache, Python lru_cache):**
- ✅ Zero latency, no external deps, simple setup
- ❌ Not shared across instances, lost on restart, memory limited

**Decision Needed By:** Prior to PERF-002 implementation

**Blocked Tasks:**
- PERF-002 (Caching Layer)
- SEC-003 (Rate Limiting - may need distributed state)

**Discussion Points:**
1. Will application run on multiple instances?
2. Required cache hit ratio?
3. Acceptable staleness window?
4. Deployment environment?
5. Budget for caching infrastructure?

**Recommendation:** If planning horizontal scaling → Redis. If single-instance → in-process.

**Context:** See [ToDoList.md]($TODOLIST_URL#7-open-questions)" \
    "question,help wanted,blocked,phase:performance"

create_issue \
    "QUESTION: Analytics storage (same DB vs warehouse)" \
    "Decision needed on analytics data storage architecture.

**Considerations:**

**Same Database (PostgreSQL/MySQL):**
- ✅ Simple, no data sync, single source of truth
- ❌ Performance impact on OLTP, limited analytics features

**Data Warehouse (BigQuery, Redshift, Snowflake):**
- ✅ Optimized for analytics, scalable, advanced features
- ❌ Data pipeline needed, sync lag, cost, complexity

**Decision Needed By:** Before Phase P5 (Analytics Layer)

**Blocked Tasks:**
- ANA-001 (Sentiment Trend Rollups)
- ANA-002 (Post Velocity Metric)
- ANA-003 (Revision Change Count)

**Discussion Points:**
1. Expected data volume and query complexity?
2. Analytics latency requirements (real-time vs batch)?
3. Who consumes analytics (internal vs user-facing)?
4. Budget for data infrastructure?
5. Team's data engineering expertise?

**Recommendation:** Start with same DB using materialized views. Migrate to warehouse if performance issues (typically >100M rows).

**Context:** See [ToDoList.md]($TODOLIST_URL#7-open-questions)" \
    "question,help wanted,blocked,phase:analytics"

# ============================================================================
# COMPLETE
# ============================================================================

echo ""
echo "✅ Successfully created 29 GitHub issues!"
echo ""
echo "Summary:"
echo "  - TODO tasks: 23"
echo "  - BLOCKED questions: 3"
echo "  - Open questions: 3"
echo ""
echo "View all issues: https://github.com/$REPO/issues"
