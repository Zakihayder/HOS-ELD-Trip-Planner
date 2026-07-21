# Fullstack Developer Assessment - HOS Trip Planner

This project is a full-stack Django + React application for trip planning with HOS compliance logic and FMCSA-style daily log rendering.

## Completed functionality

- Trip planning API with required inputs:
  - current location
  - pickup location
  - dropoff location
  - current cycle used hours
- HOS rule engine:
  - 11-hour driving limit
  - 14-hour shift window
  - 30-minute break after 8 cumulative driving hours
  - 70-hour / 8-day cycle handling
  - 34-hour restart when cycle limit is exhausted
- FMCSA daily logs:
  - 24-hour duty graph data
  - 15-minute grid increments in visualization
  - required metadata fields
  - remarks and totals (24h)
  - driver/truck/shipment details (driver number, initials, home terminal, tractor/trailer, shipper, commodity, load ID)
- Real map interaction:
  - pan/drag
  - zoom controls
  - click-to-pick locations
- Search and suggestions:
  - search by address/city or lat,lon
  - autocomplete-style suggestions
  - keyboard support (arrow up/down, enter, escape)
- English-only suggestion/lookup preference (`Accept-Language: en`)
- Offline fallback behavior when geocode/route services are unreachable:
  - known city fallback
  - coordinate parsing fallback
  - straight-line route fallback
- Frontend utility actions:
  - backend health badge + recheck
  - print/save PDF for daily logs
  - download logs JSON

## API endpoints

- `GET /api/health`
- `POST /api/plan-trip`
- `GET /api/reverse-geocode?lat=..&lon=..`
- `GET /api/geocode?q=...`
- `GET /api/geocode-suggest?q=...`

## Local setup

## Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Backend URL: `http://127.0.0.1:8000`

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## Environment variables

## Backend

See [backend/.env.example](backend/.env.example)

- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SECRET_KEY`
- `DJANGO_CORS_ALLOWED_ORIGINS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

## Frontend

See [frontend/.env.example](frontend/.env.example)

- `VITE_API_BASE_URL`

## Tests and validation

## Backend tests

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py test
```

## Frontend build

```powershell
cd frontend
npm run build
```

## Deployment-ready files

- [backend/Procfile](backend/Procfile)
- [render.yaml](render.yaml)

## Final submission checklist

- Deploy backend and frontend publicly
- Set `VITE_API_BASE_URL` to deployed backend URL
- Verify end-to-end planning on live site
- Record and share 3-5 minute Loom walkthrough
- Share GitHub repository + live URL + Loom URL
