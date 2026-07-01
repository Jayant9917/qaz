from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from novo_desktop.voice import NOVO_VOICE_PIPELINE, NOVO_VOICE_PROFILE, pipeline_summary, voice_summary
from novo_desktop.voice_runtime import DEFAULT_CAPTURE_SECONDS, DEFAULT_STT_MODEL, FasterWhisperTranscriber, VoiceRuntimeError, _frame_rms


class VoiceProfileTests(unittest.TestCase):
    def test_default_voice_profile_is_piper_female_english(self) -> None:
        self.assertEqual(NOVO_VOICE_PROFILE.engine, "Piper")
        self.assertEqual(NOVO_VOICE_PROFILE.model, "en_US-amy-medium")
        self.assertEqual(NOVO_VOICE_PROFILE.locale, "en_US")
        self.assertLess(NOVO_VOICE_PROFILE.length_scale, 1.0)

    def test_voice_runtime_error_exposes_user_message(self) -> None:
        error = VoiceRuntimeError("voice_playback", "NOVO could not play audio on the current output device.")
        self.assertEqual(str(error), "voice_playback: NOVO could not play audio on the current output device.")
        self.assertEqual(error.user_message, "NOVO could not play audio on the current output device.")

    def test_transcriber_defaults_bias_for_accuracy(self) -> None:
        transcriber = FasterWhisperTranscriber()
        self.assertEqual(DEFAULT_STT_MODEL, "small.en")
        self.assertEqual(transcriber.model_size, "small.en")
        self.assertEqual(transcriber.language, "en")
        self.assertGreater(DEFAULT_CAPTURE_SECONDS, 4.0)

    def test_frame_rms_detects_sound_energy(self) -> None:
        silence = np.zeros((160, 1), dtype=np.float32)
        voice = np.ones((160, 1), dtype=np.float32) * 0.03
        self.assertLess(_frame_rms(silence), 0.001)
        self.assertGreater(_frame_rms(voice), 0.01)

    def test_pipeline_mentions_expected_stages(self) -> None:
        self.assertEqual(
            NOVO_VOICE_PIPELINE,
            ("Microphone", "VAD", "faster-whisper", "NOVO backend chat API", "Streaming response", "Piper", "Speaker"),
        )
        self.assertIn("Piper", pipeline_summary())
        self.assertEqual(voice_summary(), "Piper / en_US-amy-medium")


if __name__ == "__main__":
    unittest.main()
