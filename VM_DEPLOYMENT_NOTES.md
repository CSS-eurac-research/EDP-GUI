# EDP Web Interface — VM Deployment & Session Notes

**Date:** 25 June 2026  
**Branch:** `feature/developing`  
**Repo:** `git@gitlab-unibz:CSS-DEV/projects/dps4eslab/edp-web-interface-2-0.git`

This document summarizes the UI work, production VM deployment setup, issues encountered on the shared host, and how they were resolved.

---

## 1. UI / Frontend Changes (Figma-aligned redesign)

Django-native UI modernization — no React/SPA migration, no Node build pipeline. Server-rendered templates, jQuery, and Leaflet are unchanged at the backend level.

### Design system (CSS)

New tokenized CSS under `main_page/static/css/`:

| File | Purpose |
|------|---------|
| `tokens.css` | Design tokens (colors, spacing, typography, radii) |
| `base.css` | Global layout (`body.edp-body`, `.edp-main`, skip link) |
| `components.css` | Reusable UI (header, pill buttons, footer, cards) |
| `pages/discovery.css` | Discovery page styles |
| `pages/docs.css` | Documentation list page styles |
| `pages/result_detail.css` | Metadata detail / topic page styles |
| `pages/home.css` | Home page styles |

Palette aligned with Figma exports: `#404649`, `#DF1B12`, Inter font, pill buttons (~30px radius).

### Templates

| File | Change |
|------|--------|
| `edp_interface/templates/base.html` | Full HTML shell; loads tokenized CSS; legacy markup preserved in comments |
| `edp_interface/templates/components/_site_shell_header.html` | Figma-style top bar with nav pills |
| `edp_interface/templates/components/_site_shell_footer.html` | Footer strip |
| `main_page/templates/discovery.html` | Redesigned discovery layout |
| `main_page/templates/docs.html` | Redesigned docs list |
| `main_page/templates/result_detail.html` | Redesigned metadata detail (topic page): pill actions, two-column metadata, snippet code panel, related docs table |

### Static file layout note

- **Source CSS** lives in `main_page/static/css/` (Django app static).
- **Served CSS** in production is copied to `edp_interface/static/css/` by `collectstatic`.
- Legacy vendor assets (Bootstrap, Font Awesome, etc.) remain in `edp_interface/static/` in the repo.

---

## 2. Production / VM Configuration (new or updated files)

### `docker-compose.vm.yml`

VM-specific Compose stack (separate from local `docker-compose.yml`):

- **Project name:** always use `-p edp-dev` for isolation on the shared host.
- **Web:** Gunicorn (3 workers), port `18080:8000`.
- **DB:** PostGIS 15, internal only (no host port 5432).
- **No bind mount** — code baked into image (unlike local dev).
- **`restart: unless-stopped`**
- **`DJANGO_DEBUG=False`** by default.
- **`collectstatic` on startup** (permanent fix for static CSS 404):

```yaml
command: >
  sh -c "python manage.py collectstatic --noinput &&
         gunicorn edp_interface.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"
```

### `.env.vm.example`

Template for VM `.env` — copy to `.env` on the server and fill in secrets.

Key values for the cssdocker VM:

- `WEB_HOST_PORT=18080`
- `DJANGO_ALLOWED_HOSTS` / `DJANGO_PROXY_ALLOWED_HOSTS` include `10.8.244.43`
- `DJANGO_CSRF_TRUSTED_ORIGINS=http://10.8.244.43:18080`
- `EDP_DISCOVERY_URL=http://10.8.244.43:18080/discovery/`

**Do not commit** the real `.env` (secrets).

### `edp_interface/settings.py`

Production-oriented static file serving:

- `whitenoise.middleware.WhiteNoiseMiddleware` (after `SecurityMiddleware`)
- `STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'`
- `CSRF_TRUSTED_ORIGINS` from environment
- `DEBUG`, `ALLOWED_HOSTS`, secrets from environment variables

### `requirements.txt`

Added for VM/production:

- `whitenoise==5.3.0` — serve static files without Nginx
- `gunicorn==22.0.0` — WSGI server
- `setuptools>=65.0` — fixes `ModuleNotFoundError: No module named 'pkg_resources'` with Gunicorn in the slim Python image

### Local dev unchanged

`docker-compose.yml` still uses `runserver`, bind mount `.:/app`, port `8000`, and `DJANGO_DEBUG=True` by default.

---

## 3. VM Environment (`cssdocker`)

| Item | Value |
|------|-------|
| Host | `cssdocker` / `10.8.244.43` |
| User | `hdosku` (Docker requires `sudo`) |
| Clone path | `~/apps/edp-web-interface-2-0` |
| App URL | http://10.8.244.43:18080 |
| Branch | `feature/developing` |

### SSH / Git on VM

- SSH key: `~/.ssh/henri_gitlab`
- `~/.ssh/config` host alias: `gitlab-unibz` → `gitlab.inf.unibz.it`
- GitLab user: `@Henri.Dosku1`

### Docker on shared VM

