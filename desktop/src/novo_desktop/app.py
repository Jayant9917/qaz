"""Tkinter desktop shell for NOVO E2.5."""

from __future__ import annotations

from datetime import datetime
import logging
from queue import Empty, Queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from .client import NovoApiClient, NovoApiError, ResponseEvent
from .voice import voice_summary

CONTROL_CENTER_URL = "http://localhost:3000"
DEFAULT_BACKEND_URL = "http://localhost:8000"
logger = logging.getLogger(__name__)


def _desktop_session_title() -> str:
    timestamp = datetime.now()
    return f"Desktop session {timestamp.strftime('%Y-%m-%d %H:%M:%S')}.{timestamp.microsecond // 1000:03d}"


class NovoDesktopApp(tk.Tk):
    """First local desktop face for NOVO."""

    def __init__(self) -> None:
        super().__init__()
        self.title("NOVO Desktop Assistant")
        self.geometry("1180x780")
        self.minsize(980, 680)
        self.configure(bg="#050608")

        self.client = NovoApiClient(DEFAULT_BACKEND_URL)
        self.conversation_id: str | None = None
        self.queue: Queue[tuple[str, object]] = Queue()
        self.state = "Idle"
        self.orb_phase = 0

        self._configure_styles()
        self._build_layout()
        self._set_state("Connecting")
        self._run_worker("health", self._check_health)
        self.after(80, self._poll_queue)
        self.after(60, self._animate_orb)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#050608")
        style.configure("Panel.TFrame", background="#0d1117", relief="flat")
        style.configure("TLabel", background="#050608", foreground="#f2f6ff")
        style.configure("Muted.TLabel", background="#050608", foreground="#8b98aa")
        style.configure("Panel.TLabel", background="#0d1117", foreground="#f2f6ff")
        style.configure("MutedPanel.TLabel", background="#0d1117", foreground="#8b98aa")
        style.configure("TButton", padding=(14, 9), background="#18202c", foreground="#f2f6ff")
        style.map("TButton", background=[("active", "#223047")])
        style.configure("Primary.TButton", background="#e8f1ff", foreground="#061018")
        style.map("Primary.TButton", background=[("active", "#cfe4ff")])
        style.configure("Danger.TButton", background="#3a1418", foreground="#ffb3ba")
        style.map("Danger.TButton", background=[("active", "#572028")])
        style.configure("TEntry", fieldbackground="#111823", foreground="#f2f6ff", insertcolor="#f2f6ff")

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(24, 18, 24, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        title_box = ttk.Frame(header)
        title_box.grid(row=0, column=0, sticky="w")
        ttk.Label(title_box, text="NOVO", font=("Segoe UI", 24, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_box,
            text="Desktop Assistant Shell - E2.5",
            style="Muted.TLabel",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w")

        self.status_label = ttk.Label(header, text="Connecting", font=("Segoe UI", 11, "bold"))
        self.status_label.grid(row=0, column=1, sticky="e", padx=14)
        ttk.Button(header, text="Control Center", command=self._open_control_center).grid(
            row=0, column=2, sticky="e"
        )

        body = ttk.Frame(self, padding=(24, 0, 24, 24))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, style="Panel.TFrame", padding=18)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 18))
        left.columnconfigure(0, weight=1)

        self.orb = tk.Canvas(left, width=220, height=220, bg="#0d1117", highlightthickness=0)
        self.orb.grid(row=0, column=0, pady=(0, 14))

        ttk.Label(left, text="Voice", style="Panel.TLabel", font=("Segoe UI", 14, "bold")).grid(
            row=1, column=0, sticky="w"
        )
        self.voice_hint = ttk.Label(
            left,
            text=f"NOVO voice: {voice_summary()}. The PySide shell already speaks with Piper; audio capture comes next in E2.5.",
            style="MutedPanel.TLabel",
            wraplength=230,
        )
        self.voice_hint.grid(row=2, column=0, sticky="ew", pady=(6, 12))
        ttk.Button(left, text="Hold to Talk", command=self._voice_placeholder).grid(
            row=3, column=0, sticky="ew"
        )
        ttk.Button(left, text="Stop Response", style="Danger.TButton", command=self._stop_placeholder).grid(
            row=4, column=0, sticky="ew", pady=(10, 0)
        )

        login = ttk.Frame(left, style="Panel.TFrame")
        login.grid(row=5, column=0, sticky="ew", pady=(18, 0))
        login.columnconfigure(0, weight=1)
        ttk.Label(login, text="Backend", style="Panel.TLabel", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.backend_var = tk.StringVar(value=DEFAULT_BACKEND_URL)
        ttk.Entry(login, textvariable=self.backend_var).grid(row=1, column=0, sticky="ew", pady=(6, 8))
        ttk.Label(login, text="Email", style="MutedPanel.TLabel").grid(row=2, column=0, sticky="w")
        self.email_var = tk.StringVar()
        ttk.Entry(login, textvariable=self.email_var).grid(row=3, column=0, sticky="ew", pady=(4, 8))
        ttk.Label(login, text="Password", style="MutedPanel.TLabel").grid(row=4, column=0, sticky="w")
        self.password_var = tk.StringVar()
        ttk.Entry(login, textvariable=self.password_var, show="*").grid(row=5, column=0, sticky="ew", pady=(4, 10))
        ttk.Button(login, text="Sign In", style="Primary.TButton", command=self._login).grid(
            row=6, column=0, sticky="ew"
        )

        right = ttk.Frame(body, style="Panel.TFrame", padding=18)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(right, style="Panel.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        toolbar.columnconfigure(0, weight=1)
        self.session_label = ttk.Label(
            toolbar,
            text="Not signed in",
            style="MutedPanel.TLabel",
            font=("Segoe UI", 10, "bold"),
        )
        self.session_label.grid(row=0, column=0, sticky="w")
        ttk.Button(toolbar, text="New Conversation", command=self._new_conversation).grid(
            row=0, column=1, sticky="e"
        )

        self.transcript = tk.Text(
            right,
            bg="#080c12",
            fg="#eef5ff",
            insertbackground="#eef5ff",
            relief="flat",
            padx=18,
            pady=18,
            wrap="word",
            font=("Segoe UI", 11),
        )
        self.transcript.grid(row=1, column=0, sticky="nsew")
        self.transcript.configure(state="disabled")

        compose = ttk.Frame(right, style="Panel.TFrame")
        compose.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        compose.columnconfigure(0, weight=1)
        self.message_entry = tk.Text(
            compose,
            height=3,
            bg="#101722",
            fg="#eef5ff",
            insertbackground="#eef5ff",
            relief="flat",
            padx=12,
            pady=10,
            wrap="word",
            font=("Segoe UI", 11),
        )
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.message_entry.bind("<Control-Return>", lambda _event: self._send_message())
        ttk.Button(compose, text="Send", style="Primary.TButton", command=self._send_message).grid(
            row=0, column=1, sticky="ns"
        )

        self._append_system("NOVO desktop shell loaded. Sign in, then send a text message to the backend.")

    def _check_health(self) -> None:
        self.client = NovoApiClient(self.backend_var.get().strip() or DEFAULT_BACKEND_URL)
        health = self.client.health_live()
        self.queue.put(("health_ok", health))

    def _login(self) -> None:
        email = self.email_var.get().strip()
        password = self.password_var.get()
        if not email or not password:
            messagebox.showwarning("NOVO", "Enter email and password first.")
            return
        self._set_state("Connecting")
        self.client = NovoApiClient(self.backend_var.get().strip() or DEFAULT_BACKEND_URL)
        self._run_worker("login", lambda: self.queue.put(("login_ok", self.client.login(email, password))))

    def _new_conversation(self) -> None:
        if not self.client.csrf_token:
            messagebox.showinfo("NOVO", "Sign in before creating a conversation.")
            return
        title = _desktop_session_title()
        self._set_state("Thinking")
        self._run_worker("new_conversation", lambda: self.queue.put(("conversation_ok", self.client.create_conversation(title))))

    def _send_message(self) -> None:
        content = self.message_entry.get("1.0", "end").strip()
        if not content:
            return
        if not self.client.csrf_token:
            messagebox.showinfo("NOVO", "Sign in before sending messages.")
            return
        self.message_entry.delete("1.0", "end")
        self._append_user(content)
        self._set_state("Thinking")
        self._run_worker("send_message", lambda: self._send_and_stream(content))

    def _send_and_stream(self, content: str) -> None:
        if self.conversation_id is None:
            conversation = self.client.create_conversation(
                _desktop_session_title()
            )
            self.conversation_id = conversation.id
            self.queue.put(("conversation_ok", conversation))
        chat = self.client.send_message(self.conversation_id, content)
        try:
            suggestion = self.client.suggest_memory(self.conversation_id, chat.response_id, content)
            if suggestion.get("should_suggest"):
                suggestion["source_locator"] = {
                    "channel": "desktop",
                    "conversation_id": self.conversation_id,
                    "message_id": chat.response_id,
                }
                self.queue.put(("memory_suggestion", suggestion))
        except NovoApiError:
            logger.exception("NOVO memory suggestion failed; continuing chat")
        self.queue.put(("assistant_start", chat.response_id))
        for event in self.client.stream_response_events(chat.response_id):
            self.queue.put(("response_event", event))

    def _save_memory_suggestion(self, suggestion: dict[str, object]) -> None:
        self.client.remember_memory(suggestion)
        self.queue.put(("memory_saved", None))
    def _run_worker(self, name: str, target) -> None:  # noqa: ANN001
        def wrapped() -> None:
            try:
                target()
            except NovoApiError as exc:
                self.queue.put(("error", str(exc)))
            except Exception as exc:  # noqa: BLE001
                self.queue.put(("error", f"{name} failed: {exc}"))

        threading.Thread(target=wrapped, name=f"novo-desktop-{name}", daemon=True).start()

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                self._handle_event(kind, payload)
        except Empty:
            pass
        self.after(80, self._poll_queue)

    def _handle_event(self, kind: str, payload: object) -> None:
        if kind == "health_ok":
            status = payload if isinstance(payload, dict) else {}
            self._set_state("Idle")
            self._append_system(f"Backend live: {status.get('service', 'NOVO')} {status.get('version', '')}")
            return
        if kind == "health_error":
            self._set_state("Offline")
            self._append_system(f"Backend not reachable yet: {payload}")
            self._append_system("Start the backend or check the backend URL, then sign in when it is live.")
            return
        if kind == "login_ok":
            session = payload
            self._set_state("Idle")
            self.session_label.configure(text=f"Signed in as {session.display_name} - {session.email}")
            self._append_system(f"Signed in. Session expires at {session.expires_at}.")
            return
        if kind == "conversation_ok":
            conversation = payload
            self.conversation_id = conversation.id
            self._append_system(f"Conversation ready: {conversation.title}")
            self._set_state("Idle")
            return
        if kind == "memory_suggestion" and isinstance(payload, dict):
            approved = messagebox.askyesno(
                "NOVO memory suggestion",
                f"Should NOVO remember this?\n\n{payload.get('content', '')}",
            )
            if approved:
                self._run_worker("remember_memory", lambda: self._save_memory_suggestion(payload))
            return
        if kind == "memory_saved":
            self._append_system("Memory saved with your approval.")
            return
        if kind == "assistant_start":
            self._append_assistant_prefix()
            self._set_state("Speaking")
            return
        if kind == "response_event" and isinstance(payload, ResponseEvent):
            self._handle_response_event(payload)
            return
        if kind == "error":
            self._set_state("Error")
            self._append_system(str(payload))

    def _handle_response_event(self, event: ResponseEvent) -> None:
        if event.event == "response.token":
            token = str(event.data.get("token") or "")
            self._append_assistant_token(token)
            return
        if event.event == "response.warning":
            warnings = event.data.get("warnings") or []
            self._append_system(f"Warning: {', '.join(warnings)}")
            return
        if event.event == "response.completed":
            self._append_assistant_token("\n")
            self._set_state("Idle")
            return
        if event.event == "response.failed":
            self._set_state("Error")
            self._append_system(str(event.data.get("error_message") or "Response failed."))

    def _append_system(self, text: str) -> None:
        self._append_text(f"\n[system] {text}\n", "system")

    def _append_user(self, text: str) -> None:
        self._append_text(f"\nYou: {text}\n", "user")

    def _append_assistant_prefix(self) -> None:
        self._append_text("\nNOVO: ", "assistant")

    def _append_assistant_token(self, token: str) -> None:
        suffix = "" if token == "\n" else " "
        self._append_text(f"{token}{suffix}", "assistant")

    def _append_text(self, text: str, tag: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.tag_configure("system", foreground="#8b98aa")
        self.transcript.tag_configure("user", foreground="#d9f99d")
        self.transcript.tag_configure("assistant", foreground="#bfdbfe")
        self.transcript.insert("end", text, tag)
        self.transcript.see("end")
        self.transcript.configure(state="disabled")

    def _set_state(self, state: str) -> None:
        self.state = state
        self.status_label.configure(text=state)

    def _animate_orb(self) -> None:
        self.orb.delete("all")
        self.orb_phase = (self.orb_phase + 1) % 120
        pulse = self.orb_phase if self.orb_phase <= 60 else 120 - self.orb_phase
        state_colors = {
            "Idle": ("#1f2937", "#60a5fa"),
            "Connecting": ("#312e81", "#a5b4fc"),
            "Thinking": ("#3b2600", "#fbbf24"),
            "Speaking": ("#052e2b", "#5eead4"),
            "Offline": ("#1f2937", "#94a3b8"),
            "Error": ("#3b0a12", "#fb7185"),
        }
        fill, outline = state_colors.get(self.state, ("#1f2937", "#60a5fa"))
        radius = 62 + pulse / 4
        center = 110
        self.orb.create_oval(
            center - radius,
            center - radius,
            center + radius,
            center + radius,
            fill=fill,
            outline=outline,
            width=3,
        )
        self.orb.create_oval(78, 78, 142, 142, fill="#08111d", outline=outline, width=2)
        self.orb.create_text(center, center, text=self.state.upper(), fill="#eef5ff", font=("Segoe UI", 12, "bold"))
        self.after(60, self._animate_orb)

    def _voice_placeholder(self) -> None:
        self._set_state("Listening")
        self._append_system(f"Voice profile set to {voice_summary()}. The PySide shell already speaks with Piper; microphone capture comes next.")
        self.after(900, lambda: self._set_state("Idle"))

    def _stop_placeholder(self) -> None:
        self._set_state("Idle")
        self._append_system("Stop requested. Streaming cancellation will be wired with voice/audio work.")

    def _open_control_center(self) -> None:
        webbrowser.open(CONTROL_CENTER_URL)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = NovoDesktopApp()
    app.mainloop()