#!/bin/bash
# GitHub Issue Creation Script for Amber Roadmap Gaps
# This script creates 27 issues based on ToDoList.md analysis
# Requires: gh CLI (GitHub CLI) to be installed and authenticated

set -e

REPO="Kodanda10/Amber"
TODOLIST_URL="https://github.com/Kodanda10/Amber/blob/roadmap/fill-gaps/ToDoList.md"

echo "🚀 Creating 27 GitHub issues for Amber Roadmap Gaps..."
echo "Repository: $REPO"
echo ""

# Function to see if an issue with this exact title already exists
issue_exists() {
  local title="$1"
  gh issue list \
    --repo "$REPO" \
    --limit 100 \
    --json title \
    --jq ".[] | select(.title == \"$title\")" \
    | grep -q '"title"' || return 1
  return 0
}

# Function to create an issue
create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"

    if issue_exists "$title"; then
      echo "⚠️  Skipping \"$title\" — already exists"
      echo ""
      return
    fi

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

# ...rest of your 26 create_issue calls go here unchanged...

echo ""
echo "✅ Done. Any new issues have been created; existing titles were skipped."
echo ""
echo "View all issues: https://github.com/$REPO/issues"
