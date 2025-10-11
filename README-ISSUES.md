# Creating GitHub Issues from ToDoList.md

This directory contains tools to create GitHub issues for all TODO, BLOCKED, and incomplete tasks in ToDoList.md.

## Quick Start

### Prerequisites
- [GitHub CLI (`gh`)](https://cli.github.com/) installed and authenticated
- Write access to Kodanda10/Amber repository

### Create All Issues

```bash
./create-issues.sh
```

This will create **27 GitHub issues** with complete specifications.

## What Gets Created

### Issue Breakdown
- **24 TODO tasks** across 10 development phases
- **3 QUESTION issues** for blocking architectural decisions

### All issues include:
- ✅ Atomic scope (one focused task per issue)
- ✅ Full acceptance criteria (including error paths and edge cases)
- ✅ Comprehensive test plan (unit/integration/e2e)
- ✅ Proper labels (phase, area, priority, status)
- ✅ Dependency tracking
- ✅ Links to ToDoList.md

## Issue Categories

### By Phase
1. **Ingestion** (1): Async worker
2. **Review & Moderation** (3): Attribution, editing, audit trail
3. **Observability** (2): Coverage gates, CodeQL
4. **Localization** (1): Locale toggle
5. **Frontend** (3): Sentiment viz, infinite scroll, error boundaries
6. **Security** (2): RBAC, rate limiting
7. **Analytics** (3): Sentiment trends, velocity, revisions
8. **Performance** (3): Query indices, caching, parallel fetch
9. **E2E Testing** (3): Playwright setup, review flow, CRUD
10. **CI/CD** (3): Coverage gate, CodeQL workflow, lint enforcement

### By Priority
- **P1 (High)**: 11 issues
- **P2 (Normal)**: 15 issues
- **P3 (Nice-to-have)**: 1 issue

### Blocked Issues
3 issues blocked by architectural decisions:
- **REV-002**: Needs auth integration
- **ANA-001**: Needs analytics storage decision
- **PERF-002**: Needs cache technology decision

## Manual Alternative

If you prefer to create issues manually, see [ISSUE_CREATION_PLAN.md](ISSUE_CREATION_PLAN.md) for complete issue templates.

## Verification

After running the script:

1. Visit https://github.com/Kodanda10/Amber/issues
2. Verify 27 new issues were created
3. Check that labels are applied correctly
4. Confirm all issues link to ToDoList.md

## Troubleshooting

### Authentication Issues
```bash
# Re-authenticate with GitHub
gh auth login

# Verify authentication
gh auth status
```

### Permission Issues
Ensure your GitHub account has write access to the repository:
```bash
gh repo view Kodanda10/Amber
```

### Script Errors
- Check that `gh` CLI version is up to date: `gh --version`
- Ensure you're in the repository root directory
- Make the script executable: `chmod +x create-issues.sh`

## Files

- **ToDoList.md**: Source of truth for all tasks
- **ISSUE_CREATION_PLAN.md**: Detailed specifications for each issue
- **create-issues.sh**: Automated issue creation script
- **README-ISSUES.md**: This file

## After Issue Creation

Once issues are created, update the PR description with:
- Links to all created issues
- Summary of issues by phase
- Any issues that couldn't be created (with reasons)

## Questions?

See the "Open Questions" section in [ISSUE_CREATION_PLAN.md](ISSUE_CREATION_PLAN.md) for the 3 architectural decisions that need to be made.
