# Evaluation (achieved results, limitations, future work)

## Achieved results
- **End-to-end web application** for sports team management and match statistics.
- **Backend (Python/FastAPI)** provides:
  - match lifecycle (planned/live/finished)
  - lineup nomination (starter/sub) and match jersey numbers
  - event logging and per-match aggregated player statistics
  - reports (season and last-N summaries)
  - coach ratings per match
  - exports (CSV)
  - analytics endpoints (leaderboards, time series)
- **Frontend (React)** provides:
  - authentication UI
  - roster and match management
  - lineup editor
  - live event recording UI (single-device “real-time”)
  - ratings UI
  - analytics UI with charts
- **Data layer**: clear schema with Alembic migrations; SQLite used for development, with a migration-first workflow.
- **Testing**: automated backend tests cover auth/RBAC, events → stats aggregation, import/export, ratings, analytics.
## Practical validation (real-world conditions)
Using the manual script in `FIELD_TEST.md`, the application can be validated in a realistic workflow:
- coach pre-match lineup
- live event recording during play
- post-match ratings
- season summary and export
## Limitations
- **Single-device “real-time”**: the UI updates immediately on the device that records events, but there is no multi-device live syncing (no polling/WS broadcast).
- **MVP security posture**: authentication + RBAC are implemented for the thesis requirements, but production hardening (password policy, rotation, refresh tokens, audit logs) is outside scope.
- **SQLite**: suitable for development and thesis demonstration; for production, Postgres is recommended.
- **Analytics depth**: current analytics focus on descriptive statistics (counts/sums/averages). More advanced metrics can be added.
## Future enhancements
- **Multi-device live module**: polling or WebSocket broadcasting of new events/stats.
- **Multi-club tenancy**: remove global uniqueness where needed and add richer permission model.
- **Deployment**: Postgres + Docker + CI.
- **Advanced analytics**: composite performance scores, role-aware normalization, trend detection, ML-assisted ratings.
- **UX**: timer-based time input, undo event UI, faster “quick actions” per player, offline-first recording.
