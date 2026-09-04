"""
Speech-To-Text (STT) & Voice Listening Manager for CLIO
Provides high-performance audio transcription with multi-tier routing:
1. Cloud Groq Whisper (whisper-large-v3-turbo) - ultra-fast sub-250ms latency
2. Local Faster-Whisper (small.en / base.en) - offline neural transcription with CUDA/CPU auto-tuning
3. Google SpeechRecognition fallback
"""

import os
import io
import time
import logging
import threading
import wave
import uuid
import gc
from typing import Optional, Dict, Any, Tuple

from core.key_manager import key_manager

# Expanded domain-vocabulary prompt to bias Whisper toward CLIO commands
STT_INITIAL_PROMPT = (
    "Clio, Hey Clio, weather forecast, latest news, remind me, set a reminder, "
    "call, phone call, WhatsApp, what time is it, play music, play song, "
    "search for, Google, screenshot, take a screenshot, volume up, volume down, "
    "mute, unmute, lock screen, shutdown, restart, sleep mode, open, close, "
    "browse, download, automate, explain, summarize, write code, calculate, "
    "expenses, add expense, battery status, system health."
)

# Comprehensive hallucination filter — common Whisper phantom outputs
STT_HALLUCINATIONS = {
    "see you soon.", "see you soon", "thank you.", "thank you",
    "bye.", "bye", "you", "mbc", "amara.org", "subtitles by",
    "copyright", "all rights reserved", "silence", "stop",
    "thanks for watching.", "thanks for watching", "subscribe",
    "please subscribe", "like and subscribe", "the end", "the end.",
    "i'm going to go ahead and", "so", "um", "uh", "hmm",
    "you know", "okay", "right", "yeah", ".", "..", "...",
    "♪", "music", "applause", "laughter", "cheers",
    "thanks for listening", "good night", "good night.",
    "thank you for watching", "see you next time",
    "watching.", "watching", "closed captioning",
    "translated by", "english subtitles", "subtitles"
}


class STTManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(STTManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._local_model = None
            self._local_model_name = "small.en"
            self._model_load_lock = threading.Lock()
            self._device = "cpu"
            self._compute_type = "int8"
            self._detect_hardware()
            self.last_provider = "None"
            self.last_model = "None"
            self.last_latency_ms = 0.0
            self.initialized = True

    def _detect_hardware(self):
        """Auto-detect if CUDA is available for Faster-Whisper."""
        try:
            import torch  # type: ignore
            if torch.cuda.is_available():
                self._device = "cuda"
                self._compute_type = "float16"
                print("⚡ STT Hardware: CUDA acceleration enabled")
            else:
                self._device = "cpu"
                self._compute_type = "int8"
        except Exception:
            self._device = "cpu"
            self._compute_type = "int8"

    def get_preferred_model_name(self) -> str:
        """Get user configured STT model or default to small.en"""
        try:
            settings_path = os.path.join("userdata", "settings.json")
            if os.path.exists(settings_path):
                import json
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    return settings.get("voice", {}).get("stt_model", "small.en")
        except Exception:
            pass
        return "small.en"

    def get_local_model(self):
        """Lazy-load local Faster-Whisper model."""
        if self._local_model is not None:
            return self._local_model

        with self._model_load_lock:
            if self._local_model is not None:
                return self._local_model

            if os.environ.get("CLIO_TESTING") == "1":
                return None

            preferred = self.get_preferred_model_name()
            # Prefer multilingual models (base, small) over .en models because they are significantly better at understanding non-native accents.
            candidate_models = [preferred, "base", "small", "base.en"]
            # Deduplicate while preserving order
            models_to_try = []
            for m in candidate_models:
                if m not in models_to_try:
                    models_to_try.append(m)

            for model_name in models_to_try:
                try:
                    print(f"🧠 Loading Faster-Whisper ({model_name} on {self._device})...")
                    from faster_whisper import WhisperModel  # type: ignore
                    self._local_model = WhisperModel(
                        model_name,
                        device=self._device,
                        compute_type=self._compute_type
                    )
                    self._local_model_name = model_name
                    print(f"✅ Speech Recognition System Ready ({model_name} — Active)")
                    break
                except Exception as e:
                    print(f"⚠️ Faster-Whisper ({model_name}) load failed: {e}")

            if self._local_model is None:
                self._local_model = False  # Failed sentinel

        return self._local_model

    def is_valid_audio(self, file_path: str) -> bool:
        """Check if audio file exists, has content, and has a recognized audio magic header."""
        try:
            if not os.path.exists(file_path) or os.path.getsize(file_path) < 32:
                return False

            with open(file_path, "rb") as f:
                header = f.read(16)

            # Check common audio headers:
            # WebM / Matroska (0x1A45DFA3)
            if header[:4] == b'\x1a\x45\xdf\xa3':
                return True
            # WAV (RIFF)
            if header[:4] == b'RIFF':
                return True
            # Ogg (OggS)
            if header[:4] == b'OggS':
                return True
            # MP3 (ID3 or sync frame)
            if header[:3] == b'ID3' or (len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
                return True
            # FLAC
            if header[:4] == b'fLaC':
                return True
            # MP4 / M4A / AAC container
            if len(header) >= 8 and (b'ftyp' in header[4:12] or header[:4] == b'\xff\xf1' or header[:4] == b'\xff\xf9'):
                return True

            # If unknown format but file size is substantial (>1KB), attempt to process
            if os.path.getsize(file_path) > 1024:
                return True

            return False
        except Exception as e:
            logging.error(f"Audio validation error for {file_path}: {e}")
            return False

    def preprocess_audio(self, file_path: str) -> str:
        """Normalize audio volume and apply high-pass filter for cleaner transcription."""
        try:
            from pydub import AudioSegment  # type: ignore
            audio = AudioSegment.from_file(file_path)

            # High-pass filter at 80Hz to remove mic rumble
            audio = audio.high_pass_filter(80)  # type: ignore

            # Normalize to -20 dBFS
            target_dBFS = -20.0
            change_in_dBFS = target_dBFS - audio.dBFS
            if abs(change_in_dBFS) < 40:
                audio = audio.apply_gain(change_in_dBFS)

            # Export as 16kHz mono WAV for optimal Whisper input
            wav_path = file_path.rsplit('.', 1)[0] + '_processed.wav'
            audio.export(wav_path, format='wav', parameters=["-ar", "16000", "-ac", "1"])
            return wav_path
        except Exception:
            return file_path

    def is_hallucination(self, text: str) -> bool:
        """Check if transcribed text is a known Whisper phantom output."""
        if not text:
            return True
        cleaned = text.strip().lower().rstrip('.')
        if cleaned in STT_HALLUCINATIONS or text.strip() in STT_HALLUCINATIONS:
            return True
        if len(cleaned) <= 2 and not cleaned.isalpha():
            return True
        if len(set(cleaned.replace(' ', ''))) <= 1:
            return True
        return False

    def _transcribe_groq(self, file_path: str) -> Optional[str]:
        """Ultra-fast cloud STT using Groq Whisper (whisper-large-v3-turbo)."""
        api_key = key_manager.get_working_key("groq")
        if not api_key:
            return None

        try:
            import requests  # type: ignore
            headers = {"Authorization": f"Bearer {api_key}"}
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "audio/wav")}
                data = {
                    "model": "whisper-large-v3-turbo",
                    "prompt": STT_INITIAL_PROMPT,
                    "response_format": "json",
                    "temperature": 0.0,
                    "language": "en"
                }
                resp = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=10
                )

            if resp.status_code == 200:
                result = resp.json()
                text = result.get("text", "").strip()
                if text and not self.is_hallucination(text):
                    self.last_provider = "Groq"
                    self.last_model = "whisper-large-v3-turbo"
                    return text
            elif resp.status_code == 429:
                key_manager.report_key_failure("groq", api_key, "rate_limit")
        except Exception as e:
            logging.debug(f"Groq Whisper transcription failed: {e}")

        return None

    def _transcribe_local_whisper(self, file_path: str) -> Optional[str]:
        """Local neural transcription using Faster-Whisper."""
        model = self.get_local_model()
        if not model:
            return None

        try:
            segments, info = model.transcribe(
                file_path,
                beam_size=5,
                language="en",
                vad_filter=False,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=150
                ),
                initial_prompt=STT_INITIAL_PROMPT,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                word_timestamps=False
            )

            raw_parts = []
            filtered_parts = []
            for seg in segments:
                avg_logprob = getattr(seg, 'avg_logprob', -0.5)
                no_speech = getattr(seg, 'no_speech_prob', 0.0)
                raw_parts.append(seg.text)
                print(f"🎤 [STT Debug] Heard: '{seg.text}' (logprob: {avg_logprob:.2f}, no_speech: {no_speech:.2f})")
                if avg_logprob > -2.0 and no_speech < 0.6:
                    filtered_parts.append(seg.text)

            text = " ".join(filtered_parts).strip()
            if text and not self.is_hallucination(text):
                self.last_provider = "Faster-Whisper (Local)"
                self.last_model = self._local_model_name
                return text
        except Exception as e:
            logging.error(f"Local Faster-Whisper error: {e}")

        return None

    def _transcribe_google_fallback(self, file_path: str) -> Optional[str]:
        """SpeechRecognition Google fallback."""
        try:
            import speech_recognition as sr  # type: ignore
            r = sr.Recognizer()
            with sr.AudioFile(file_path) as source:
                audio_data = r.record(source)
            recognizer_func = getattr(r, "recognize_google", None)
            if recognizer_func:
                text = recognizer_func(audio_data, language="en-IN")
                if text and not self.is_hallucination(text):
                    self.last_provider = "Google Speech"
                    self.last_model = "Google-ASR"
                    return text.strip()
        except Exception:
            pass
        return None

    def transcribe(self, file_path: str) -> Dict[str, Any]:
        """
        Unified transcription pipeline with multi-tier routing.
        Returns:
            {"transcript": str, "language": "en", "provider": str, "model": str, "latency_ms": float}
        """
        start_time = time.time()
        result = {
            "transcript": "",
            "language": "en",
            "provider": "None",
            "model": "None",
            "latency_ms": 0.0
        }

        if not self.is_valid_audio(file_path):
            return result

        processed_path = self.preprocess_audio(file_path)
        input_audio = processed_path if processed_path != file_path else file_path

        try:
            # Tier 1: Ultra-fast Groq Whisper Cloud (if key present)
            text = self._transcribe_groq(input_audio)

            # Tier 2: Google SpeechRecognition (Fast, free, lightweight like Edge TTS)
            if not text:
                text = self._transcribe_google_fallback(input_audio)

            # Tier 3: Local Faster-Whisper Fallback
            if not text:
                text = self._transcribe_local_whisper(input_audio)

            if text and not self.is_hallucination(text):
                result["transcript"] = text
                result["provider"] = self.last_provider
                result["model"] = self.last_model
        finally:
            # Clean up preprocessed file if created
            if processed_path and processed_path != file_path and os.path.exists(processed_path):
                try:
                    os.remove(processed_path)
                except Exception:
                    pass
            gc.collect()

        latency = (time.time() - start_time) * 1000.0
        self.last_latency_ms = latency
        result["latency_ms"] = round(latency, 2)
        return result


# Global singleton instance
stt_manager = STTManager()
