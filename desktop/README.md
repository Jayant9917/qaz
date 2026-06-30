# NOVO Desktop Assistant

E2.5 desktop shell for NOVO. This is the local daily-use assistant surface. The current UI is a PySide6 modern assistant console with glass panels, animated orb, chat bubbles, live status, and streaming response display. The existing Next.js app remains the Control Center for governance, permissions, audit, settings, and recovery.

## What exists now

- PySide6 desktop window with modern glass-panel layout and NOVO animated status orb.
- Backend health check against `http://localhost:8000/health/live`.
- Owner login through the existing backend auth API.
- Cookie and CSRF-aware backend client.
- New conversation creation through the governed backend.
- Text message send through the existing E2 conversation API.
- SSE response stream display in the desktop transcript.
- Voice/push-to-talk placeholders with pulsing microphone UI for the next E2.5 slice.
- Control Center launcher for the web dashboard.

## Run

Start the backend first from `backend/`:

```powershell
python -m uvicorn novo.main:app --reload --app-dir src
```

Then run the desktop app from the repository root:

```powershell
python desktop\run.py
```

## Boundary

The desktop app is a client. It must not bypass backend permissions, audit, memory, RAG, tools, credentials, model routing, or kill switch behavior.

## Next E2.5 slice

- Add real push-to-talk capture.
- Add speech-to-text adapter interface.
- Add text-to-speech adapter interface.
- Add cancellable streaming.
- Add persisted local desktop settings without storing secrets.
## UI dependencies

The modern desktop shell uses:

- PySide6
- Pillow
- psutil
- qtawesome and markdown are installed for upcoming icon/markdown rendering improvements

If the GUI packages are missing, install them with:

```powershell
python -m pip install PySide6 qtawesome markdown Pillow psutil
```