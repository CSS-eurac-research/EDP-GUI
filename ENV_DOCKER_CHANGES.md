# Environment and Docker Changes

This document tracks the local-development hardening and Dockerization changes that were applied to the project.

## What changed

### 1) Environment-based settings (`edp_interface/settings.py`)

- Added helper parsers:
  - `_env_bool(name, default)`
  - `_env_list(name, default)`
- Replaced hardcoded Django values with environment variables:
  - `SECRET_KEY` -> `DJANGO_SECRET_KEY`
  - `DEBUG` -> `DJANGO_DEBUG`
  - `ALLOWED_HOSTS` -> `DJANGO_ALLOWED_HOSTS`
  - `PROXY_ALLOWED_HOSTS` -> `DJANGO_PROXY_ALLOWED_HOSTS`
- Replaced hardcoded database config with env-driven config:
  - `DB_ENGINE`
  - `DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_HOST`
  - `DB_PORT`
- Centralized integration URL configuration in settings:
  - `GEONETWORK_BASE_URL`
  - `EDP_DISCOVERY_URL`
  - `DOI_URL`
  - `OPENEO_URL`
  - `DATA_CITE_API`
  - `GEONETWORK_URL`
  - `GEONETWORK_HARVEST_URL`

### 2) Removed hardcoded DB credentials from app code

#### `main_page/views.py`

- Added `from django.conf import settings`.
- Replaced hardcoded URL constants with settings-backed values.
- Added `_get_db_connection()` that reads DB values from `settings.DATABASES["default"]`.
- Updated `discovery()` DB connection to use `_get_db_connection()`.

#### `main_page/admin.py`

- Added `from django.conf import settings`.
- Added `_get_db_connection()` using `settings.DATABASES["default"]`.
- Replaced hardcoded DB connect values in `download_all_metadata()`.
- Replaced hardcoded GeoNetwork harvest URL with `settings.GEONETWORK_HARVEST_URL`.

### 3) Docker support

#### Added `Dockerfile`

- Uses `python:3.10-slim`.
- Installs GIS/system dependencies needed by GeoDjango:
  - `gdal-bin`
  - `libgdal-dev`
  - `libgeos-dev`
  - `libproj-dev`
  - `proj-data`
  - `proj-bin`
  - `gcc`
- Installs `requirements.txt`.
- Exposes port `8000`.

#### Added `docker-compose.yml`

- `db` service: `postgis/postgis:15-3.4`.
- `web` service: Django runserver on `0.0.0.0:8000`.
- Web service receives env vars for Django, DB, and integration URLs.
- Shared project mount (`.:/app`) for local development.

#### Added `.dockerignore`

- Excludes local venv, git metadata, cache files, and local env files from Docker build context.

### 4) Env template and git ignore hygiene

#### Added `.env.example`

- Includes all required app variables:
  - Django settings
  - DB settings
  - Integration URL settings

#### Updated `.gitignore`

- Added:
  - `.venv/`
  - `.env`
  - `.env.*`
  - `!.env.example`
  - `__pycache__/`
  - `*.pyc`

## New files added

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`
- `ENV_DOCKER_CHANGES.md`

## Files updated

- `edp_interface/settings.py`
- `main_page/views.py`
- `main_page/admin.py`
- `.gitignore`

## How to run with Docker

1. Copy env template:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

2. Build and run containers:

```bash
docker compose up --build
```

3. In another terminal, run migrations:

```bash
docker compose exec web python manage.py migrate
```

4. Open app:

- `http://localhost:8000`

## Notes

- Existing business logic and endpoint contracts were preserved.
- This change set focuses on environment cleanup and local Docker usability.
- Additional hardening (parameterized SQL refactor, request timeouts/retries, test coverage) is still recommended as a follow-up phase.
