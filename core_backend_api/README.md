# Concept Quest - Backend (FastAPI)

This container provides the API for games, progress tracking, achievements, and syllabus mappings.

## Running (preview/local)

- Backend runs on port **3001**
- Database container runs Postgres on port **5000** internally (viewer on 5001)

### Environment variables

Set via orchestrator `.env` (do not hardcode secrets):

- `POSTGRES_URL` (recommended)
  - Example: `postgresql://appuser:dbuser123@localhost:5000/myapp`

If `POSTGRES_URL` is not set, the backend falls back to the template-local connection shown above so previews work.

## What it provides

- Health: `GET /`
- Auth (placeholder):
  - `POST /auth/signup`
  - `POST /auth/login`
  - `POST /auth/logout` (no-op)
- Games:
  - `GET /games`
  - `POST /games/start`
  - `POST /games/submit`
- Progress:
  - `GET /progress/{user_id}`
  - `GET /achievements/{user_id}`
- Syllabus:
  - `GET /syllabus/mappings?game_id=&subject=`

## Notes

- Tables are created automatically on startup via `create_all` as a migrations fallback.
- Seed data is inserted on startup (idempotent).
- CORS is enabled for the React dev server (port 3000).
