## Trainer App – Match Analytics User Guide

Web application for managing a football team, building match lineups, recording in‑match events with precise timestamps, and analyzing player/team performance through dashboards and coach ratings.

---

## 1. Tech stack and architecture

- **Backend**: Python, **FastAPI**, SQLAlchemy, SQLite (dev), Alembic (migrations)
- **Frontend**: **React + TypeScript** (Vite), React Router, TanStack React Query, TailwindCSS, Recharts
- **Architecture**:
  - **React UI** talks to a **FastAPI REST API**
  - FastAPI persists data via **SQLAlchemy** into the configured database
  - Match events are stored as an **event log** (`half`, `second_in_match`) and aggregated into `MatchPlayerStats` for fast reporting

---

## 2. Installation and local run

### 2.1 Backend setup

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 2.1.1 Database configuration

- **Default (recommended for local dev)**:
  - Uses SQLite file `app.db` in `backend/`.
  - This is controlled by the env variable `TRAINERAPP_DATABASE_URL`.
  - If not set, the backend defaults to:

```bash
TRAINERAPP_DATABASE_URL=sqlite:///./app.db
```

- **Custom database (e.g. PostgreSQL)**:
  - Set `TRAINERAPP_DATABASE_URL` before running the app, for example:

```bash
export TRAINERAPP_DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/trainerapp
```

> **Note**: For non-SQLite databases you must ensure the DB exists and run Alembic migrations accordingly.

#### 2.1.2 Create schema and seed demo data

The project includes a helper script that resets the DB and seeds a demo club, users, players, season, and one match.

From `backend/`:

```bash
python -m app.scripts.seed
```

This will:
- **Create schema** via Alembic.
- Create **Demo Club**, players, and users.
- Create a demo season and a first match.

You can optionally generate a **high‑volume test match** for analytics:

```bash
python -m app.scripts.generate_analytics_test_match --events 500 --seed 42 --replace-existing
```

This creates a finished match called **“Analytics Test Match”** with 300–500+ events for stress‑testing charts.

#### 2.1.3 Run the backend server

From `backend/` (with virtualenv activated):

```bash
uvicorn app.main:app --reload --port 8000
```

Useful URLs:
- **API docs (Swagger)**: `http://127.0.0.1:8000/docs`
- **Health check**: `http://127.0.0.1:8000/health`

---

### 2.2 Frontend setup

From `frontend/`:

```bash
npm install
npm run dev
```

The app runs at:

- `http://127.0.0.1:5173`

The backend CORS settings already allow:
- `http://localhost:5173`
- `http://127.0.0.1:5173`

---

## 3. Demo login (users and roles)

After `seed.py`, you can log in using:

- **Coach (full access)**  
  - **Email**: `coach@demo.local`  
  - **Password**: `coach`

- **Assistant (limited, e.g. no match creation)**  
  - **Email**: `assistant@demo.local`  
  - **Password**: `assistant`

Use the **coach** account for most workflows in this guide (creating matches, editing lineup, exporting CSV, coach ratings).

---

## 4. Main workflow: from match creation to analytics review

The typical workflow is:

1. **Create a match**
2. **Create and edit the lineup**
3. **Start the match and run the clock**
4. **Record events**
5. **Manage substitutions**
6. **Finish the match**
7. **Assign coach ratings**
8. **Review analytics & statistics**
9. **Export data if needed**

Everything is accessible from the **Matches** page and linked views.

---

## 5. Creating a match

1. Open the app in a browser: `http://127.0.0.1:5173`.
2. Log in as the **coach**.
3. Go to the **Matches** page (main navigation).
4. In the **“Vytvořit zápas”** form:
   - **Soupeř**: opponent name (e.g. `Sparta`).
   - **Soutěž**: competition name (e.g. `Liga`).
   - **Datum/čas (ISO)**: date/time in ISO format (e.g. `2026-02-23T18:00:00`).
   - **Sezóna ID**: numeric season ID (the seed script creates season `1`).
5. Click **“Vytvořit zápas → Sestava”**.

The backend will:
- Create a new match in **planned** status.
- Redirect you to the **Lineup** page for the new match.

---

## 6. Creating and editing the lineup

On the **Lineup** page for a given match:

- The page shows all club players with:
  - Default jersey number.
  - Current lineup status: **Hraje** (starter), **Střídá** (sub), **Nehraje** (out).
- At the top you see:
  - `Zápas ID`
  - Number of starters and subs currently selected.

### 6.1 Assign roles (starter / sub / out)

- **Starter** (`Hraje`):
  - Click the **“Hraje”** button to mark the player as a starter.
  - There can be **max 11** starters.
- **Substitute** (`Střídá`):
  - Click the **“Střídá”** button to mark as substitute.
  - There can be **max 5** substitutes.
