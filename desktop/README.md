# NOVO Desktop Assistant

E2.5 desktop shell for NOVO. This is the local daily-use assistant surface. The existing Next.js app remains the Control Center for governance, permissions, audit, settings, and recovery.

## What exists now

- Tkinter desktop window with NOVO status orb.
- Backend health check against `http://localhost:8000/health/live`.
- Owner login through the existing backend auth API.
- Cookie and CSRF-aware backend client.
- New conversation creation through the governed backend.
- Text message send through the existing E2 conversation API.
- SSE response stream display in the desktop transcript.
- Voice/push-to-talk placeholders for the next E2.5 slice.
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