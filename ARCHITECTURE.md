# Architecture and design decisions

This document describes the high-level architecture of the Trainer App and the main design choices made for the thesis project.

## Overview

The application is a **full-stack sports team management and match statistics** system:

- **Backend**: FastAPI (Python), SQLAlchemy ORM, Alembic migrations, JWT auth, RBAC (coach/assistant).
- **Frontend**: React (Vite), TypeScript, TanStack Query, Tailwind CSS.
- **Database**: SQLite for development (default); schema is migration-driven and can target PostgreSQL via `TRAINERAPP_DATABASE_URL`.

## Backend architecture

### Layers

1. **API routes** (`app/api/routes/`)  
   Thin HTTP layer: parse input, call services or queries, return responses. Route handlers catch domain exceptions (`AppError`) and map them to HTTP status codes.  
   **Club profile**: `GET /club` (any authenticated user), `PUT /club` (coach only) for name, city, stadium, etc.

2. **Services** (`app/services/`)  
   Application use cases and transaction boundaries:
   - `match_service`: start match, half-time, second half, finish (single commit per operation).
   - `lineup_service`: validate and save lineup (duplicate player/jersey checks, replace lineup in one transaction).
   - `ratings_service`: save coach ratings for a finished match.
   - `stats_service`: aggregate match events into `match_player_stats` (used by events route in same transaction).

3. **Schemas** (`app/schemas/`)  
   Pydantic models for request/response and validation. Domain rules (e.g. allowed event types, delta ±1, half 1/2) are enforced in schemas so routes stay thin.

4. **Models** (`app/models/`)  
   SQLAlchemy ORM entities. Timestamps use a shared `app.util.time.utcnow()` so all stored times are consistently UTC.

5. **Common / util**  
   - `app.common.enums`: `EventType`, `LineupRole`, `MatchStatus`, `UserRole` (used in schemas and domain logic).
   - `app.util.time`: `utcnow()` for all `created_at` / `live_started_at` defaults.
   - `app.exceptions`: `AppError`, `NotFoundError`, `BadRequestError`, `ForbiddenError` for consistent API errors.

### Database

- **Migrations**: Alembic; schema changes are done only via migrations.
- **Integrity**: Uniqueness constraints on `match_lineups (match_id, player_id)`, `match_player_stats (match_id, player_id)`, `match_player_ratings (match_id, player_id)` to prevent inconsistent data.
- **Session handling**: One session per request via FastAPI dependency `get_db()`; services that perform writes own the commit/rollback within that session.

### Time handling

- All timestamps are stored as **UTC** (using `app.util.time.utcnow()`).
- The app is single-timezone; explicit timezone handling for users is out of scope and documented as such.

## Frontend architecture

- **API client** (`frontend/src/api/client.ts`): Axios instance with `baseURL` from `VITE_API_URL` (fallback: `http://127.0.0.1:8000`). Interceptors attach JWT and clear token on 401.
- **API modules** (`api/matches.ts`, `api/players.ts`, etc.): Typed wrappers (e.g. `listMatches()`, `createMatch()`, `addEvent()`) so pages do not call raw `api.get/post` everywhere.
- **Auth**: JWT in memory/localStorage, `AuthContext` and protected routes.

## Design decisions (summary)

| Decision | Rationale |
|----------|-----------|
| Validation in Pydantic schemas | Single place for domain rules; routes stay thin and do not duplicate checks. |
| Service layer for match/lineup/ratings | Clear use-case boundaries and transaction ownership; easier to test and document. |
| DB uniqueness on lineups and stats | Prevents duplicate player per match at DB level; aligns with stats/ratings constraints. |
| Central `utcnow()` | Consistent UTC semantics and one place to change if time handling is extended. |
| Configurable API URL via env | Supports different environments (dev/staging) without code changes. |
| Domain exceptions (`AppError`) | Consistent error shape and status codes; handler in `main.py` maps to JSON `detail`. |

## Running and testing

- **Backend**: From `backend/`, `uvicorn app.main:app --reload --port 8000`. Tests: `pytest tests/`.
- **Frontend**: From `frontend/`, `npm run dev` (uses `VITE_API_URL` if set).
- **Database**: After clone, run `python -m app.scripts.seed` from `backend/` to create schema and demo data (see README).
