# Jay AI — Windows Personal Assistant

Jay AI is being developed as an installable Windows desktop application.

## Development
- Python and PySide6 desktop interface
- Home chat screen
- Personalization settings with saved theme preference
- Planned: AI integration, voice, news, weather, Windows installer,
  automatic updates, and Android integration

## Run locally
Install Python 3.11 or newer, then run:

    python -m pip install -r requirements.txt
    python -m app.main

## Enable AI chat
Copy `.env.example` for reference and set `JAY_ANTHROPIC_API_KEY` (and optionally the
`JAY_OPENAI_*` variables) as environment variables before launching. Without a key the
app shows "AI not connected" and chat returns a clear error. Never commit real keys.
A key in a desktop environment variable is a stopgap; the planned design keeps keys on a backend.

## Tests
    python -m unittest discover -s tests -v

Provider tests use mocks only; they do not prove a live provider works.
