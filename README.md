# PaintSWMS

A free SWMS (Safe Work Method Statement) generator for Australian painting jobs, built on the Safe Work Australia model template. The free version shows a watermarked preview. Paying unlocks the full job pack through a Gumroad licence key, and an Unlimited plan is offered after purchase.

## Run locally

    python -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

The app uses SQLite locally. When `DATABASE_URL` is set, it uses Postgres.

## Tests

    pip install httpx
    DB_PATH=/tmp/t.db python test_flow.py

## Deploy

`render.yaml` is a Render Blueprint that sets up a free web service and a free Postgres database. Set these secrets in the Render dashboard: `GUMROAD_ACCESS_TOKEN`, `RESEND_API_KEY`, `MAIL_FROM`, `TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET` (the Turnstile keys are optional).
