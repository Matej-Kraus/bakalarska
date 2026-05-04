# Test Report - Trainer App

Datum testovani: 2026-05-04

## Prehled

- Backend testy (`pytest`): **PASS**
- Frontend lint (`eslint`): **PASS**
- Frontend build (`tsc -b && vite build`): **PASS**

## Prostredi

- OS: macOS (darwin 25.0.0)
- Backend: Python 3.14.0, pytest 8.4.2
- Frontend: Vite 7.3.1

## Spustene testy

### 1) Backend - automaticke testy

Prikaz:

`cd backend && source ../.venv/bin/activate && pytest --junitxml ../docs/test-reports/backend-pytest-junit.xml`

Vysledek:

- Collected: 20 testu
- Passed: 20
- Failed: 0
- Cas behu: 55.87 s

Pokryte oblasti:

- autentizace a role (`auth/rbac`)
- klubova API opravnene role
- import/export dat
- sestava a stridani
- live eventy a statistiky
- hodnoceni a analytika
- tymova sezonnni analytika

Artefakty:

- `docs/test-reports/backend-pytest.txt`
- `docs/test-reports/backend-pytest-junit.xml`

### 2) Frontend - lint

Prikaz:

`cd frontend && npm run lint`

Vysledek:

- ESLint probehl bez chyb.

Artefakt:

- `docs/test-reports/frontend-lint.txt`

### 3) Frontend - build

Prikaz:

`cd frontend && npm run build`

Vysledek:

- Build uspesne dokoncen.
- Vite zpracoval 810 modulu.
- Vytvoren produkcni build:
  - `dist/index.html`
  - `dist/assets/index-CjAhZLbN.css`
  - `dist/assets/index-BCA6198R.js`

Poznamka:

- Vite hlasi informativni varovani o velikosti JS chunku (> 500 kB), build je ale validni a uspesny.

Artefakt:

- `docs/test-reports/frontend-build.txt`

## Zaverecne hodnoceni

Na zaklade provedeneho testovani je aplikace v testovanem commitu funkcni:

- backend API prochazi vsemi automatickymi testy,
- frontend nema lint chyby,
- frontend je sestavitelny do produkcni podoby.
