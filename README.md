# AI Hardware Architect

AI Hardware Architect is a multi-agent PC builder assistant with a Flask + SocketIO UI, RAG-backed component search, database persistence, and optional Discord notifications.

## Requirements

- Python 3.14 or newer
- `uv`
- MySQL running locally on `localhost:3306` or another configured host
- A Groq API key
- Optional: a Discord webhook URL for build notifications

## Setup

1. Clone the repository.
2. Create your local environment file:

   - Copy `.env.example` to `.env`
   - Fill in your real values

3. Install dependencies:

   - `uv sync`

4. Initialize the database:

   - `uv run python database/init_db.py`

## Run locally

Use the interface you want:

- Main Flask + SocketIO app: `uv run python app.py`

On Windows, you can also use the helper scripts:

- `run_app.bat`
- `setup_database.bat`

## Environment variables

The repository ships with `.env.example` only. Copy it to `.env` and set these values:

- `GROQ_API_KEY`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DISCORD_WEBHOOK_URL`
- `SECRET_KEY`

If you do not use Discord notifications, leave `DISCORD_WEBHOOK_URL` empty.