- **Out of squad** (`Nehraje`):
  - Click **“Nehraje”** to remove the player from the matchday squad.

If you exceed limits (more than 11 starters or 5 subs), the app shows an error and prevents the change.

### 6.2 Jersey numbers

- Each player has:
  - **Default jersey number** (from the roster).
  - Optional **match jersey number** you can override.
- To override:
  - Enter a custom number in the jersey input.
  - Leave blank to use the default number.
- The UI warns about **duplicate jersey numbers** in the match squad.
  - You need to fix duplicates before saving.

### 6.3 Saving lineup and going to Live

- **Top‑right buttons**:
  - **“Uložit”**: saves the current lineup only.
  - **“Přejít na Live”**: saves the lineup and navigates to the **Live match** screen.

> **Important**: Going to Live does **not** automatically start the match clock. The match remains in `planned` status until you explicitly start the first half on the Live page.

---

## 7. Starting a match and recording live events

### 7.1 Live match header and timer

On the **Live** page for a match you see:

- Match info (opponent, competition).
- Current **status**: `planned`, `live_half_1`, `half_time`, `live_half_2`, `finished`.
- A **match timer** showing match time (e.g. `12:34`).
- Current half indicator (`—` before start, then `1` or `2`).

The timer is driven by:
- The match status.
- `seconds_before_live` (accumulated time).
- `live_started_at` (UTC; set at half starts).

### 7.2 Starting, pausing, and finishing halves

- **Start 1st half**:
  - Click the **“Start 1st Half”** button.
  - Match status becomes `live_half_1`.
  - Timer starts from `00:00` and increases only while live.

- **Half-time**:
  - Click **“Half-Time”** near 45 minutes.
  - Status becomes `half_time`.
  - Timer stops; event buttons are disabled.

- **Start 2nd half**:
  - Click **“Start 2nd Half”**.
  - Status becomes `live_half_2`.
  - Timer resumes from `45:00` and keeps increasing while live.

- **Finish match**:
  - Click **“Finish Match”** near 90 minutes.
  - Status becomes `finished`.
  - Timer stops permanently; events and substitutions are disabled.
  - You are redirected to the **Evaluation / Match Report** page.

### 7.3 Recording events

On the Live page you have a **per‑player event panel**:

- Each player row shows:
  - Name and jersey number.
  - Status label: `Na hřišti`, `Na lavičce`, `Vystřídán`.
  - A row of compact buttons like `[ + ] Přihrávka [ − ]`, `[ + ] Střela`, `[ + ] Souboj`, etc.

**How it works**:
- **+ button**: adds one event of that type for the player.
- **− button**: removes one previously added event (down to zero).
- At the moment you click:
  - The app captures the **exact match time** using the live timer.
  - Sends an event with `half` and `second_in_match` to the backend.
  - Backend stores the event and updates aggregated stats.

Examples:
- Pass at 12:34 → `half=1`, `second_in_match=754`.
- Goal at 44:10 → `half=1`, `second_in_match=2650`.
- Foul at 67:22 → `half=2`, `second_in_match=4042`.

> **Note**: Events can only be recorded when the match status is `live_half_1` or `live_half_2`. During `planned`, `half_time`, or `finished`, event buttons are disabled.

---

## 8. Managing substitutions

On the Live page, the **Substitutions** section shows:

- **Aktuálně na hřišti** – list of players currently on the pitch.
- Substitution **history** with time, half, and `OUT → IN` pairs.

### 8.1 Creating a substitution

1. Choose the **player going out** (must currently be on the field).
2. Choose the **player coming in** (must be on the bench).
3. Confirm:
   - The app captures:
     - `half` (1 or 2, based on current time).
     - `second_in_match` (exact match second).
4. The substitution is stored and:
   - On‑field list is updated.
   - Player labels in the events panel are updated (who is `Na hřišti`, `Vystřídán`, `Na lavičce`).

Substitutions later provide context for:
- When intensity changes.
- Which players influenced which phases of the match.

---

## 9. Finishing the match

When the match is over:

1. On the **Live** page, click **“Finish Match”**.
2. Backend:
   - Finalizes `seconds_before_live`.
   - Sets status to `finished`.
3. Frontend:
   - Disables all event and substitution controls.
   - Navigates to the **Match Evaluation / Report** page.

From now on, the match is read‑only for events, but you can:
- Assign or edit **coach ratings**.
- View detailed analytics and tables.
- Export match events CSV.

---

## 10. Assigning coach ratings

Coach ratings live on the **Match Evaluation** (`/matches/{id}/evaluation`) page. You can only reach this page for a **finished** match.

### 10.1 Auto vs coach vs combined rating

For each player who actually played (starters + subs who entered):

- **Auto rating**:
  - Computed from the player’s stats (goals, assists, shots, passes, duels, errors, cards, etc.).
  - Shown with one decimal (1.0–10.0).

