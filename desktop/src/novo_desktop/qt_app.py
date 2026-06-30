"""Modern PySide6 desktop assistant for NOVO E2.5."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import html
import math
import sys
import webbrowser

from PySide6.QtCore import QObject, QPoint, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

from .client import ConversationInfo, NovoApiClient, NovoApiError, ResponseEvent, SessionInfo

CONTROL_CENTER_URL = "http://localhost:3000"
DEFAULT_BACKEND_URL = "http://localhost:8000"


@dataclass(frozen=True, slots=True)
class WorkerResult:
    kind: str
    payload: object


class BackendWorker(QObject):
    result = Signal(object)
    event = Signal(object)
    error = Signal(str)
    finished = Signal()

    def __init__(self, action: str, client: NovoApiClient, **kwargs: object) -> None:
        super().__init__()
        self.action = action
        self.client = client
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            if self.action == "health":
                self.result.emit(WorkerResult("health_ok", self.client.health_live()))
            elif self.action == "login":
                session = self.client.login(str(self.kwargs["email"]), str(self.kwargs["password"]))
                self.result.emit(WorkerResult("login_ok", session))
            elif self.action == "new_conversation":
                title = str(self.kwargs["title"])
                self.result.emit(WorkerResult("conversation_ok", self.client.create_conversation(title)))
            elif self.action == "send":
                conversation_id = self.kwargs.get("conversation_id")
                if conversation_id is None:
                    title = f"Desktop session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    conversation = self.client.create_conversation(title)
                    conversation_id = conversation.id
                    self.result.emit(WorkerResult("conversation_ok", conversation))
                chat = self.client.send_message(str(conversation_id), str(self.kwargs["content"]))
                self.result.emit(WorkerResult("assistant_start", chat.response_id))
                for item in self.client.stream_response_events(chat.response_id):
                    self.event.emit(item)
            else:
                raise NovoApiError(f"Unknown action: {self.action}")
        except NovoApiError as exc:
            self.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.error.emit(f"{self.action} failed: {exc}")
        finally:
            self.finished.emit()


class GlowOrb(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(210, 118)
        self.phase = 0.0
        self.state = "Connecting"
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

    def set_state(self, state: str) -> None:
        self.state = state
        self.update()

    def tick(self) -> None:
        self.phase = (self.phase + 0.045) % (math.pi * 2)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        cx = rect.width() / 2
        cy = rect.height() * 0.43
        base = min(rect.width(), rect.height()) * 0.28
        pulse = 1 + math.sin(self.phase) * 0.08
        palette = {
            "Online": (QColor("#7c3cff"), QColor("#25d5ff")),
            "Idle": (QColor("#7c3cff"), QColor("#25d5ff")),
            "Connecting": (QColor("#6d5dfc"), QColor("#33c7ff")),
            "Thinking": (QColor("#ffb74d"), QColor("#7c3cff")),
            "Speaking": (QColor("#2de2e6"), QColor("#7c3cff")),
            "Listening": (QColor("#ff4fd8"), QColor("#33c7ff")),
            "Offline": (QColor("#64748b"), QColor("#273142")),
            "Error": (QColor("#ff5572"), QColor("#48111c")),
        }
        primary, secondary = palette.get(self.state, palette["Online"])
        for ring in range(7):
            color = QColor(primary)
            color.setAlpha(max(28, 145 - ring * 18))
            painter.setPen(QPen(color, 1.8))
            wobble = math.sin(self.phase * (1.1 + ring * 0.08) + ring) * 6
            painter.drawEllipse(QPoint(int(cx + wobble), int(cy)), int(base * pulse + ring * 7), int(base * 0.74 + ring * 5))
        gradient = QLinearGradient(0, 0, rect.width(), rect.height())
        gradient.setColorAt(0, QColor("#111827"))
        gradient.setColorAt(1, QColor("#030712"))
        painter.setBrush(gradient)
        painter.setPen(QPen(primary, 2))
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(base * 0.62), int(base * 0.62))
        painter.setBrush(QColor("#f8fbff"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(cx - base * 0.18), int(cy - 4)), 5, 7)
        painter.drawEllipse(QPoint(int(cx + base * 0.18), int(cy - 4)), 5, 7)
        painter.setPen(QPen(secondary, 2))
        for index in range(18):
            x = 16 + index * ((rect.width() - 32) / 17)
            wave = math.sin(self.phase * 2.5 + index * 0.7) * 12
            painter.drawLine(int(x), int(cy + base + 26 - wave), int(x), int(cy + base + 26 + wave))


class ChatBubble(QFrame):
    def __init__(self, role: str, text: str = "") -> None:
        super().__init__()
        self.role = role
        self.raw_text = text
        self.setObjectName(f"bubble_{role}")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        self.label = QLabel()
        self.label.setObjectName("bubbleText")
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.time = QLabel(datetime.now().strftime("%I:%M %p"))
        self.time.setObjectName("bubbleTime")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 10)
        layout.addWidget(self.label)
        layout.addWidget(self.time, alignment=Qt.AlignmentFlag.AlignRight)
        self.set_text(text)
        add_shadow(self, 30, 10, QColor(0, 0, 0, 120))

    def append_token(self, token: str) -> None:
        if self.raw_text and token and not token.startswith((".", ",", "!", "?", ";", ":", ")")):
            if not self.raw_text.endswith((" ", "\n", "(", "-")) and not token.startswith(" "):
                self.raw_text += " "
        self.raw_text += token
        self.set_text(self.raw_text)

    def set_text(self, text: str) -> None:
        self.raw_text = text
        safe = html.escape(text).replace("\n", "<br>")
        self.label.setText(safe or "...")

class StatCard(QFrame):
    def __init__(self, title: str, value: str, accent: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        self.value = QLabel(value)
        self.value.setObjectName("statValue")
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        dot = QLabel("?")
        dot.setStyleSheet(f"color: {accent}; font-size: 16px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 11, 13, 11)
        row = QHBoxLayout()
        row.addWidget(dot)
        row.addWidget(self.value)
        row.addStretch()
        layout.addLayout(row)
        layout.addWidget(title_label)

    def set_value(self, value: str) -> None:
        self.value.setText(value)


class NovoQtApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NOVO Desktop Assistant")
        self.resize(1280, 820)
        self.setMinimumSize(1100, 720)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.client = NovoApiClient(DEFAULT_BACKEND_URL)
        self.conversation_id: str | None = None
        self.active_assistant_bubble: ChatBubble | None = None
        self.threads: list[QThread] = []
        self.drag_position: QPoint | None = None
        self.command_count = 0
        self.conversation_count = 0
        self.started_at = datetime.now()
        self._build_ui()
        self.setStyleSheet(STYLES)
        self._start_metrics_timer()
        self.set_state("Connecting")
        self.run_worker("health")

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(8, 8, 8, 8)
        shell = QFrame()
        shell.setObjectName("shell")
        add_shadow(shell, 42, 18, QColor(0, 0, 0, 150))
        outer.addWidget(shell)
        main = QVBoxLayout(shell)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        main.addWidget(self._title_bar())
        grid = QGridLayout()
        grid.setContentsMargins(16, 10, 16, 16)
        grid.setHorizontalSpacing(10)
        grid.setColumnStretch(1, 1)
        main.addLayout(grid, stretch=1)
        grid.addWidget(self._left_panel(), 0, 0)
        grid.addWidget(self._conversation_panel(), 0, 1)
        grid.addWidget(self._right_panel(), 0, 2)

    def _title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("titleBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 14, 18, 8)
        icon = QLabel("?")
        icon.setObjectName("appIcon")
        brand = QVBoxLayout()
        brand.addWidget(label("NOVO", "brandTitle"))
        brand.addWidget(label("DESKTOP ASSISTANT", "brandSubtitle"))
        layout.addWidget(icon)
        layout.addLayout(brand)
        layout.addStretch()
        self.state_label = QLabel("Connecting")
        self.state_label.setObjectName("statePill")
        layout.addWidget(self.state_label)
        control = QPushButton("Control Center")
        control.setObjectName("ghostButton")
        control.clicked.connect(lambda: webbrowser.open(CONTROL_CENTER_URL))
        layout.addWidget(control)
        for text, slot in [("-", self.showMinimized), ("[]", self._toggle_maximized), ("x", self.close)]:
            button = QPushButton(text)
            button.setObjectName("windowButton")
            button.clicked.connect(slot)
            layout.addWidget(button)
        return bar

    def _left_panel(self) -> QWidget:
        panel = glass_panel("leftPanel")
        panel.setFixedWidth(306)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(8)
        self.orb = GlowOrb()
        layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        hero = label("NOVO", "heroName")
        hero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hero)
        subtitle = muted("Your AI Desktop Assistant")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        self.connection_badge = QLabel("Checking backend")
        self.connection_badge.setObjectName("connectionBadge")
        self.connection_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.connection_badge)
        layout.addWidget(self._voice_card())
        layout.addWidget(self._login_card())
        layout.addWidget(self._status_card())
        layout.addStretch()
        layout.addWidget(muted("NOVO v2.5.0  -  All systems operational"))
        return panel

    def _voice_card(self) -> QWidget:
        card = glass_panel("voicePanel")
        card.setFixedHeight(136)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        row = QHBoxLayout()
        row.addWidget(label("Voice", "panelTitle"))
        row.addStretch()
        settings = QLabel("Settings")
        settings.setObjectName("tinyAction")
        row.addWidget(settings)
        layout.addLayout(row)
        layout.addWidget(muted("Push-to-talk or click to speak"))
        mic = QPushButton("MIC")
        mic.setObjectName("micButton")
        mic.setFixedSize(48, 48)
        mic.clicked.connect(self.voice_placeholder)
        layout.addWidget(mic, alignment=Qt.AlignmentFlag.AlignCenter)
        talk = QPushButton("Hold to Talk")
        talk.setObjectName("smallGlowButton")
        talk.setFixedHeight(30)
        talk.clicked.connect(self.voice_placeholder)
        layout.addWidget(talk)
        return card

    def _login_card(self) -> QWidget:
        card = glass_panel("loginPanel")
        card.setFixedHeight(162)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        layout.addWidget(label("Backend Login", "panelTitle"))
        self.backend_edit = QLineEdit(DEFAULT_BACKEND_URL)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("owner@novo.example")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        for field in [self.backend_edit, self.email_edit, self.password_edit]:
            field.setFixedHeight(28)
            layout.addWidget(field)
        sign_in = QPushButton("Sign In")
        sign_in.setObjectName("primaryButton")
        sign_in.setFixedHeight(32)
        sign_in.clicked.connect(self.login)
        layout.addWidget(sign_in)
        return card

    def _status_card(self) -> QWidget:
        card = glass_panel("statusPanel")
        card.setFixedHeight(122)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        layout.addWidget(label("System Status", "panelTitle"))
        self.backend_status = label("Backend                 Checking", "statusLine")
        self.memory_status = label("Memory                  42%", "statusLine")
        self.cpu_status = label("CPU                     --%", "statusLine")
        layout.addWidget(self.backend_status)
        layout.addWidget(self.memory_status)
        layout.addWidget(self.cpu_status)
        return card

    def _conversation_panel(self) -> QWidget:
        panel = glass_panel("conversationPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(8)
        header = QHBoxLayout()
        header.addWidget(label("*  Conversation", "sectionTitle"))
        header.addStretch()
        new_chat = QPushButton("+ New Conversation")
        new_chat.setObjectName("primaryButton")
        new_chat.clicked.connect(self.new_conversation)
        header.addWidget(new_chat)
        layout.addLayout(header)
        self.scroll = QScrollArea()
        self.scroll.setObjectName("chatScroll")
        self.scroll.setWidgetResizable(True)
        self.chat_host = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_host)
        self.chat_layout.setContentsMargins(4, 8, 4, 8)
        self.chat_layout.setSpacing(6)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_host)
        layout.addWidget(self.scroll, stretch=1)
        composer = QFrame()
        composer.setObjectName("composer")
        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(14, 10, 10, 10)
        self.message_edit = QTextEdit()
        self.message_edit.setObjectName("messageEdit")
        self.message_edit.setPlaceholderText("Type your message...")
        self.message_edit.setFixedHeight(58)
        composer_layout.addWidget(self.message_edit, stretch=1)
        self.send_button = QPushButton(">")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.send_message)
        composer_layout.addWidget(self.send_button)
        layout.addWidget(composer)
        hint = muted("Press Ctrl+Enter to send. Voice arrives in the next E2.5 slice.")
        hint.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(hint)
        self.message_edit.installEventFilter(self)
        self.add_system_message("NOVO desktop console loaded. Sign in, then send a message.")
        return panel

    def _right_panel(self) -> QWidget:
        panel = glass_panel("rightPanel")
        panel.setFixedWidth(260)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(8)
        self.greeting = label("Good Evening, Prime", "rightTitle")
        layout.addWidget(self.greeting)
        layout.addWidget(muted("Here is what is happening"))
        grid = QGridLayout()
        grid.setSpacing(8)
        self.conversations_card = StatCard("Conversations", "0", "#ff66c4")
        self.commands_card = StatCard("Commands", "0", "#7c3cff")
        self.active_card = StatCard("Active Time", "0m", "#28e98c")
        self.uptime_card = StatCard("Uptime", "--", "#36b7ff")
        cards = [self.conversations_card, self.commands_card, self.active_card, self.uptime_card]
        for index, card in enumerate(cards):
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addSpacing(8)
        layout.addWidget(label("Quick Actions", "panelTitle"))
        for text in ["Open Terminal", "System Info", "Take Screenshot", "Manage Reminders"]:
            button = QPushButton(text)
            button.setObjectName("actionButton")
            button.clicked.connect(lambda _checked=False, t=text: self.toast(f"{t} is planned for a later desktop slice."))
            layout.addWidget(button)
        layout.addStretch()
        mascot = QLabel("*\n  o   o\n[ NOVO ]")
        mascot.setObjectName("mascot")
        mascot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(mascot)
        return panel

    def eventFilter(self, obj: QObject, event) -> bool:  # noqa: N802
        if obj is self.message_edit and event.type() == event.Type.KeyPress:
            key = event.key()
            mods = event.modifiers()
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and mods & Qt.KeyboardModifier.ControlModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self.drag_position and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def mouseReleaseEvent(self, _event) -> None:  # noqa: N802
        self.drag_position = None

    def _toggle_maximized(self) -> None:
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def run_worker(self, action: str, **kwargs: object) -> None:
        worker = BackendWorker(action, self.client, **kwargs)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.result.connect(self.handle_worker_result)
        worker.event.connect(self.handle_response_event)
        worker.error.connect(self.handle_worker_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._forget_thread(thread))
        self.threads.append(thread)
        thread.start()

    def _forget_thread(self, thread: QThread) -> None:
        if thread in self.threads:
            self.threads.remove(thread)

    def login(self) -> None:
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        if not email or not password:
            QMessageBox.information(self, "NOVO", "Enter email and password first.")
            return
        self.client = NovoApiClient(self.backend_edit.text().strip() or DEFAULT_BACKEND_URL)
        self.set_state("Connecting")
        self.run_worker("login", email=email, password=password)

    def new_conversation(self) -> None:
        if not self.client.csrf_token:
            QMessageBox.information(self, "NOVO", "Sign in before creating a conversation.")
            return
        self.set_state("Thinking")
        title = f"Desktop session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.run_worker("new_conversation", title=title)

    def send_message(self) -> None:
        content = self.message_edit.toPlainText().strip()
        if not content:
            return
        if not self.client.csrf_token:
            QMessageBox.information(self, "NOVO", "Sign in before sending messages.")
            return
        self.message_edit.clear()
        self.command_count += 1
        self.commands_card.set_value(str(self.command_count))
        self.add_bubble("user", content)
        self.set_state("Thinking")
        self.send_button.setEnabled(False)
        self.run_worker("send", conversation_id=self.conversation_id, content=content)

    def handle_worker_result(self, result: WorkerResult) -> None:
        if result.kind == "health_ok":
            payload = result.payload if isinstance(result.payload, dict) else {}
            self.backend_status.setText("Backend                 Connected")
            self.connection_badge.setText("? Online & Ready")
            self.connection_badge.setProperty("mode", "online")
            self.style().unpolish(self.connection_badge)
            self.style().polish(self.connection_badge)
            self.set_state("Online")
            self.add_system_message(f"Backend live: {payload.get('service', 'NOVO')} {payload.get('version', '')}")
        elif result.kind == "login_ok" and isinstance(result.payload, SessionInfo):
            self.set_state("Online")
            name = result.payload.display_name
            self.greeting.setText(f"Good Evening, {name.split()[0]}")
            self.add_system_message(f"Signed in as {name}. Session expires {result.payload.expires_at}.")
        elif result.kind == "conversation_ok" and isinstance(result.payload, ConversationInfo):
            self.conversation_id = result.payload.id
            self.conversation_count += 1
            self.conversations_card.set_value(str(self.conversation_count))
            self.add_system_message(f"Conversation ready: {result.payload.title}")
        elif result.kind == "assistant_start":
            self.active_assistant_bubble = self.add_bubble("assistant", "")
            self.set_state("Speaking")

    def handle_worker_error(self, message: str) -> None:
        self.set_state("Error")
        self.backend_status.setText("Backend                 Attention")
        self.add_system_message(message)
        self.send_button.setEnabled(True)

    def handle_response_event(self, event: ResponseEvent) -> None:
        if event.event == "response.token":
            token = str(event.data.get("token") or "")
            if self.active_assistant_bubble is None:
                self.active_assistant_bubble = self.add_bubble("assistant", "")
            self.active_assistant_bubble.append_token(token)
            self.scroll_to_bottom()
        elif event.event == "response.warning":
            warnings = event.data.get("warnings") or []
            self.add_system_message(f"Warning: {', '.join(warnings)}")
        elif event.event == "response.completed":
            self.set_state("Online")
            self.send_button.setEnabled(True)
            self.active_assistant_bubble = None
        elif event.event == "response.failed":
            self.set_state("Error")
            self.send_button.setEnabled(True)
            self.add_system_message(str(event.data.get("error_message") or "Response failed."))

    def add_system_message(self, text: str) -> ChatBubble:
        return self.add_bubble("system", text)

    def add_bubble(self, role: str, text: str) -> ChatBubble:
        bubble = ChatBubble(role, text)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if role == "user":
            row.addStretch()
            row.addWidget(bubble)
        else:
            avatar = QLabel("?")
            avatar.setObjectName("avatar")
            row.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignTop)
            row.addWidget(bubble)
            row.addStretch()
        container = QWidget()
        container.setLayout(row)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
        self.scroll_to_bottom()
        return bubble

    def scroll_to_bottom(self) -> None:
        QTimer.singleShot(10, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

    def set_state(self, state: str) -> None:
        self.state_label.setText("Online" if state == "Online" else state)
        self.state_label.setProperty("mode", state.lower())
        self.orb.set_state(state)
        self.style().unpolish(self.state_label)
        self.style().polish(self.state_label)

    def voice_placeholder(self) -> None:
        self.set_state("Listening")
        self.add_system_message("Voice capture placeholder reached. Push-to-talk arrives in E2.5.2.")
        QTimer.singleShot(900, lambda: self.set_state("Online" if self.client.csrf_token else "Idle"))

    def toast(self, text: str) -> None:
        self.add_system_message(text)

    def _start_metrics_timer(self) -> None:
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(1500)
        self.update_metrics()

    def update_metrics(self) -> None:
        elapsed = datetime.now() - self.started_at
        minutes = max(0, int(elapsed.total_seconds() // 60))
        self.active_card.set_value(f"{minutes}m")
        if psutil is not None:
            self.cpu_status.setText(f"CPU                     {int(psutil.cpu_percent(interval=None))}%")
            self.uptime_card.set_value("98%")


def label(text: str, object_name: str) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(object_name)
    return widget


def muted(text: str) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName("muted")
    widget.setWordWrap(True)
    return widget


def glass_panel(name: str) -> QFrame:
    panel = QFrame()
    panel.setObjectName(name)
    add_shadow(panel, 28, 12, QColor(0, 0, 0, 90))
    return panel


def add_shadow(widget: QWidget, blur: int, y: int, color: QColor) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)


STYLES = """
#root { background: transparent; }
#shell { background: #03060b; border: 1px solid rgba(102,126,234,0.18); border-radius: 22px; }
#titleBar { background: transparent; }
#appIcon { min-width: 44px; min-height: 44px; max-width: 44px; max-height: 44px; border-radius: 22px; background: qradialgradient(cx:0.3, cy:0.2, radius:1, stop:0 #273f74, stop:1 #060a12); color: #8dd7ff; font-size: 24px; font-weight: 800; qproperty-alignment: AlignCenter; }
#brandTitle { color: #f8fbff; font-size: 25px; font-weight: 800; }
#brandSubtitle { color: #7c3cff; font-size: 12px; font-weight: 800; }
#statePill, #connectionBadge { color: #cbd5e1; background: rgba(15,23,42,0.72); border: 1px solid rgba(148,163,184,0.16); border-radius: 15px; padding: 7px 14px; font-weight: 700; }
#statePill[mode="online"], #connectionBadge[mode="online"] { color: #7df8b7; border-color: rgba(45,233,140,0.26); }
#statePill[mode="thinking"] { color: #ffd38a; border-color: rgba(255,183,77,0.28); }
#statePill[mode="speaking"] { color: #7defff; border-color: rgba(45,226,230,0.28); }
#statePill[mode="error"] { color: #ff8aa0; border-color: rgba(255,85,114,0.3); }
#windowButton, #ghostButton { background: rgba(15,23,42,0.62); color: #e2e8f0; border: 1px solid rgba(148,163,184,0.16); border-radius: 10px; padding: 8px 12px; font-weight: 700; }
#windowButton:hover, #ghostButton:hover, #actionButton:hover { background: rgba(124,60,255,0.18); border-color: rgba(124,60,255,0.42); }
#leftPanel, #rightPanel, #conversationPanel, #voicePanel, #loginPanel, #statusPanel, #statCard { background: rgba(9,14,24,0.72); border: 1px solid rgba(148,163,184,0.12); border-radius: 18px; }
#conversationPanel { background: rgba(7,11,19,0.82); }
#heroName { color: #7657ff; font-size: 22px; font-weight: 900; margin-top: 0; }
#muted, #bubbleTime, #statTitle { color: #94a3b8; font-size: 11px; }
#panelTitle, #sectionTitle, #rightTitle { color: #f8fbff; font-size: 14px; font-weight: 800; }
#tinyAction { color: #64748b; font-size: 10px; }
#sectionTitle { font-size: 16px; }
#statusLine { color: #cbd5e1; padding: 3px 0; font-size: 12px; }
#primaryButton, #sendButton, #smallGlowButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7c3cff, stop:1 #2563eb); color: white; border: 0; border-radius: 10px; padding: 7px 12px; font-weight: 800; }
#primaryButton:hover, #sendButton:hover, #smallGlowButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #9068ff, stop:1 #3b82f6); }
#sendButton { min-width: 50px; min-height: 44px; border-radius: 12px; font-size: 18px; }
#sendButton:disabled { background: #1e293b; color: #64748b; }
#micButton { min-width: 48px; min-height: 48px; max-width: 48px; max-height: 48px; border-radius: 24px; background: rgba(124,60,255,0.12); color: white; border: 2px solid #7c3cff; font-size: 13px; font-weight: 900; }
#chatScroll { background: transparent; border: 0; }
#chatScroll QWidget { background: transparent; }
#composer { background: rgba(15,23,42,0.68); border: 1px solid rgba(148,163,184,0.13); border-radius: 16px; }
#messageEdit { background: transparent; color: #f8fbff; border: 0; font-size: 14px; selection-background-color: #7c3cff; }
#bubble_system, #bubble_assistant, #bubble_user { border-radius: 16px; border: 1px solid rgba(148,163,184,0.12); }
#bubble_system, #bubble_assistant { background: rgba(15,23,42,0.78); }
#bubble_user { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7c3cff, stop:1 #1d4ed8); }
#bubbleText { color: #e5edf8; font-size: 14px; line-height: 1.45; }
#avatar { color: #8dd7ff; min-width: 34px; min-height: 34px; max-width: 34px; max-height: 34px; border-radius: 17px; border: 1px solid #7c3cff; qproperty-alignment: AlignCenter; }
#statValue { color: #f8fbff; font-size: 19px; font-weight: 900; }
#actionButton { text-align: left; background: rgba(15,23,42,0.62); color: #dbe7f6; border: 1px solid rgba(148,163,184,0.12); border-radius: 12px; padding: 12px 14px; }
#mascot { color: #9cc7ff; font-size: 24px; background: rgba(124,60,255,0.08); border: 1px solid rgba(124,60,255,0.18); border-radius: 22px; padding: 16px; }
QLineEdit { background: rgba(15,23,42,0.78); color: #f8fbff; border: 1px solid rgba(148,163,184,0.14); border-radius: 8px; padding: 4px 10px; font-size: 12px; selection-background-color: #7c3cff; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: rgba(124,60,255,0.42); border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("NOVO Desktop Assistant")
    window = NovoQtApp()
    window.show()
    sys.exit(app.exec())