- System `docker compose` is too old (v2.3.3) for Docker 29.x.
- **Workaround:** personal binary `~/bin/docker-compose` v2.36.2 — use this for all EDP commands.
- **Do not** upgrade system Docker/Compose (other apps depend on current setup).
- Other containers on the host (`django`, `db`, `monitoring`, `redis`, `portainer`, etc.) must not be touched.
- No reverse proxy on ports 80/443 — app exposed directly on `18080`.

---

## 4. Deployment Commands (VM)

```bash
cd ~/apps/edp-web-interface-2-0

# First-time or after code/Dockerfile changes
sudo ~/bin/docker-compose -f docker-compose.vm.yml -p edp-dev up -d --build

# After pull (compose/command/env change only)
sudo ~/bin/docker-compose -f docker-compose.vm.yml -p edp-dev up -d

# Stop
sudo ~/bin/docker-compose -f docker-compose.vm.yml -p edp-dev down

# Start again (DB data preserved in volume)
sudo ~/bin/docker-compose -f docker-compose.vm.yml -p edp-dev up -d
```

### One-time setup (already done on VM)

```bash
cp .env.vm.example .env
# Edit .env: DJANGO_SECRET_KEY, DB_PASSWORD, hosts

sudo ~/bin/docker-compose -f docker-compose.vm.yml -p edp-dev exec web python manage.py migrate
sudo ~/bin/docker-compose -f docker-compose.vm.yml -p edp-dev exec web python manage.py createsuperuser
sudo ~/bin/docker-compose -f docker-compose.vm.yml -p edp-dev exec web python manage.py seed_discovery
```

`collectstatic` runs automatically on every `web` container start (no manual step needed).

### Pull latest code

```bash
git pull origin feature/developing
sudo ~/bin/docker-compose -f docker-compose.vm.yml -p edp-dev up -d
```

If `git pull` fails due to local edits on the VM:

```bash
git diff docker-compose.vm.yml   # inspect
git checkout -- docker-compose.vm.yml   # discard VM-only edits if remote is correct
git pull origin feature/developing
```

---

## 5. Issues Encountered & Fixes

### Docker Compose API too old

**Symptom:** `compose` fails with Docker API version errors.  
**Fix:** Use `sudo ~/bin/docker-compose` (v2.36.2), not system `docker compose`.

### Gunicorn crash — `pkg_resources` missing

**Symptom:** `ModuleNotFoundError: No module named 'pkg_resources'`.  
**Fix:** Add `setuptools>=65.0` to `requirements.txt`, rebuild image.

### Static files 404 (`/static/css/components.css`)

**Symptom:** Homepage returns 200, but new UI CSS returns 404.  
**Diagnosis:**

- WhiteNoise worked (`/static/style.css` → 200).
- `main_page/static/css/` existed in the container.
- `edp_interface/static/css/` did **not** exist — `collectstatic` had not been run (or was lost after container recreate).

**Fix (immediate):** Run `collectstatic`, restart `web`.  
**Fix (permanent):** Run `collectstatic` before Gunicorn in `docker-compose.vm.yml` `command` (see section 2).

### Git pull blocked on VM

**Symptom:** Local edits to `docker-compose.vm.yml` on VM blocked merge.  
**Fix:** Revert local file (`git checkout -- docker-compose.vm.yml`) or stash, then pull.

---

## 6. Verification

```bash
# App responds
curl -I http://127.0.0.1:18080

# Static CSS (should be 200)
curl -I http://127.0.0.1:18080/static/css/components.css
curl -I http://127.0.0.1:18080/static/css/tokens.css

# Containers
sudo ~/bin/docker-compose -f docker-compose.vm.yml -p edp-dev ps
```

Expected containers:

- `edp-dev-web-1` — `0.0.0.0:18080->8000/tcp`
- `edp-dev-db-1` — `5432/tcp` (internal only)

Browser: http://10.8.244.43:18080

---

## 7. Data / Content Still Empty on VM

Same as local unless populated manually:

| Model | Effect when empty |
|-------|-------------------|
| `SnippetCode` | Snippet code section hidden on detail/openEO pages |
| `DocSource` | No related documentation links on detail pages |

Discovery metadata was seeded: **385 records** via `seed_discovery`.

Admin: http://10.8.244.43:18080/admin/ (superuser `admin` created on VM).

---

## 8. Files Not to Commit

- `.env` (real secrets on VM)
- `figmacode_edp/` (Figma export reference files, untracked)

---

## 9. Architecture Summary

```
Browser → http://10.8.244.43:18080
       → Gunicorn (edp-dev-web-1)
       → Django + WhiteNoise (static from edp_interface/static/)
       → PostGIS (edp-dev-db-1, Docker network only)
```

**Static file flow on container start:**

1. `collectstatic` copies `main_page/static/` → `edp_interface/static/`
2. Gunicorn starts; WhiteNoise indexes `STATIC_ROOT`
3. Requests to `/static/...` served by WhiteNoise

---

## 10. Next Steps (optional)

- Verify all pages in browser from laptop (discovery, docs, detail, home)
- Merge `feature/developing` → `main` when ready (does not affect upstream original repo if forked)
- Consider separating `STATIC_ROOT` to `/app/staticfiles` and `STATICFILES_DIRS` for `edp_interface/static` (cleaner long-term)
