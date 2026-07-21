# HOS Trip Planner & ELD Log Generator

A full-stack web application that plans multi-day truck routes under FMCSA Hours-of-Service (HOS) regulations and automatically generates compliant ELD-style daily log sheets. Built with **Django REST Framework** on the backend and **React (Vite)** on the frontend, with live map search, routing, and interactive drive/rest scheduling.

**Live demo:** https://hos-eld-trip-planner-ten.vercel.app

---

## Overview

Drivers and dispatchers input a trip (current location, pickup, dropoff, and current cycle hours used), and the app returns:

- An optimized route with turn-by-turn instructions and distance/duration estimates.
- A full HOS-compliant schedule covering driving, breaks, fuel stops, and rest periods.
- FMCSA-style daily log sheets (24-hour duty graphs) ready to print, save as PDF, or export as JSON.

## Features

- **Trip planning API** — accepts current location, pickup, dropoff, and current cycle hours used.
- **HOS rule engine**
  - 11-hour driving limit per shift
  - 14-hour on-duty shift window
  - Mandatory 30-minute break after 8 cumulative driving hours
  - 70-hour / 8-day cycle tracking
  - 34-hour restart when the cycle limit is exhausted
  - Fuel stops every 1,000 miles, plus 1-hour pickup/dropoff windows
- **FMCSA daily logs**
  - 24-hour duty status graph with 15-minute grid resolution
  - Full metadata (driver number/initials, home terminal, tractor/trailer numbers, shipper, commodity, load ID)
  - Per-day and cumulative duty totals
  - Print/save as PDF or download as JSON
- **Interactive map**
  - Drag, pan, and zoom
  - Click-to-pick locations
  - Address/city or lat/lon search with keyboard-navigable autocomplete suggestions
  - English-only results for consistent output
- **Resilient by design** — falls back to known city coordinates, coordinate parsing, or straight-line distance estimates if external geocoding/routing services are briefly unreachable.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6, Django REST Framework, django-cors-headers, Gunicorn, WhiteNoise |
| Frontend | React 19, Vite, react-leaflet / Leaflet |
| Mapping & Routing | OpenStreetMap Nominatim (geocoding), OSRM (routing) |
| Hosting | Railway (backend), Vercel (frontend) |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Service health check |
| POST | `/api/plan-trip` | Generate a route + HOS schedule + daily logs |
| GET | `/api/reverse-geocode?lat=&lon=` | Reverse geocode coordinates to an address |
| GET | `/api/geocode?q=` | Geocode a search query |
| GET | `/api/geocode-suggest?q=` | Autocomplete suggestions for a search query |

## Local Development

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Runs at `http://127.0.0.1:8000`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173`.

## Environment Variables

**Backend** — see [backend/.env.example](backend/.env.example)

- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SECRET_KEY`
- `DJANGO_CORS_ALLOWED_ORIGINS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

**Frontend** — see [frontend/.env.example](frontend/.env.example)

- `VITE_API_BASE_URL`

## Testing

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py test
```

```powershell
cd frontend
npm run build
```

## Deployment

- **Backend** is deployed on [Railway](https://railway.app) using [backend/Procfile](backend/Procfile) (Gunicorn WSGI server).
- **Frontend** is deployed on [Vercel](https://vercel.com), built from the `frontend/` directory with `VITE_API_BASE_URL` pointed at the live backend.

## Project Structure

```
backend/    Django project (API, HOS engine, geocoding/routing services)
frontend/   React + Vite single-page application
```

