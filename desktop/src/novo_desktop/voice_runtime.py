"""NOVO audio runtime helpers for the E2.5 voice foundation."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
import tempfile
import time
from queue import Empty, Queue
from pathlib import Path
from typing import Callable, NoReturn
import threading
import wave

import numpy as np
from faster_whisper import WhisperModel
from piper import PiperVoice
from piper.config import SynthesisConfig
from piper.download_voices import download_voice
import sounddevice as sd
import soundfile as sf

from .voice import NOVO_VOICE_PROFILE, VoiceProfile

DEFAULT_STT_MODEL = os.environ.get("NOVO_STT_MODEL", "small.en")
DEFAULT_STT_DEVICE = os.environ.get("NOVO_STT_DEVICE", "auto")
DEFAULT_STT_COMPUTE_TYPE = os.environ.get("NOVO_STT_COMPUTE_TYPE", "auto")
DEFAULT_TRANSCRIPTION_PROMPT = (
    "NOVO is a desktop assistant. Common words include NOVO, Virat Kohli, "
    "ChatGPT, email, backend, frontend, microphone, Piper, and documents."
)
DEFAULT_TRANSCRIPTION_HOTWORDS = "NOVO Virat Kohli ChatGPT email backend frontend microphone Piper documents"
DEFAULT_CAPTURE_SECONDS = float(os.environ.get("NOVO_CAPTURE_SECONDS", "5.5"))
DEFAULT_CAPTURE_BLOCK_SECONDS = float(os.environ.get("NOVO_CAPTURE_BLOCK_SECONDS", "0.12"))
DEFAULT_INITIAL_SILENCE_SECONDS = float(os.environ.get("NOVO_INITIAL_SILENCE_SECONDS", "1.4"))
DEFAULT_SILENCE_SECONDS = float(os.environ.get("NOVO_SILENCE_SECONDS", "0.85"))
DEFAULT_SPEECH_THRESHOLD = float(os.environ.get("NOVO_SPEECH_THRESHOLD", "0.008"))
DEFAULT_MIN_SPEECH_SECONDS = float(os.environ.get("NOVO_MIN_SPEECH_SECONDS", "0.3"))
DEFAULT_NOISE_CALIBRATION_SECONDS = float(os.environ.get("NOVO_NOISE_CALIBRATION_SECONDS", "0.4"))

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class VoiceAssets:
    model_path: Path
    config_path: Path


@dataclass(frozen=True, slots=True)
class AudioCaptureResult:
    audio_path: Path
    sample_rate: int
    channels: int


class VoiceRuntimeError(RuntimeError):
    """Structured voice error with a safe user message."""

    def __init__(self, operation: str, user_message: str) -> None:
        super().__init__(f"{operation}: {user_message}")
        self.operation = operation
        self.user_message = user_message


def _raise_voice_error(operation: str, user_message: str, exc: Exception) -> NoReturn:
    logger.exception("NOVO voice %s failed", operation)
    raise VoiceRuntimeError(operation, user_message) from exc


def _frame_rms(frame: np.ndarray) -> float:
    array = np.asarray(frame, dtype=np.float32)
    if array.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(array))))


def _cuda_device_count() -> int:
    try:
        import ctranslate2
    except Exception:  # noqa: BLE001
        return 0

    try:
        return int(ctranslate2.get_cuda_device_count())
    except Exception:  # noqa: BLE001
        logger.exception("NOVO STT CUDA probe failed")
        return 0


def _resolve_stt_device(preferred_device: str | None = None) -> str:
    device = (preferred_device or DEFAULT_STT_DEVICE).strip().lower()
    if device in {"cpu", "cuda"}:
        return device
    if device not in {"", "auto"}:
        logger.warning("NOVO STT device override %r is invalid; falling back to auto detection.", device)
    return "cuda" if _cuda_device_count() > 0 else "cpu"


def _resolve_stt_compute_type(device: str, preferred_compute_type: str | None = None) -> str:
    compute_type = (preferred_compute_type or DEFAULT_STT_COMPUTE_TYPE).strip().lower()
    if compute_type and compute_type != "auto" and compute_type != "default":
        return compute_type
    return "float16" if device == "cuda" else "int8"


def _is_cuda_runtime_failure(exc: Exception) -> bool:
    message = str(exc).casefold()
    cuda_markers = ("cublas64_12.dll", "cublas", "cannot be loaded", "not found")
    return isinstance(exc, RuntimeError) and any(marker in message for marker in cuda_markers)


def default_voice_cache_dir() -> Path:
    env_override = os.environ.get("NOVO_VOICE_CACHE_DIR")
    if env_override:
        return Path(env_override)

    return Path(tempfile.gettempdir()) / "novo-voices"


class PiperVoiceRuntime:
    """Local Piper text-to-speech runtime for NOVO."""

    def __init__(self, profile: VoiceProfile = NOVO_VOICE_PROFILE, cache_dir: Path | None = None) -> None:
        self.profile = profile
        self.cache_dir = cache_dir or default_voice_cache_dir()
        self._voice: PiperVoice | None = None
        self._lock = threading.Lock()
        self._stop_requested = threading.Event()

    @property
    def sample_text(self) -> str:
        return "Hi, I'm NOVO."

    def assets(self) -> VoiceAssets:
        base = self.cache_dir / self.profile.model
        return VoiceAssets(model_path=base.with_suffix(".onnx"), config_path=base.with_suffix(".onnx.json"))

    def ensure_assets(self) -> VoiceAssets:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            download_voice(self.profile.model, self.cache_dir)
            return self.assets()
        except Exception as exc:  # noqa: BLE001
            _raise_voice_error(
                "voice_model_download",
                "NOVO could not download the Piper voice model. Check your connection or try again later.",
                exc,
            )

    def load_voice(self) -> PiperVoice:
        with self._lock:
            if self._voice is None:
                try:
                    assets = self.ensure_assets()
                    self._voice = PiperVoice.load(assets.model_path, assets.config_path, download_dir=self.cache_dir)
                except VoiceRuntimeError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    _raise_voice_error(
                        "voice_model_load",
                        "NOVO could not load the Piper voice model. The local voice files may be missing or corrupted.",
                        exc,
                    )
            return self._voice

    def warm_up(self) -> None:
        self.load_voice()

    def synthesize_to_file(self, text: str, output_path: Path) -> Path:
        cleaned = " ".join(text.split()).strip()
        if not cleaned:
            raise ValueError("Text is empty.")

        try:
            voice = self.load_voice()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output_path), "wb") as wav_file:
                voice.synthesize_wav(cleaned, wav_file, syn_config=SynthesisConfig(length_scale=self.profile.length_scale))
            return output_path
        except VoiceRuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001
            _raise_voice_error(
                "voice_synthesis",
                "NOVO could not synthesize speech with Piper. The voice profile may be incompatible.",
                exc,
            )

    def speak(self, text: str) -> bool:
        self._stop_requested.clear()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            temp_path = Path(handle.name)
        try:
            self.synthesize_to_file(text, temp_path)
            if self._stop_requested.is_set():
                return False
            audio, sample_rate = sf.read(str(temp_path), dtype="float32")
            if self._stop_requested.is_set():
                return False
            sd.play(audio, sample_rate)
            sd.wait()
            return not self._stop_requested.is_set()
        except VoiceRuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001
            _raise_voice_error(
                "voice_playback",
                "NOVO could not play audio on the current output device. Check your speakers or default audio output.",
                exc,
            )
        finally:
            temp_path.unlink(missing_ok=True)

    def stop_playback(self) -> None:
        self._stop_requested.set()
        try:
            sd.stop()
        except Exception as exc:  # noqa: BLE001
            logger.exception("NOVO voice stop failed")
            raise VoiceRuntimeError(
                "voice_stop",
                "NOVO could not stop audio playback on the current output device.",
            ) from exc

    def speak_async(
        self,
        text: str,
        *,
        on_started: Callable[[], None] | None = None,
        on_finished: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> threading.Thread:
        def worker() -> None:
            try:
                if on_started is not None:
                    on_started()
                self.speak(text)
            except VoiceRuntimeError as exc:
                if on_error is not None:
                    on_error(exc)
            except Exception as exc:  # noqa: BLE001
                logger.exception("NOVO voice worker hit an unexpected error")
                if on_error is not None:
                    on_error(VoiceRuntimeError("voice_worker", "NOVO voice encountered an unexpected error. Check the desktop terminal for details."))
            finally:
                if on_finished is not None:
                    on_finished()

        thread = threading.Thread(target=worker, name="novo-piper-tts", daemon=True)
        thread.start()
        return thread


class FasterWhisperTranscriber:
    """Local faster-whisper transcription helper for NOVO."""

    def __init__(
        self,
        model_size: str = DEFAULT_STT_MODEL,
        *,
        device: str | None = None,
        compute_type: str | None = None,
        language: str | None = "en",
    ) -> None:
        self.model_size = model_size
        self.device = _resolve_stt_device(device)
        self.compute_type = _resolve_stt_compute_type(self.device, compute_type)
        self.language = language
        self.initial_prompt = DEFAULT_TRANSCRIPTION_PROMPT
        self.hotwords = DEFAULT_TRANSCRIPTION_HOTWORDS
        self._model: WhisperModel | None = None
        self._lock = threading.Lock()

    def load_model(self) -> WhisperModel:
        with self._lock:
            if self._model is None:
                try:
                    self._model = WhisperModel(
                        self.model_size,
                        device=self.device,
                        compute_type=self.compute_type,
                    )
                except Exception as exc:  # noqa: BLE001
                    if self.device == "cuda":
                        logger.exception("NOVO STT CUDA load failed; falling back to CPU")
                        try:
                            self.device = "cpu"
                            self.compute_type = "int8"
                            self._model = WhisperModel(
                                self.model_size,
                                device=self.device,
                                compute_type=self.compute_type,
                            )
                            return self._model
                        except Exception as cpu_exc:  # noqa: BLE001
                            _raise_voice_error(
                                "stt_model_load",
                                "NOVO could not load the speech-to-text model on CUDA or CPU. The Whisper model may be unavailable.",
                                cpu_exc,
                            )
                    _raise_voice_error(
                        "stt_model_load",
                        "NOVO could not load the speech-to-text model. The Whisper model may be unavailable.",
                        exc,
                    )
            return self._model

    def _build_warmup_probe(self) -> Path:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            probe_path = Path(handle.name)
        duration_seconds = 0.25
        sample_rate = 16000
        sample_count = max(1, int(sample_rate * duration_seconds))
        timeline = np.linspace(0.0, duration_seconds, sample_count, endpoint=False, dtype=np.float32)
        waveform = (0.01 * np.sin(2.0 * np.pi * 220.0 * timeline)).astype(np.float32).reshape(-1, 1)
        sf.write(str(probe_path), waveform, sample_rate)
        return probe_path

    def warm_up(self) -> None:
        model = self.load_model()
        if self.device != "cuda":
            return
        probe_path = self._build_warmup_probe()
        try:
            try:
                self._transcribe_with_model(model, probe_path, vad_filter=False, beam_size=1, best_of=1)
            except Exception as exc:  # noqa: BLE001
                if _is_cuda_runtime_failure(exc):
                    logger.warning("NOVO STT CUDA warm-up failed; retrying on CPU", exc_info=exc)
                    cpu_model = self._switch_to_cpu_model()
                    self._transcribe_with_model(
                        cpu_model,
                        probe_path,
                        vad_filter=False,
                        beam_size=1,
                        best_of=1,
                    )
                    return
                _raise_voice_error(
                    "stt_warm_up",
                    "NOVO could not verify the speech-to-text runtime during warm-up. Check the desktop terminal for details.",
                    exc,
                )
        finally:
            probe_path.unlink(missing_ok=True)

    def runtime_summary(self) -> str:
        return f"{self.device} / {self.compute_type}"

    def _transcribe_with_model(
        self,
        model: WhisperModel,
        audio_path: Path,
        *,
        vad_filter: bool = True,
        beam_size: int = 5,
        best_of: int = 5,
    ) -> str:
        segments, _info = model.transcribe(
            str(audio_path),
            language=self.language,
            beam_size=beam_size,
            best_of=best_of,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=vad_filter,
            vad_parameters={"min_silence_duration_ms": 350},
            initial_prompt=self.initial_prompt,
            hotwords=self.hotwords,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()

    def _switch_to_cpu_model(self) -> WhisperModel:
        with self._lock:
            self.device = "cpu"
            self.compute_type = "int8"
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            return self._model

    def transcribe_file(self, audio_path: Path) -> str:
        try:
            model = self.load_model()
            return self._transcribe_with_model(model, audio_path)
        except VoiceRuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001
            if self.device == "cuda" and _is_cuda_runtime_failure(exc):
                logger.warning(
                    "NOVO STT CUDA transcription failed; retrying on CPU",
                    exc_info=exc,
                )
                try:
                    model = self._switch_to_cpu_model()
                    return self._transcribe_with_model(model, audio_path)
                except VoiceRuntimeError:
                    raise
                except Exception as cpu_exc:  # noqa: BLE001
                    _raise_voice_error(
                        "speech_transcription",
                        "NOVO could not transcribe the recording. The Whisper runtime failed on CUDA and the CPU fallback also failed.",
                        cpu_exc,
                    )
            _raise_voice_error(
                "speech_transcription",
                "NOVO could not transcribe the recording. Check the microphone audio and Whisper model.",
                exc,
            )

    def capture_seconds(
        self,
        seconds: float,
        *,
        sample_rate: int = 16000,
        channels: int = 1,
        stop_requested: Callable[[], bool] | None = None,
    ) -> AudioCaptureResult:
        try:
            block_frames = max(1, int(sample_rate * DEFAULT_CAPTURE_BLOCK_SECONDS))
            audio_chunks: list[np.ndarray] = []
            pre_speech_chunks: list[np.ndarray] = []
            noise_rms_values: list[float] = []
            saw_speech = False
            speech_started_at = 0.0
            last_voice_at = 0.0
            started_at = time.monotonic()
            queue: Queue[np.ndarray] = Queue()

            def on_audio(indata, _frames, _time_info, status) -> None:  # noqa: ANN001
                if status:
                    logger.debug("NOVO microphone callback status: %s", status)
                queue.put(np.array(indata, copy=True))

            with sd.InputStream(
                samplerate=sample_rate,
                channels=channels,
                dtype="float32",
                blocksize=block_frames,
                callback=on_audio,
            ):
                while True:
                    if stop_requested is not None and stop_requested():
                        break
                    try:
                        chunk = queue.get(timeout=0.05)
                    except Empty:
                        elapsed = time.monotonic() - started_at
                        if saw_speech and elapsed >= seconds and (time.monotonic() - last_voice_at) >= DEFAULT_SILENCE_SECONDS:
                            break
                        if not saw_speech and elapsed >= DEFAULT_INITIAL_SILENCE_SECONDS:
                            break
                        continue

                    now = time.monotonic()
                    rms = _frame_rms(chunk)
                    if not saw_speech:
                        noise_rms_values.append(rms)
                        pre_speech_chunks.append(chunk)
                        if len(pre_speech_chunks) > 4:
                            pre_speech_chunks.pop(0)

                    baseline_noise = float(np.median(noise_rms_values[-8:])) if noise_rms_values else 0.0
                    adaptive_threshold = max(
                        DEFAULT_SPEECH_THRESHOLD,
                        baseline_noise * 3.0 + 0.002,
                    )

                    if rms >= adaptive_threshold:
                        if not saw_speech:
                            saw_speech = True
                            speech_started_at = now
                            audio_chunks.extend(pre_speech_chunks)
                            pre_speech_chunks.clear()
                        last_voice_at = now
                        audio_chunks.append(chunk)
                    elif saw_speech:
                        audio_chunks.append(chunk)

                    elapsed = now - started_at
                    if saw_speech:
                        speech_duration = now - speech_started_at
                        silence_duration = now - last_voice_at
                        if speech_duration >= DEFAULT_MIN_SPEECH_SECONDS and silence_duration >= DEFAULT_SILENCE_SECONDS:
                            break
                        if elapsed >= seconds and silence_duration >= DEFAULT_SILENCE_SECONDS:
                            break
                    elif elapsed >= seconds:
                        break

            if audio_chunks:
                frames = np.concatenate(audio_chunks, axis=0)
            elif pre_speech_chunks:
                frames = np.concatenate(pre_speech_chunks, axis=0)
            else:
                frames = np.zeros((max(1, int(sample_rate * 0.2)), channels), dtype=np.float32)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
                temp_path = Path(handle.name)
            sf.write(str(temp_path), frames, sample_rate)
            return AudioCaptureResult(audio_path=temp_path, sample_rate=sample_rate, channels=channels)
        except Exception as exc:  # noqa: BLE001
            _raise_voice_error(
                "microphone_capture",
                "NOVO could not access the microphone. Check microphone permissions and the selected device.",
                exc,
            )

    def capture_and_transcribe(
        self,
        seconds: float = DEFAULT_CAPTURE_SECONDS,
        *,
        on_listening_started: Callable[[], None] | None = None,
        on_transcribing_started: Callable[[], None] | None = None,
        stop_requested: Callable[[], bool] | None = None,
    ) -> str:
        if on_listening_started is not None:
            on_listening_started()
        capture = self.capture_seconds(seconds, stop_requested=stop_requested)
        try:
            if on_transcribing_started is not None:
                on_transcribing_started()
            return self.transcribe_file(capture.audio_path)
        finally:
            capture.audio_path.unlink(missing_ok=True)
