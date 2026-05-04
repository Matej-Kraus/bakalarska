# README 2 - Kompletní provozni manual projektu

Tento soubor je samostatna dokumentace k projektu. Puvodni `README.md` zustava beze zmen.

## 1) Co je to za aplikaci

Trainer App je webova aplikace pro fotbalovy tym:

- sprava hracu a sezony
- planovani zapasu a sestavy
- live zapis udalosti zapasu
- pozapasova evaluace a analytika
- registrace a prihlaseni uzivatele (coach/assistant role)

Architektura:

- Frontend: React + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy + Alembic
- Lokalni DB: SQLite
- Produkcni DB: PostgreSQL

## 2) Co je v projektu dodelane (dulezite zmeny)

### Stabilita a infrastruktura

- Opraveno lokalni API napojeni pres Vite proxy:
  - `frontend/src/api/client.ts` ma fallback na `/api`
  - `frontend/vite.config.ts` proxy `/api -> http://127.0.0.1:8000`
- Opraveny login 500 error v lokalnim behu pres spravne DB nastaveni.

### Uzivatele a role

- Seed vytvari oba ucty:
  - `coach@demo.local / coach`
  - `assistant@demo.local / assistant`
- Opraveno API schema tak, aby role `assistant` byla validni i v odpovedi auth endpointu.

### Hráci a validace

- Implementovana server-side validace proti duplicitnimu cslu dresu ve stejne sezone.
- Implementovana i client-side validace v `PlayersPage` (tlacitko je zablokovane + hlaska).

### Demo data a simulace zapasu

- Prepracovana simulace sezony do realistickejsi podoby:
  - position-aware statistiky (GK/DF/MF/FW)
  - variabilita zapasu pres match profile (tempo/agresivita/finishing/chybovost)
  - realisticke rozsahy prihravek, souboju, strel, faulu, zisku/ztrat
  - neuspesne prihravky jsou generovany a promitaji se do analytiky
- Sezona je nastavena na 20 zapasu.

### Analytika a UI

- Dodelan fallback sezonnich hodnoceni hracu:
  - pokud neni coach rating, pouzije se automaticky rating vypocteny ze statistik
- Upraveno automaticke hodnoceni tak, aby nebylo zbytecne prisne.
- Opravena stranka vyhodnoceni po zapase (`timeline before initialization` bug).
- Graf "Souboje a disciplina" vracen do konzistentniho timeline stylu jako ostatni grafy.

### Uklid projektu

- Smazane zastarale/nevuzite soubory (stare scripts, temporary soubory, sablony).

## 3) Lokalni beh (development)

### 3.1 Backend env (`backend/.env`)

Pouzij lokalni SQLite:

```env
TRAINERAPP_DATABASE_URL=sqlite:////Users/mates/Bakalarska_prace/backend/app.db
TRAINERAPP_FRONTEND_BASE_URL=http://127.0.0.1:5173
```

### 3.2 Spusteni backendu

```bash
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3.3 Spusteni frontendu

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Otevri:

- `http://127.0.0.1:5173`

### 3.4 Lokalni test useri

- coach: `coach@demo.local / coach`
- assistant: `assistant@demo.local / assistant`

## 4) Testovani a reporty (pro BP)

Testy jsou ulozeny do:

- `docs/test-reports/backend-pytest-junit.xml`
- `docs/test-reports/backend-pytest.txt`
- `docs/test-reports/frontend-lint.txt`
- `docs/test-reports/frontend-build.txt`
- shrnuti: `docs/TEST_REPORT.md`

Aktualni vysledek:

- Backend pytest: 20 passed
- Frontend lint: pass
- Frontend build: pass

## 5) Produkce (Render) - jak to bezi na internetu

Aktualni URL:

- Frontend: `https://bakalarska-1.onrender.com`
- Backend API: `https://bakalarska.onrender.com`

### 5.1 Frontend env (Render)

```env
VITE_API_URL=https://bakalarska.onrender.com
```

### 5.2 Backend env (Render)

```env
TRAINERAPP_FRONTEND_BASE_URL=https://bakalarska-1.onrender.com
TRAINERAPP_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
TRAINERAPP_SECRET_KEY=vlastni_silny_secret
```

### 5.3 Proc to funguje na kazdem zarizeni

- Uzivatel otevre jen frontend URL.
- Frontend vola backend pres verejnou URL (`VITE_API_URL`).
- Backend povoli frontend domenu pres CORS (`TRAINERAPP_FRONTEND_BASE_URL`).

Neni potreba byt ve stejne lokalni siti.

## 6) Deploy checklist (po kazde velke zmene)

1. Lokalni testy: `pytest`, `npm run lint`, `npm run build`
2. Commit + push do `main`
3. Render redeploy backend + frontend (pokud se nespusti automaticky)
4. Smoke test produkce:
   - login
   - vytvoreni hrace
   - vytvoreni/otevreni zapasu
   - analytika a hodnoceni

## 7) Nejčastejsi problemy a rychle reseni

- Frontend v produkci vola localhost:
  - zkontroluj `VITE_API_URL`, pak redeploy frontend.
- CORS chyba:
  - zkontroluj `TRAINERAPP_FRONTEND_BASE_URL` na backendu.
- 500 na login nebo API:
  - over `TRAINERAPP_DATABASE_URL` a dostupnost DB.
- Na produkci chybi nove zmeny:
  - over posledni commit na `origin/main` a probehly deploy.

## 8) Doporuceny provozni postup

- Vyvijet lokalne, nasazovat az po uspesnych testech.
- Drzet oddelene lokalni a produkcni `.env`.
- U kazde verze ulozit test report do `docs/test-reports`.
- Pred odevzdanim BP spustit finalni smoke test na produkcni URL.