- **Coach rating**:
  - You enter a value **1–10** based on your subjective evaluation.

- **Combined rating**:
  - Weighted blend: **60% auto + 40% coach** (if a valid coach rating is provided).
  - Falls back to auto rating only if no valid coach rating is set.

### 10.2 Where to edit ratings

In the **“Hodnocení trenéra (po zápase)”** card:

- Table columns:
  - **Hráč** – name, jersey, starter/sub.
  - **Auto rating** – read‑only.
  - **Hodnocení trenéra** – editable numeric input (1–10).
  - **Kombinované** – computed live.
  - **Poznámka trenéra** – optional free text.

To save:

1. Fill in ratings and optional notes for players.
2. Click **“Uložit hodnocení trenéra”**.
3. The app sends ratings to the backend and refreshes saved data.

---

## 11. Viewing match analytics and statistics

The **Match Evaluation** page is also your **Match Report / Analytics dashboard**.

### 11.1 Timeline and intensity charts

The top card **“Průběh zápasu v čase”** shows several Recharts line charts using 5‑minute buckets:

- **Celková intenzita**:
  - One teal line `Akce celkem` showing the total number of actions per 5‑minute interval.

- **Přihrávky a souboje**:
  - Blue line: `Přihrávky`.
  - Orange line: `Souboje`.

- **Střely a góly**:
  - Purple line: `Střely` (on + off target).
  - Green line: `Góly`.

- **Fauly a karty**:
  - Slate line: `Fauly`.
  - Yellow line: `Žluté karty`.
  - Red line: `Červené karty`.

**How to read & interact**:

- **X axis**:
  - Shows the **start minute** of the 5‑minute bucket (e.g. `15'` means 15–20 minutes).
- **Tooltips**:
  - Hover near a point to see a tooltip like `15.–20. minuta` with values for all series at that time.
- **Legends as “filters”**:
  - Click on a legend item (e.g. “Přihrávky”) to toggle that series on/off.
  - This acts as a simple filter to focus on one metric at a time without clutter.

This lets you see:
- When the match was most intense.
- How shots, duels, and fouls evolved across the two halves.
- Whether discipline problems cluster in certain phases (e.g. after substitutions).

### 11.2 Team match statistics

The **“Týmové statistiky v zápase”** card contains:

- **Team overview table** (“Přehled týmu”):
  - Totals for goals, assists, shots on/off target, passes, duels, ball wins/losses, fouls, cards, penalties.
  - Accuracy metrics:
    - **Přesnost střel** – share of shots on target.
    - **Úspěšnost v soubojích** – % of duels won.

- **Grouped cards**:
  - **Útok** – goals/assists, shots, passes.
  - **Souboje a práce s míčem** – duels and ball recoveries/losses.
  - **Disciplína** – fouls, yellow cards, red cards.

### 11.3 Per‑player statistics table and top performers

The **“Souhrn výkonu hráčů”** card has two main parts:

- **Per‑player stats table (“Statistiky hráčů”)**:
  - Columns include:
    - Goals, assists, shots, passes.
    - Duels (won/lost), ball wins/losses, fouls, cards.
    - **Podíl na akcích** – player’s share of team actions (passes + shots + duels + wins/losses + fouls).
    - Auto and combined ratings.
  - Horizontally scrollable on small screens.

- **Top performers cards**:
  - “Nejvíce přihrávek” – who made the most passes.
  - “Nejvíce vyhraných soubojů” – most duels won.
  - “Nejvíce střel” – most total shots.

Together, these let you quickly see:
- Who dominated possession or passing.
- Who was most active in duels.
- Who took the most shots and how that lines up with goals/assists.

---

## 12. Using filters and charts in analytics

While there is no complex filter UI yet (like sliders or dropdowns), you can still **focus** the analytics effectively:

- **Per‑chart focusing**:
  - Use the **legends** to toggle series on/off. For example, hide passes to focus only on duels.

- **Phase‑based reading**:
  - Mentally group the X‑axis:
    - 0–45 minutes (1st half).
    - 45–60, 60–75, 75–90 for late‑game phases.
  - Look for spikes in:
    - Shots or goals in the last 15 minutes (clutch performance).
    - Fouls and cards in specific segments (discipline issues).

- **Cross‑reading with substitutions**:
  - Combine substitution times with the charts:
    - If a key sub happened at ~60 minutes, look at buckets 60–65, 65–70, etc.
    - Check if team intensity or certain players’ contributions changed after a substitution.

---

## 13. Exporting data (CSV & reports)

The app supports several CSV exports.

### 13.1 Export match events (CSV)

From the **Matches** page:

- Each row has an **“Export events”** button (visible to coach).
- Clicking it calls `GET /export/matches/{match_id}/events.csv` and downloads:
  - One row per event with:
    - Event ID, match ID, half, `second_in_match`.
    - `event_type`, `delta`.
    - Player ID, name, default jersey, match jersey.

