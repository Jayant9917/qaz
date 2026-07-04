# NOVO Current Work

This is the single living documentation file for ongoing NOVO work.

When the project changes, update this file first so the current state stays easy to follow.

## Current checkpoint

- E2.5 complete / E3 in progress

## What this file is for

Use this file for the latest work-in-progress summary:

- what we are building right now
- what changed most recently
- what is blocked
- what the next step is
- any decisions that should not be forgotten

## Update rule

Keep this file short, current, and easy for a junior engineer to read.
If a detail becomes historical, move it into the relevant folder under `docs/` instead of keeping it here.

## Current status snapshot

- E2 is complete.
- The current engineering phase is E3: explicit memory, with the first durable memory slice implemented and verified.
- The next backend work is the remaining E3 memory slices: revisions, sources, tags, guardrails, and the Memory Center.
- The docs have been reorganized into purpose-based folders, and this file is the single living work log.
- The new API documentation lives under `docs/api/`.
- The desktop GUI now acts as the primary NOVO face for chat, status, and voice work.
- The selected NOVO desktop voice stack is Piper TTS with the female English `en_US-amy-medium` profile, paired with faster-whisper for STT. The desktop shell can synthesize and play Piper voice output, capture microphone input with push-to-talk, transcribe it locally, and stop playback or streaming on request. The STT runtime auto-detects CUDA, probes it during warm-up, and falls back to CPU if the CUDA runtime is broken. The Piper rate is tuned a bit faster than the default. Voice and backend failures now emit exact traces to the desktop/backend terminals while the UI shows safe messages. Assistant bubbles render markdown cleanly, while speech output strips markdown markers before speaking.
- Local desktop settings persist safe values such as backend URL, email, and window size without storing secrets.

- The first E3 memory slice is implemented: durable memory records, explicit remember command, access events, and memory CRUD/correction/archive/restore/delete APIs.

## What was completed in E2

- Conversation fast path
- Ordered messages and conversation history
- Chat API with SSE response streaming
- Fast-path routing and orchestration selection
- Prompt registry minimum implementation
- Model registry and OpenRouter gateway
- Input and output guardrails
- Token, latency, and cost accounting
- Conversation UI and history in the frontend
- Desktop GUI shell with backend login, live status, chat streaming, refresh health checks, Enter-to-send, Shift+Enter newline behavior, and smoother scroll handling

## What comes next

- E3 explicit memory
- Redis working context
- memory records, revisions, sources, and tags
- memory guardrails and memory center
- correction, archive, classification, deletion, and provenance
- later voice enhancements such as wake word and always-on listening
