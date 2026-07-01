# NOVO Desktop Assistant

E2.5 desktop shell for NOVO. This is the local daily-use assistant surface. The current UI is a PySide6 modern assistant console with glass panels, animated orb, chat bubbles, live status, and streaming response display. The selected NOVO voice profile is Piper with the female English model `en_US-amy-medium`, tuned to speak a little faster, and the desktop shell can already synthesize and play sample voice output. The faster-whisper STT runtime now auto-detects CUDA, validates the CUDA runtime during warm-up, retries on CPU if the CUDA runtime fails, and defaults to `small.en` with `en` transcription. Voice, backend, and streaming failures now log the exact exception and traceback to the terminal while the UI shows a safe NOVO-facing message. The existing Next.js app remains the Control Center for governance, permissions, audit, settings, and recovery.

## What exists now

- PySide6 desktop window with modern glass-panel layout and NOVO animated status orb.
- Backend health check against `http://localhost:8000/health/live`.
- Owner login through the existing backend auth API.
- Cookie and CSRF-aware backend client.
- New conversation creation through the governed backend.
- Text message send through the existing E2 conversation API.
- SSE response stream display in the desktop transcript.
- Real push-to-talk microphone capture with local transcription.
- Sample voice playback through Piper in the Qt desktop shell.
- Stop/interruption control for voice playback and assistant response streaming.
- Voice and backend request errors log the exact exception and traceback to the desktop terminal while the UI shows a safe user message.
- Safe local desktop settings persist backend URL, email, and window size without storing secrets.
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

## Next voice work

- Add wake word and always-on listening after the security/privacy model is ready.
- Add richer microphone error recovery and retry UI.
- Add optional voice profile selection UI.
- Add more nuanced interruption controls for multi-stage voice sessions.
## UI dependencies

The modern desktop shell uses:

- PySide6
- Pillow
- psutil
- qtawesome and markdown are installed for icon and markdown rendering in the desktop shell
- Piper is the selected text-to-speech engine for NOVO voice
- NOVO's Piper speech rate is tuned to be a little faster than the default
- faster-whisper is the selected speech-to-text engine for NOVO, with auto CUDA detection, warm-up CUDA probing, and CPU fallback on load or transcription failure
- sounddevice and soundfile are the audio I/O layer
- pyttsx3 is available as a Windows fallback voice engine if needed

If the GUI packages are missing, install them with:

```powershell
python -m pip install PySide6 qtawesome markdown Pillow psutil
```
