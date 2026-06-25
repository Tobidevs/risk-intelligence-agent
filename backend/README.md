# FilingLens — Backend

FastAPI service for the FilingLens SEC filing risk-intelligence tool.

## Requirements

- Python 3.12

## Setup

```bash
# from backend/
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Optionally copy the example environment file:

```bash
cp .env.example .env
```

## Run

```bash
# from backend/ (venv active)
uvicorn app.main:app --reload --port 8000
```

- API root: http://localhost:8000/
- Health:   http://localhost:8000/health
- Swagger:  http://localhost:8000/docs

## Layout

```
app/
  main.py              # create_app() factory, CORS, router includes
  core/config.py       # pydantic-settings configuration
  api/routes/health.py # GET /health
```

CORS allows the Next.js dev origin (`http://localhost:3000`) by default; adjust
via the `CORS_ORIGINS` environment variable.
