# Scientific Methodology Extractor

A Django application for turning life-science research PDFs into traceable, machine-readable methodology workflows. Phase 3 adds rule-based detection of methodology-relevant sections with retained source boundaries.

## Architecture

- `config/`: Django, WSGI, Celery configuration.
- `papers/`: upload and paper-record domain.
- `extraction/`: reserved boundary for parsers, structured extraction, workflow reconstruction, evidence, and reproducibility modules.

## Local setup

1. Copy `.env.example` to `.env` and set values as appropriate. Production requires `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=False`.
2. `python -m pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py runserver`

Use `DATABASE_URL` to select PostgreSQL. If it is unset, development uses SQLite.

## Docker startup

The production image starts through `entrypoint.sh`, which runs `python manage.py migrate --noinput` before executing the existing Gunicorn command. A migration failure stops startup, preventing Gunicorn from serving against an incomplete schema.

Optionally configure `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, and `DJANGO_SUPERUSER_PASSWORD` together. The startup command creates the account only when it does not already exist and never logs the password.

## Render deployment

Create a Docker Web Service from this repository and attach a Render PostgreSQL database as `DATABASE_URL`. The image runs migrations and optional superuser initialization before Gunicorn. Render supplies `PORT`; the container binds it automatically. Configure `DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and `DJANGO_CSRF_TRUSTED_ORIGINS` for the service URL. Uploaded PDFs use local media storage, which is ephemeral on Render; use durable object storage before relying on uploads across redeploys.

## Current endpoints

- `/` dashboard
- `/papers/upload/` upload form
- `/admin/` Django admin
- `/api/papers/` list endpoint

## Parse an uploaded paper

Run `python manage.py parse_paper <paper-uuid>`. The same operation is available as `extraction.tasks.parse_paper_task` for Celery workers.

After parsing, run `python manage.py detect_sections <paper-uuid>` to persist recognized Methods, study-design, bioinformatics, statistical-analysis, and data/code-availability sections.

## Structured extraction

Set `OPENAI_API_KEY` in the server environment before enabling extraction. The Phase 4 service uses strict JSON-schema output plus Pydantic validation and requires evidence for every extracted entity; it does not invent absent parameters.
