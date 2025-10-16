# Amber Project - Development Log

This log tracks all development activities performed by the Gemini agent, following the Ironclad DevOps Rulebook v2.1.

## Development Actions (October 2, 2025)

*   **Renamed Project Directory:** Renamed the project directory from `Amber` to `amber` to comply with npm naming restrictions.
*   **Cleaned Project Directory:** Removed conflicting files (excluding `.agent-policy/` and `GEMINI.md`) from the `amber` directory to prepare for Next.js initialization.
*   **Initialized Next.js Application:** Created a `nextjs-app` subdirectory within `amber` and successfully initialized a new Next.js project (TypeScript, ESLint, Tailwind CSS, App Router) using `npx create-next-app@latest`.
*   **Copied Old Project Files:** Copied relevant source files and directories (`App.tsx`, `constants.tsx`, `index.tsx`, `metadata.json`, `types.ts`, `vite.config.ts`, `backend/`, `components/`, `hooks/`, `services/`) from the old Amber project (`/Volumes/abhijita/Projects/Amber`) into the newly created `amber/nextjs-app` directory.

## Development Actions (October 4, 2025)

*   **Implemented Facebook Graph ingestion scaffolding:** Added feature-flagged Graph client and backend ingestion path that persists avatar/media metadata with TDD coverage (`tests/test_facebook_ingestion.py`).
*   **Surfaced localization cues in UI:** Hooked shared Hindi utilities into `PostCard` and `Dashboard`, added Vitest suites to assert badges/summary output.
*   **Policy alignment:** Updated `ToDoList.md`, `AGENTS.md`, and PR change log to reflect ING-006 WIP and L10N-002 follow-up, honoring Ironclad DevOps Rulebook v2.1.
*   **Established admin JWT skeleton:** Protected `/api/admin/ping` via signed tokens and added end-to-end pytest coverage for authorized/unauthorized flows.

## Development Actions (October 6, 2025)

*   **Completed Graph ingestion feature:** Finalized `_sync_posts_for_leader` to prioritize Facebook Graph when flagged, persist `platformPostId`/`mediaUrl`/`avatarUrl`, and fall back to news or sample data; validated via `tests/test_facebook_ingestion.py`.
*   **Expanded leader catalog:** Seeded the 11 provided Facebook handles and added pytest coverage (`tests/test_leader_seed.py`) to guard the roster.
*   **Dashboard roster & deletion controls:** Introduced a leader roster panel with delete/refresh actions and Vitest coverage (`src/tests/dashboard.test.tsx`, `src/components/Dashboard.test.tsx`) ensuring UI parity with backend data.
*   **Admin ping regression:** Restored `ADMIN_JWT_SECRET` helpers and `/api/admin/ping` guard with serializer-based tokens to keep `SEC-001` tests green post-refactor.

## Development Actions (October 7, 2025)

*   **Graph metadata surfaced to UI:** `PostCard` now renders backend-provided `avatarUrl`, Hindi date badges, and optional `mediaUrl` attachments with targeted Vitest coverage (`src/components/PostCard.test.tsx`).
*   **Admin token issuance endpoint:** Added `/api/admin/token` gated by `ADMIN_BOOTSTRAP_SECRET` alongside pytest coverage (`tests/test_auth.py`) ensuring tokens flow through `/api/admin/ping`.
*   **Structured error logging:** Centralized exception handler emits JSON error envelopes and logs with request correlation; verified via `tests/test_observability_and_ingest.py::test_error_log_shape_on_exception`.
*   **Removed legacy Vite stack:** Deleted `archive/vite-app/` so the repository solely reflects the Next.js implementation.

## Development Actions (October 16, 2025)

*   **Platform post normalization hardening:** Added `ensure_post_schema()` migrations plus ingestion updates so Facebook/Twitter/X writes persist `platformPostId` consistently; revised merge order to preserve latest metrics.
*   **Expanded backend TDD coverage:** New pytest suites (`tests/test_platform_post_schema.py`, `tests/test_external_clients.py`) cover schema backfill, Graph/Twitter revisions, and social client adapters, lifting backend coverage to 88%.
*   **Regression-proofed ingestion dedup:** Facebook/Twitter tests now assert revision increments and metric refresh for duplicate posts, guarding ANA-001 scenarios with deterministic fixtures.