You can open this in Excel, Google Sheets, or further process it in Python/R.

### 13.2 Export players (CSV)

From the **Players** page:

- There is an **“Export CSV”** button that calls `GET /export/players.csv`.
- The file contains:
  - `id`, `first_name`, `last_name`, `jersey_number`, `position`.

### 13.3 Export season‑level team stats (CSV, API)

For advanced users (via API, not yet wired into the UI):

- `GET /export/seasons/{season_id}/team_stats.csv`
  - Returns one summary row for the given season (goals, assists, passes, duels, cards, etc.).

---

## 14. Summary

- **Backend**: FastAPI app running at `:8000` with SQLite by default, seeded via `seed.py`.
- **Frontend**: React/Vite app at `:5173` that provides the full coach workflow.
- **Core flow**:
  - Create match → define lineup → live record events + substitutions → finish match → assign coach ratings → review analytics → export CSV.
- **Analytics**:
  - Use timelines, grouped stats, per‑player tables, top‑performer cards, and coach ratings to understand each match both visually and numerically.  

This guide should be enough for a new user to install, run, and effectively use the application without additional explanation.  
For more technical details, see the FastAPI docs at `http://127.0.0.1:8000/docs`.

# Sports Team Management & Match Stats (Bachelor Thesis Project)

Web application for managing a sports team, building match lineups, recording in-match events, and analyzing player/team performance over time.

## Tech stack
- **Backend**: Python, **FastAPI**, SQLAlchemy, SQLite (dev), Alembic (migrations)
- **Frontend**: **React** (Vite), React Router, TanStack React Query, TailwindCSS

## Architecture (high level)
- **React UI** calls a **FastAPI REST API**
- FastAPI persists data via **SQLAlchemy** into **SQLite**
- Match events are stored as an **event log** and also aggregated into per-match player stats for fast reporting

## Run locally

### Backend
From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

Optional: seed a demo dataset (drops and recreates tables):

```bash
python -m app.scripts.seed
```

### Frontend
From `frontend/`:

```bash
npm install
npm run dev
```

App runs at `http://127.0.0.1:5173`.

## Features (what the app provides)
- **Player roster management**: create/list/delete players (import/export will be added)
- **Match history**: create/list matches; start/finish match
- **Lineup creation**: nominate starters/subs and assign match jersey numbers
- **Live match module**: record events (goals, assists, cards, shots, passes, duels, etc.) during a live match
- **Statistics**:
  - per-match aggregated player stats
  - season summaries and “last N matches” reports
- **Coach ratings**: coach assigns post-match performance ratings (to be implemented)
- **Analytics module**: charts + summaries for performance trends over time (to be implemented)

## Backend API overview (selected)
Match & lineup:
- `POST /matches` create match
- `GET /matches` list matches
- `POST /matches/{match_id}/start` set match to live
- `POST /matches/{match_id}/finish` set match to finished
- `GET /matches/{match_id}/lineup-editor` lineup editor payload
- `PUT /matches/{match_id}/lineup` save lineup
- `GET /matches/{match_id}/roster-with-stats` roster + aggregated stats for live UI

Events & stats:
- `POST /matches/{match_id}/events` add event (+1 / -1)
- `GET /matches/{match_id}/events` list events
- `GET /matches/{match_id}/stats` aggregated stats rows

Reports:
- `GET /players/{player_id}/stats/season/{season_id}`
- `GET /players/{player_id}/stats/last/{n}`
- `GET /seasons/{season_id}/team-stats`

## Assignment requirements → implementation mapping
- **Python backend + modern JS frontend**: FastAPI backend (`backend/app/`), React frontend (`frontend/src/`).
- **Sports team management & match statistics**: players, matches, lineup, events, aggregated stats, reports.
- **User authentication under club account + RBAC (coach/assistant)**: will be implemented (users, roles, protected routes).
- **Roster management incl. import/export**: import/export endpoints + UI will be implemented.
- **Lineup creation & match history**: implemented (matches + lineup editor).
- **Real-time event recording module**: implemented backend endpoints; live UI will be rebuilt to record events quickly.
- **Clear results + seasonal stats**: reporting endpoints exist; UI + charts will be added.
- **Coach performance ratings**: will be implemented (ratings model + endpoints + UI).
- **Simple/scalable data layer**: add clear entities (club, user, ratings), constraints, and Alembic migrations.
- **Analytics module with charts**: time-series endpoints + React charts will be added.
- **Testing under real-world conditions**: automated backend tests + a repeatable “mock match” scenario will be added.

## Future enhancements (planned)
- Multi-device live syncing (polling / WebSocket)
- Postgres deployment + indexing
- Multi-club tenancy + richer permission model
- Advanced analytics (composite scores, leaderboards, richer visualizations)

