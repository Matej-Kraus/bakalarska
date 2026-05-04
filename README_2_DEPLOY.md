# README 2 - Kompletní technicka dokumentace projektu (podklad pro BP)

Tento dokument slouzi jako:

- provozni manual aplikace
- souhrn implementace a oprav
- podklad pro kapitoly bakalarske prace

Puvodni `README.md` zustava beze zmen. Tento soubor je rozsirena verze "co, proc, jak".

---

## 1) Cile projektu

Hlavni cil byl dodelat a stabilizovat webovou aplikaci pro fotbalovy tym tak, aby:

1. spolehlive bezela lokalne (vyvoj),
2. byla nasaditelna na verejny server,
3. fungovala na libovolnem internetovem zarizeni (PC/mobil/tablet),
4. poskytovala pouzitelna data pro analytiku,
5. mela realisticky demo obsah pro prezentaci/obhajobu.

---

## 2) Architektura aplikace

### 2.1 Technologie

- Frontend: React + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy
- Migrace DB: Alembic
- Lokalni DB: SQLite
- Produkcni DB: PostgreSQL (Render)
- Testovani backendu: pytest
- Kvalita frontendu: ESLint + production build

### 2.2 Logicka struktura

- `frontend/`:
  - stranky (`src/pages/*`)
  - API klient (`src/api/*`)
  - autentizace (`src/auth/*`)
  - UI komponenty (`src/components/*`)
- `backend/`:
  - routy API (`app/api/routes/*`)
  - modely (`app/models/*`)
  - schema (`app/schemas/*`)
  - business logika (`app/services/*`)
  - skripty pro seed/simulaci (`app/scripts/*`)

### 2.3 Datovy tok

1. Uzivatel otevre frontend.
2. Frontend vola backend API.
3. Backend validuje uzivatele (JWT), role a data.
4. Backend uklada/vraci data z DB.
5. Frontend zobrazi data (tabulky, grafy, evaluace, analytika).

---

## 3) Produkcni a lokalni URL

Aktualni produkce:

- Frontend: `https://bakalarska-1.onrender.com`
- Backend API: `https://bakalarska.onrender.com`

Lokalni vyvoj:

- Frontend: `http://127.0.0.1:5173` (nebo aktualni Vite port)
- Backend: `http://127.0.0.1:8000`

---

## 4) Chronologie problemu a jak byly vyreseny

Tato sekce je dulezita do BP (kapitola implementace + ladeni).

### 4.1 Problem: "Network Error" mezi frontendem a backendem lokalne

Pricina:

- frontend smeroval API volani na nevhodnou adresu pro aktualni lokalni setup.

Reseni:

- `frontend/src/api/client.ts` fallback `baseURL` zmenen na `/api`
- `frontend/vite.config.ts` doplnen proxy:
  - `/api -> http://127.0.0.1:8000`
  - `rewrite` odstraneni prefixu `/api`

Prinos:

- frontend vola backend stabilne i bez explicitniho hardcodu localhost URL.

### 4.2 Problem: Login vracel `500`

Pricina:

- lokalni backend mel v `.env` produkcni PostgreSQL URL (nedostupne lokalne).

Reseni:

- prepnuto na lokalni SQLite:
  - `TRAINERAPP_DATABASE_URL=sqlite:////Users/mates/Bakalarska_prace/backend/app.db`

Prinos:

- lokalni login a dalsi API operace prestaly padat na DB connectivity.

### 4.3 Problem: Duplicitni cisla dresu v jedne sezone

Pricina:

- chybel business constraint na backendu a UX guard na frontendu.

Reseni:

- backend validace v `backend/app/api/routes/players.py` (conflict pri duplicite)
- frontend validace v `frontend/src/pages/PlayersPage.tsx`:
  - disable tlacitka "Pridat hrace"
  - chybova hlaska pro uzivatele
- test doplnen v `backend/tests/test_auth_rbac.py`

Prinos:

- konzistence dat sezony, odstraneni chybnych vstupu.

### 4.4 Problem: Nejasna/neudrzitelna demo data zapasu

Pricina:

- puvodni generovani neodpovidalo realistictejsim benchmarkum podle pozic.

Reseni:

- vyznamne prepracovan `sim_match_core_v2.py`:
  - zavedena `MatchProfile` (tempo, aggression, passing_quality, finishing, error_rate)
  - position-aware rozdeleni statistik (GK/DF/MF/FW)
  - realisticke rozsahy:
    - prihravky
    - souboje
    - strely
    - goly
    - fauly
    - zisky/ztraty
  - generovani neuspesnych prihravek
- upraven orchestracni skript `generate_full_match_timelines.py`
- cilem je 20 zapasu na sezonu

Prinos:

- demonstracni data jsou variabilni a blizsi realnemu fotbalu.
- analytika ma smysluplnejsi vstup.

### 4.5 Problem: Sezonni hodnoceni hracu se zobrazovalo jako `-`

Pricina:

- leaderboard pocital prumer jen z rucnich coach ratings.
- pokud rating nebyl zadan, vysledek byl `None`.

Reseni:

- v `backend/app/api/routes/analytics.py` doplnen fallback:
  - pokud neni coach rating, vypocita se auto rating ze statistik
- frontend `AnalyticsPage` doplnen o souhrn:
  - prumer sezony
  - nejlepsi zapas
  - nejhorsi zapas

Prinos:

- hodnoceni je viditelne i bez manualniho hodnoceni kazdeho zapasu.

### 4.6 Problem: Pady stranky vyhodnoceni zapasu

Symptom:

- `Uncaught ReferenceError: Cannot access 'timeline' before initialization`

Pricina:

- spatne poradi `useMemo` zavislosti v `MatchEvaluationPage.tsx`.

Reseni:

- opraveno poradi vypoctu dat
- opravene tooltip typy a fallback hodnoty

Prinos:

- stranka vyhodnoceni se stabilne nacita bez runtime padu.

### 4.7 Problem: Vizualni neprehlednost grafu "Souboje a disciplina"

Prubeh:

- probahlo vice iteraci grafu podle UX feedbacku.

Konecne reseni:

- navrat na timeline styl konzistentni s ostatnimi grafy
- fauly barevne odlisene (zelena dle pozadavku)

Prinos:

- konzistentni vzhled a citelnost napric analytikou po zapase.

### 4.8 Problem: Testy padaly po rozsireni seedu

Pricina:

- seed puvodne vytvarel jen coach ucet
- schema role v auth odpovedi akceptovalo pouze `coach`
- lineup test vyzadoval hrace navazane na sezonu

Reseni:

- `seed.py` doplnen:
  - ucet `assistant@demo.local / assistant`
  - vazba hracu do `season_players`
- `backend/app/schemas/auth.py` upraveno:
  - role `Literal["coach", "assistant"]`

Prinos:

- backend test suite je opet plne zelena.

---

## 5) Implementovane funkcionalni zmeny po modulech

### 5.1 Backend

- Autentizace:
  - validni role `coach` + `assistant`
- Hráci:
  - kontrola duplicitnich cisel dresu v jedne sezone
- Analytika:
  - fallback auto ratingu v leaderboards
- Seed:
  - coach + assistant account
  - navazani hracu na sezonu
- Simulace:
  - realisticke pozicni statistiky a timeline eventy

### 5.2 Frontend

- API klient:
  - `/api` fallback a Vite proxy
- Players:
  - klientska validace duplicitniho dresu
- Analytics:
  - sezonni souhrn hodnoceni hrace
  - odstraneni lint anti-patternu `setState-in-effect` pres odvozeny stav
- Match Evaluation:
  - opraven runtime bug `timeline`
  - sjednocene grafy a citelnejsi "Souboje a disciplina"

### 5.3 Testy

- backend test doplnen o overeni duplicate jersey validace
- kompletni regression pass po opravach

---

## 6) Lokalni setup - presny postup

### 6.1 Backend env (`backend/.env`)

```env
TRAINERAPP_DATABASE_URL=sqlite:////Users/mates/Bakalarska_prace/backend/app.db
TRAINERAPP_FRONTEND_BASE_URL=http://127.0.0.1:5173
```

### 6.2 Spusteni backendu

