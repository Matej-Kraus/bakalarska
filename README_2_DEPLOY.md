# README 2 - Lokal + Server Deploy

Tenhle soubor je samostatny navod. Tvuj puvodni `README.md` zustava beze zmen.

## Cíl

Chces 2 rezimy:

- **Lokalni vyvoj** na tvem pocitaci
- **Produkce** na verejne adrese, dostupna z jakehokoli zarizeni pripojeneho k internetu

---

## 1) Lokalni rezim (vyvoj)

### Backend

V `backend/.env` pouzij lokalni DB:

```env
TRAINERAPP_DATABASE_URL=sqlite:////Users/mates/Bakalarska_prace/backend/app.db
TRAINERAPP_FRONTEND_BASE_URL=http://127.0.0.1:5173
```

Spusteni backendu:

```bash
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

Frontend uz ma nastavenou Vite proxy:

- `frontend/src/api/client.ts` fallback na `/api`
- `frontend/vite.config.ts` proxy `/api -> http://127.0.0.1:8000`

Spusteni frontendu:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Otevri:

- `http://127.0.0.1:5173`

---

## 2) Produkce (server, dostupne odkudkoliv)

Potrebujes 2 verejne URL:

- Frontend URL (napr. `https://bakalarska-1.onrender.com`)
- Backend API URL (napr. `https://xxx.onrender.com`)

Aktualne nasazene URL:

- Frontend: `https://bakalarska-1.onrender.com`
- Backend API: `https://bakalarska.onrender.com`

### Frontend env (Render)

Nastav:

```env
VITE_API_URL=https://bakalarska.onrender.com
```

Po zmene env udelej redeploy frontendu.

### Backend env (Render)

Nastav minimalne:

```env
TRAINERAPP_FRONTEND_BASE_URL=https://bakalarska-1.onrender.com
TRAINERAPP_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
TRAINERAPP_SECRET_KEY=vlastni_silny_secret
```

Po zmene env udelej redeploy backendu.

---

## 3) Proc to pak pobezi na kazdem zarizeni

Kdyz je frontend i backend na verejne URL (HTTPS), tak:

- mobil/tablet/PC jen otevre frontend URL
- frontend vola backend pres `VITE_API_URL`
- backend povoli frontend URL pres `TRAINERAPP_FRONTEND_BASE_URL` (CORS)

To je cele. Zarizeni uz nemusi byt ve stejne lokalni siti.

---

## 4) Rychly test po nasazeni

1. Otevri frontend URL v anonymnim okne
2. Prihlaseni musi projit bez `Network Error`
3. V DevTools -> Network over:
   - requesty jdou na backend URL
   - nejsou CORS chyby
4. Otestuj:
   - vytvoreni hrace
   - vytvoreni zapasu
   - otevreni live zapasu

Aktualni online kontrola (overeno):

- `GET https://bakalarska.onrender.com/health` vraci `200`
- `POST https://bakalarska.onrender.com/auth/login` vraci `200`
- CORS z frontendu `https://bakalarska-1.onrender.com` je povolen

---

## 5) Nejcastejsi problemy

- **Frontend vola localhost v produkci**  
  => spatne nastavene `VITE_API_URL`, nebo chybi redeploy frontendu.

- **CORS chyba**  
  => `TRAINERAPP_FRONTEND_BASE_URL` neodpovida skutecne frontend domene.

- **500 na login/create**  
  => spatna DB URL nebo nedostupna DB.

---

## 6) Doporuceny postup prace

- Vyvoj a test funkcionalit delat lokalne.
- Na server deployovat az po overeni.
- Produkcni env drzet oddelene od lokalniho `backend/.env`.