```bash
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 6.3 Spusteni frontendu

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

### 6.4 Prihlasovaci udaje (demo)

- `coach@demo.local / coach`
- `assistant@demo.local / assistant`

---

## 7) Produkcni nasazeni (Render)

### 7.1 Frontend env

```env
VITE_API_URL=https://bakalarska.onrender.com
```

### 7.2 Backend env

```env
TRAINERAPP_FRONTEND_BASE_URL=https://bakalarska-1.onrender.com
TRAINERAPP_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
TRAINERAPP_SECRET_KEY=vlastni_silny_secret
```

### 7.3 Deploy flow

1. lokalni testy
2. commit + push na `main`
3. Render build/deploy
4. produkcni smoke test

### 7.4 Overeni dostupnosti

- `GET /health` backend vraci `200`
- frontend URL vraci `200`

---

## 8) Testovani - co je ulozeno do repozitare

Reporty:

- `docs/test-reports/backend-pytest-junit.xml`
- `docs/test-reports/backend-pytest.txt`
- `docs/test-reports/frontend-lint.txt`
- `docs/test-reports/frontend-build.txt`
- shrnuti `docs/TEST_REPORT.md`

Aktualni vysledek:

- Backend: `20 passed`
- Frontend lint: pass
- Frontend build: pass

---

## 9) Cleanup repozitare (co bylo odstraneno)

Odstranene zbytecnosti:

- `.DS_Store`, cache/temp artefakty, stare scripts
- nepouzivane obrazky/sablony
- nepouzite front-end assety

Zprisnen `.gitignore`:

- Python cache a coverage artefakty
- virtualenv slozky
- frontend build/install artefakty
- log soubory

Cil:

- repozitar obsahuje jen zdrojaky, dokumentaci a relevantni test artefakty.

---

## 10) Troubleshooting (prakticke chyby)

### Frontend vola localhost v produkci

- zkontrolovat `VITE_API_URL`
- udelat redeploy frontendu

### CORS chyba

- zkontrolovat `TRAINERAPP_FRONTEND_BASE_URL` na backendu

### 500 na login/API

- zkontrolovat DB URL a dostupnost DB

### Zmeny nejsou videt v produkci

- overit push na `origin/main`
- overit probehly deploy na Renderu

### Frontend stale ukazuje starou verzi

- hard refresh / anonymni okno
- restart dev serveru

---

## 11) Co pouzit do bakalarske prace (doporucěne kapitoly)

Tento dokument lze primo rozdelit do BP:

1. **Analyza problemu**
   - oddelene frontend/backend URL
   - CORS a API routing
2. **Navrh reseni**
   - proxy, env konfigurace, role model
3. **Implementace**
   - validace dresu
   - seed + simulace
   - analytika rating fallback
   - vizualni upravy a fix runtime chyb
4. **Testovani**
   - pytest + lint + build
   - ulozene reporty v `docs/test-reports`
5. **Nasazeni**
   - Render konfigurace
   - produkcni smoke test
6. **Zaver**
   - funkcni aplikace lokalne i produkcne
   - realisticka demo data
   - cistejsi repozitar a udrzitelny workflow

---

## 12) Finalni stav projektu

Projekt je v tomto stavu:

- funkcni lokalni vyvoj
- funkcni produkcni deployment
- stabilni autentizace a role
- konzistentni data (validace dresu)
- realisticka demo sezona
- opravena analytika a evaluace
- ulozene test reporty pro dokumentaci
- vycisteny repozitar

Tento soubor je urcen jako hlavni orientacni dokument pro dalsi psani BP i finalni predani projektu.

---

## 13) Provozni zaznam - produkcni pregenerovani dat

Datum: 2026-05-04

Provedene kroky:

- backend byl nasazen na aktualni commit s endpointem pro vzdaleny run generovani
- produkcni sezona `id=3` byla pregenerovana pres API po davkach (bez pristupu do server shellu)
- behem procesu byly dodelany kompatibilni opravy pro starsi produkcni DB (vazby `season_players`, odolne mazani zavislych dat)

Overeny vysledek:

- v produkci je v sezone `id=3` celkem `20` zapasu
- leaderboard endpoint vraci `avg_rating` bez `null` hodnot (`null_avg = 0`)
- frontend i backend endpointy jsou dostupne (`HTTP 200`)

Prakticka poznamka:

- pri kontrole v prohlizeci je vhodne provest tvrdy refresh (`Ctrl/Cmd + Shift + R`), aby se neprojevila stara cache.

