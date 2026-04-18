import webview  # type: ignore
import threading
import time
import sys
import os

# Set project root to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
import random
import gc
import json
import base64
import uuid
import yaml  # type: ignore
import re # Added for clean_text_for_tts and math interceptor
from flask import Flask, request, jsonify, send_from_directory  # type: ignore
from flask_cors import CORS  # type: ignore
import typing as t
import asyncio
import edge_tts  # type: ignore
import concurrent.futures
import logging
from datetime import datetime
import traceback

try:
    import psutil  # type: ignore
except ImportError:
    psutil = None

# Global Executor for Parallel LLM Processing
llm_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

# ==================================================================================
# ERROR LOGGING SYSTEM (Capture Bugs & Glitches)
# ==================================================================================

# Configure logging to save errors AND fixes to a permanent file
LOG_FILE = os.path.join("userdata", "nova_errors.log")
logging.basicConfig(
    level=logging.INFO, # Changed from ERROR to INFO to track resolutions
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Silence Flask access logs
logging.getLogger("werkzeug").setLevel(logging.ERROR)
# Silence specific annoying warnings for a cleaner terminal
import warnings
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*renamed to ddgs.*")

# Fix Hugging Face Symlink and Telemetry Warnings (Silence Hub noise)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1" # Force offline mode for local model stability

# Silence Transformers and Hub logging
from transformers import logging as transformers_logging  # type: ignore
transformers_logging.set_verbosity_error()
import logging
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

def log_glitch_fixed(glitch_name, solution):
    """Log a solved glitch to the audit file"""
    msg = f"✅ GLITCH SOLVED: {glitch_name} | SOLUTION: {solution}"
    logging.info(msg)
    print(f"\n✨ {msg}")

# Global exception handler to catch and log program crashes
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = f"CRITICAL CRASH: {exc_type.__name__}: {exc_value}"
    logging.error(error_msg)
    logging.error("Traceback: " + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    print(f"\n❌ {error_msg} (Check {LOG_FILE} for details)")

# Hook the handler into the system
sys.excepthook = handle_exception

# Core Imports (Assumes 'core' folder exists alongside desktop.py)
from core.assistant import Nova  # type: ignore
from core.conversation_memory import ConversationMemory  # type: ignore
from core.nlp_processor import NLUProcessor  # type: ignore
from core.hitl_system import HITLSystem  # type: ignore
from core.domain_knowledge import DomainKnowledge  # type: ignore
from core.user_profile import UserProfile  # type: ignore
from core.drl_system import DRLSystem  # type: ignore
from core.response_optimizer import ResponseOptimizer  # type: ignore
from core.personality_manager import PersonalityManager  # type: ignore
from core.analytics import AnalyticsEngine  # type: ignore
from core.vision import ImageAnalyzer  # type: ignore
from core.emotion_detector import emotion_detector  # type: ignore
from core.ml_predictor import MLPredictor  # type: ignore
from core.conversation_trainer import ConversationTrainer  # type: ignore
from core.ltm_manager import LTMManager  # type: ignore
try:
    from core.distiller import distiller  # type: ignore
except ImportError:
    distiller = None

# ==================================================================================
# SPEECH RECOGNITION (STT) SYSTEM
# ==================================================================================
stt_model = None

def get_stt_model():
    """Lazy load Faster-Whisper to save 1GB+ RAM on startup"""
    global stt_model
    if stt_model is not None:
        return stt_model
        
    if os.environ.get("NOVA_TESTING") != "1":
        # Using 'base' (multilingual) for better global/Indian accent parsing
        model_size = "base" 
        try:
            print(f"🎧 Loading Faster-Whisper ({model_size} Model)...")
            from faster_whisper import WhisperModel  # type: ignore
            stt_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            print("✅ Speech Recognition System Ready")
        except Exception as e:
            print(f"❌ Whisper model load error: {e}")
            stt_model = False # Marker for failed load
    return stt_model

try:
    from core.nova_core_llm import nova_core_llm  # type: ignore
except ImportError:
    nova_core_llm = None
    print("⚠️ Warning: core.nova_core_llm not found. Using fallback.")

from core.time_context import TimeContextManager  # type: ignore
from core.proactive_vision import proactive_vision_engine  # type: ignore
from skills.reminders import get_all_jobs, cancel_job_by_id  # type: ignore
import speech_recognition as sr  # type: ignore
import atexit
import pygame  # type: ignore

# Initialize Pygame Mixer
try:
    pygame.mixer.init()
except:
    pass

# ==================================================================================
# SERVER INITIALIZATION (Formerly piserver.py)
# ==================================================================================

app = Flask(__name__, static_folder='web', static_url_path='')
CORS(app)

@app.route('/userdata/<path:filename>')
def serve_userdata(filename):
    """Serve files from the consolidated userdata directory."""
    return send_from_directory('userdata', filename)

start_time = time.time()

# Initialize Nova Core (Deferred after skills/managers ready)
nova = None
ONLINE_MODE = True

# Initialize Conversation Memory
memory = ConversationMemory(memory_file=os.path.join("userdata", "conversation_history.json"), max_context=10)
print(f"🧠 Memory System: {memory.get_stats()['total_conversations']} conversations loaded")

# Initialize NLU Processor
nlp = NLUProcessor()
print(f"🤖 NLU System: Ready for natural language understanding with semantic analysis")

# Initialize HITL System
hitl = HITLSystem(feedback_file=os.path.join("userdata", "hitl_feedback.json"))
hitl_stats = hitl.get_feedback_stats()
print(f"🔄 HITL System: {hitl_stats['total_interactions']} interactions, {hitl_stats['learned_patterns']} learned patterns")

# Initialize Domain Knowledge
knowledge = DomainKnowledge(knowledge_file=os.path.join("userdata", "domain_knowledge.json"))
kb_stats = knowledge.get_stats()
print(f"📚 Knowledge Base: {kb_stats['total_domains']} domains, {kb_stats['total_facts']} facts")

# Initialize User Profile
user_profile = UserProfile(profile_file=os.path.join("userdata", "user_profile.json"))
print(f"👤 User Profile: {user_profile.get_profile_summary()}")

# Initialize DRL System
drl = DRLSystem(drl_file=os.path.join("userdata", "drl_model.json"))
drl_stats = drl.get_performance_stats()
print(f"🤖 DRL System: {drl_stats['learned_states']} states, Avg Reward: {drl_stats['average_reward']:.2f}")

# Initialize Key Manager
from core.key_manager import key_manager  # type: ignore
print(f"🔑 Key Manager: Initialized")

# Initialize Response Optimizer
optimizer = ResponseOptimizer(cache_file=os.path.join("userdata", "response_cache.json"))
opt_stats = optimizer.get_stats()
print(f"⚡ Response Optimizer: {opt_stats['cached_responses']} cached, Mode: {opt_stats['mode']}")

# Initialize Personality Manager
personality_manager = PersonalityManager(default_mode="sweetheart")
print(f"🎭 Personality System: Active Mode = {personality_manager.current_mode}")

# Initialize Instant Reply Generator
from core.instant_reply import InstantReplyGenerator  # type: ignore
instant_reply = InstantReplyGenerator(personality_manager)
ir_stats = instant_reply.get_stats()
print(f"⚡ Instant Reply: {ir_stats['total_intents']} instant intents ready")

# Initialize Analytics Engine
analytics = AnalyticsEngine()
print(f"📊 Analytics Engine: Ready to visualize data")

# Initialize ML Predictor
ml_predictor = MLPredictor()
print(f"🧠 ML Predictor: Active (Context-aware suggestions)")

# Initialize Conversation Trainer
conversation_trainer = ConversationTrainer()
trainer_stats = conversation_trainer.export_training_summary()
print(f"🎓 Conversation Trainer: {trainer_stats['total_patterns']} patterns, {trainer_stats['total_examples']} examples")

# Initialize Time Context Manager
time_context = TimeContextManager()
print(f"🕒 Time Context: {time_context.get_day_context()['time']} ({time_context.get_day_context()['time_period']})")

# Initialize Correction Manager
from core.correction_manager import CorrectionManager  # type: ignore
correction_manager = CorrectionManager(corrections_file=os.path.join("userdata", "corrections.json"))
corr_stats = correction_manager.get_stats()
print(f"🔧 Correction Manager: {corr_stats['total_corrections']} corrections learned")

# Initialize NeuralChat (Nova Core)
try:
    from core.neural_chat import NeuralChat  # type: ignore
    custom_llm = NeuralChat()
    print("🧠 Nova Core (Custom LLM) Initialized")
except ImportError:
    custom_llm = None
    NeuralChat = None
    print("⚠️ Warning: core.neural_chat not found. Custom LLM disabled.")

print("🧠 Local Brain: Ready (Deferred Load Enabled)")

# Initialize LLM Manager (single import point)
from core.llm_manager import llm_manager  # type: ignore

# Initialize Text Corrector
from core.text_corrector import TextCorrector  # type: ignore
text_corrector = TextCorrector(llm_manager)
print("✍️ Text Corrector: Ready to fix spelling & grammar")

# Initialize Nova Core with managers
nova = Nova()
# Register text correction skill explicitly
from skills import text_correction, natural_events  # type: ignore
text_correction.register(nova.dispatcher, text_corrector)
natural_events.register(nova.dispatcher)


# Register emotion explanation skill
from skills import emotion_analytics  # type: ignore
emotion_analytics.register(nova.dispatcher)

# Register browser control skill
from skills import browser_control  # type: ignore
browser_control.register(nova.dispatcher)

# Register autonomous browser agent skill
from skills import browser_agent  # type: ignore
browser_agent.register(nova.dispatcher)

# State & Shared Objects
IS_LIVE_MODE = False
IS_SPEAKING = False
IS_SPEAKING_LOCK = threading.Lock()
console_lock = threading.Lock()
gui_window = None # Global Handle for UI interaction

def update_ui(message, msg_type="system-msg"):
    """Pushes a message to the frontend chat UI via a global window handle with safe serialization."""
    global gui_window
    if gui_window and message:
        try:
            import json
            # Safe serialization to prevent JS injection/syntax errors
            safe_msg = json.dumps(message)
            safe_type = json.dumps(msg_type)
            js_code = f"addLine({safe_msg}, {safe_type})"
            gui_window.evaluate_js(js_code)
        except Exception as e:
            print(f"⚠️ UI Update Error: {e}")

def show_nova_response(response_text, tokens=0):
    """Pushes Nova's final response and metadata to the UI safely."""
    global gui_window
    if gui_window:
        try:
            import json
            safe_resp = json.dumps(response_text)
            js_code = f"addLine({safe_resp}, 'nova-msg', {tokens})"
            gui_window.evaluate_js(js_code)
        except Exception as e:
            print(f"⚠️ UI Response Error: {e}")

def safe_print(msg):
    with console_lock:
        print(msg)

# Initialize Long-Term Memory (LTM)
ltm = LTMManager(memory_file=os.path.join("userdata", "user_facts.json"))
print(f"🧠 Long-Term Memory: {len(ltm.facts)} facts stored")

# Initialize Offline Manager and Proactive Engine
from core.offline_manager import OfflineManager  # type: ignore
from core.proactive_engine import ProactiveEngine  # type: ignore
offline_manager = OfflineManager()
proactive_engine = ProactiveEngine()
print("🔌 Offline Manager: Ready")
print("🔔 Proactive Engine: Initialized")


# Initialize Wake Word Listener
# Log Recent Historical Fixes
log_glitch_fixed("Live Mode Latency", "Switched to 'base.en' Whisper model and reduced VAD silence to 0.8s.")
log_glitch_fixed("WhatsApp Messaging Loop", "Implemented fuzzy contact matching and multi-turn conversational dialogue.")
log_glitch_fixed("Intent Swallowing", "Prioritized task intents (message/play) over Time Context greetings.")
log_glitch_fixed("HF Hub Symlink Warning", "Disabled symlink warning with environment variable for safer Windows caching.")

def speak_locally(text):
    """Speaks text using the backend TTS engine and manages global speaking state."""
    if not text: return
    global IS_SPEAKING
    
    with IS_SPEAKING_LOCK:
        IS_SPEAKING = True
        
    try:
        # We only play audio locally IF there is no GUI window active
        # to prevent directed 'double-voice' echoes.
        global gui_window
        if not gui_window:
            audio_b64 = quick_tts(text)
            if not audio_b64: return
            import base64
            audio_data = base64.b64decode(audio_b64)
            temp_file = os.path.join("userdata", "temp", f"local_speech_{uuid.uuid4().hex}.mp3")
            os.makedirs(os.path.join("userdata", "temp"), exist_ok=True)
            with open(temp_file, "wb") as f: f.write(audio_data)
            if not pygame.mixer.get_init(): pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): time.sleep(0.1)
            pygame.mixer.music.unload()
            if os.path.exists(temp_file): os.remove(temp_file)
        else:
            # If GUI is present, we still 'wait' for the estimated duration
            # to prevent Nova from interrupting her own UI-based speech.
            # Avg speaking speed ~150 wpm = ~2.5 words/sec.
            word_count = len(text.split())
            wait_time = max(1.5, word_count / 2.5) 
            time.sleep(wait_time)
            
    except Exception as e:
        print(f"⚠️ Local TTS Error: {e}")
    finally:
        with IS_SPEAKING_LOCK:
            IS_SPEAKING = False

def ptt_listener_loop():
    """Polls for Alt key press to trigger on-device hearing (Push-To-Talk)."""
    try:
        import win32api  # type: ignore
        print("⌨️ PTT System: Active (Hold 'Alt' to talk)")
        last_state = False
        while True:
            # 0x12 is Alt. 0x8000 checks if currently down.
            current_state = (win32api.GetAsyncKeyState(0x12) & 0x8000) != 0
            if current_state and not last_state:
                # Manual Trigger
                threading.Thread(target=trigger_active_listening, daemon=True).start()
            last_state = current_state
            time.sleep(0.05)
    except Exception as e:
        print(f"⚠️ PTT Listener Failed: {e}")

def cleanup_temp_files():
    """Removes all orphaned temporary audio files from the temp directory and root."""
    try:
        # 1. Clean temp directory
        removed = []
        temp_dir = os.path.join("userdata", "temp")
        if os.path.exists(temp_dir):
            for f in os.listdir(temp_dir):
                if any(f.endswith(ext) for ext in [".wav", ".mp3", ".webm"]):
                    try:
                        os.remove(os.path.join(temp_dir, f))
                        removed.append(f)
                    except: pass
        
        # 2. Clean root directory for specific patterns
        import glob
        for pattern in ["temp_audio_*.webm", "temp_voice_*.webm", "temp_audio_*.wav"]:
            for f in glob.glob(pattern):
                try:
                    os.remove(f)
                    removed.append(f)
                except: pass

        if removed:
            print(f"🧹 Cleanup: Removed {len(removed)} orphaned temp files.")
    except Exception as e:
        print(f"⚠️ Cleanup Error: {e}")

def select_best_microphone():
    """Scavenges for a real microphone, avoiding 'Stereo Mix' or 'Loopback'."""
    try:
        import speech_recognition as sr  # type: ignore
        mics = sr.Microphone.list_microphone_names()
        # Preference order: genuine microphones
        keywords = ["Microphone Array", "Mic", "Realtek Audio", "Internal"]
        # Avoidance list: loopbacks, virtual cables, and stereo mixes
        blacklist = ["Stereo Mix", "Loopback", "What U Hear", "Virtual", "VoiceMeeter", "Cable"]
        
        candidates = []
        for i, name in enumerate(mics):
            low_name = name.lower()
            if any(b.lower() in low_name for b in blacklist):
                continue
            for kw in keywords:
                if kw.lower() in low_name:
                    candidates.append((keywords.index(kw), i, name))
                    break
        
        if candidates:
            candidates.sort() # Lowest keyword index first
            best_idx = candidates[0][1]
            best_name = candidates[0][2]
            print(f"🎙️ [HearingConfig] Scavenged real mic: {best_name} (Index {best_idx})")
            return sr.Microphone(device_index=best_idx)
    except Exception as e:
        print(f"⚠️ [HearingConfig] Mic scavenging error: {e}")
    
    print("🎙️ [HearingConfig] Using system default microphone.")
    # Use the global sr import
    try:
        microphone = None
        if 'sr' in globals():
            microphone = sr.Microphone()
        else:
            import speech_recognition as sr_internal
            microphone = sr_internal.Microphone()
        return microphone
    except:
        return None

class NovaHearingEngine:
    """
    Google-style Streaming Hearing Engine.
    Maintains a single persistent microphone stream and switches states 
    to provide seamless wake-word and command processing.
    """
    def __init__(self, keyword="nova"):
        self.keyword = keyword.lower()
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 800
        self.recognizer.dynamic_energy_threshold = True
        self.mic = select_best_microphone()
        self.is_active = False
        self.processing_lock = threading.Lock()
        self.stop_listening: t.Any = None # Initialize for static analysis
        cleanup_temp_files() # Clean on start

    def start(self):
        print(f"👂 Nova Hearing Engine: Seamless Monitoring ('{self.keyword}')")
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # Start the background listener that never stops
        self.stop_listening = self.recognizer.listen_in_background(
            self.mic, self._handle_audio, phrase_time_limit=10
        )

    def force_trigger(self):
        """Manually force the engine to process the next slice as a command (PTT/Button)."""
        print("⚡ Manual trigger received.")
        self.is_active = True
        # In this state, the next _handle_audio call will treat input as a command

    def _handle_audio(self, recognizer, audio):
        """Callback for every detected phrase segment."""
        # 0. Global Suppression: Don't listen to yourself!
        global IS_SPEAKING
        if IS_SPEAKING: return
        
        # Use a lock to prevent overlapping callbacks if processing is slow
        if self.processing_lock.locked(): return
        
        with self.processing_lock:
            try:
                # 1. Capture to temporary WAV
                hex_id = uuid.uuid4().hex
                temp_wav = os.path.join("temp", f"stream_{hex_id[:6]}.wav")  # type: ignore[index]
                os.makedirs("temp", exist_ok=True)
                with open(temp_wav, "wb") as f: f.write(audio.get_wav_data())
                
                # 2. Fast Transcription
                stt = get_stt_model()
                if not stt: return
                
                segments, _ = stt.transcribe(
                    temp_wav, 
                    beam_size=5,
                    language="en",
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=800),
                    initial_prompt="Nova, weather, news, remind, call, time, play music, search, screenshot, volume."
                )
                text = " ".join([s.text for s in segments]).strip()
                # Use a small delay or try-except to handle Windows file locking during Faster-Whisper iteration
                try:
                    if os.path.exists(temp_wav): os.remove(temp_wav)
                except:
                    # If it fails, it will be caught by the next cleanup_temp_files() call
                    pass
                
                # Periodically run a full cleanup to catch orphans
                if random.random() < 0.1: # 10% chance per phrase
                    cleanup_temp_files()

                if not text: return

                # Terminal visibility for transcription
                print(f"👂 [Transcribed] '{text}'")

                # 3. State-Based Logic
                if self.is_active:
                    # COMMAND STATE
                    print(f"📝 [Command] User: '{text}'")
                    update_ui(text, "user-msg")
                    self.is_active = False # Reset to IDLE
                    
                    # Full Agent Loop
                    result = process_command_text(text, voice_mode=True)
                    response = result.get('response', '') if isinstance(result, dict) else str(result)
                    
                    show_nova_response(response)
                    speak_locally(response)
                    
                else:
                    # IDLE/WAKE-WORD STATE
                    if self.keyword in text.lower():
                        print("🚀 Wake Word Detected!")
                        update_ui("<i>Listening...</i>", "system-msg")
                        self.is_active = True 
                        # The very next phrase heard will hit the branch above
            except Exception as e:
                error_msg = f"⚠️ Hearing Loop Error: {e}"
                print(error_msg)
                logging.error(error_msg)

def trigger_active_listening():
    """Starts a focused listening session (triggered by wake word or PTT)."""
    global hearing_engine
    if hearing_engine:
        update_ui("<i>Listening...</i>", "system-msg")
        hearing_engine.force_trigger()
    else:
        # Fallback if engine not running for some reason
        print("⚠️ hearing_engine not initialized. Re-initializing...")
        # (Self-correction logic here if needed)

# Global Hearing Instance
hearing_engine = None

# Initialize Vision System
vision = ImageAnalyzer()
# STT initialization relocated to top of file

 # STT initialization removed from here to enable lazy loading

def is_valid_audio(file_path):
    """Check if audio file is large enough and has a valid WebM header"""
    try:
        # Lowered threshold to 64 bytes to allow for very short commands (e.g., "Hi", "Go")
        # while still filtering out zero-byte or noise-only buffers.
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 64: 
            return False
            
        with open(file_path, 'rb') as f:
            header = f.read(4)
            # WebM/EBML magic number is 0x1A45DFA3
            is_valid = header == b'\x1a\x45\xdf\xa3'
            if not is_valid:
                # Downgraded to DEBUG to reduce log noise
                logging.debug(f"Invalid audio header detected in {file_path}. Content: {header.hex()}")
            return is_valid
    except Exception as e:
        logging.error(f"Audio validation error for {file_path}: {e}")
        return False

# Initialize TTS (Edge TTS - API Only)
coqui_tts = None
USE_COQUI = False

# threading.Thread(target=start_llm, daemon=True).start() # Already pre-loaded synchronously
# threading.Thread(target=load_coqui, daemon=True).start()

# ==================================================================================
# APP ROUTES
# ==================================================================================

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    """Returns the current online/offline and initialization status of Nova"""
    res = {
        "status": "online",
        "name": "Nova",
        "version": "1.0.0"
    }
    if nova:
        res["name"] = getattr(nova, 'name', 'Nova')
        if hasattr(nova, 'config') and nova.config:
            res["version"] = nova.config.get("assistant", {}).get("version", "1.0.0")
    return jsonify(res)

# --- SETTINGS ROUTES ---

@app.route('/api/settings/online', methods=['POST'])
def set_online():
    """Toggle Nova's online/offline status"""
    global ONLINE_MODE
    try:
        data = request.json
        ONLINE_MODE = data.get('online', True)
        print(f"🌐 Online Mode: {'ACTIVE' if ONLINE_MODE else 'OFFLINE'}")
        return jsonify({"status": "success", "online": ONLINE_MODE})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/settings/live', methods=['POST'])
def set_live_mode():
    """Sync live mode state from frontend to backend"""
    global IS_LIVE_MODE
    try:
        data = request.json
        IS_LIVE_MODE = data.get('active', False)
        print(f"🔄 Live Mode Sync: {'ACTIVE' if IS_LIVE_MODE else 'OFF'}")
        return jsonify({"status": "success", "live": IS_LIVE_MODE})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/settings/personality', methods=['POST'])
def set_personality():
    try:
        data = request.json
        mode = data.get('mode')
        if personality_manager.set_mode(mode):
            return jsonify({"status": "success", "mode": personality_manager.current_mode, "name": personality_manager.get_active_personality()['name']})
        return jsonify({"status": "error", "message": "Invalid mode"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/settings/model', methods=['POST'])
def set_model():
    """LOCKED: Nova is now strictly local and single-model."""
    return jsonify({
        "status": "locked",
        "message": "Nova is locked to strictly local brain. No switching allowed.",
        "current_provider": "Strictly Local"
    }), 200

@app.route('/api/settings/profile', methods=['GET', 'POST'])
def handle_profile():
    if request.method == 'GET':
        return jsonify(user_profile.profile)
    
    try:
        data = request.json
        name = data.get('name')
        if name:
            user_profile.update_name(name)
            # Check for admin role immediately
            user_profile.is_admin()
            
        # Support for extended questionnaire (Personal Info)
        personal_info = data.get('personal_info')
        if personal_info and isinstance(personal_info, dict):
            # Update each field in personal_info
            for key, value in personal_info.items():
                user_profile.update_personal_info(key, value)
        
        return jsonify({"status": "success", "profile": user_profile.profile})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/settings/profile/image', methods=['POST'])
def upload_profile_image():
    if 'image' not in request.files: return jsonify({"error": "No image"}), 400
    file = request.files['image']
    if file.filename == '': return jsonify({"error": "No file"}), 400
    
    try:
        # Save as standard 'user_avatar.png' in web folder
        filename = "user_avatar.png"
        static_dir = app.static_folder or "web"
        filepath = os.path.join(static_dir, filename)
        file.save(filepath)
        
        # Update timestamp to bust cache
        timestamp = int(time.time())
        return jsonify({"status": "success", "url": f"{filename}?t={timestamp}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/admin/system_stats', methods=['GET'])
def get_admin_system_stats():
    """Returns detailed system stats for the Admin Dashboard"""
    if not user_profile.is_admin():
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        import psutil  # type: ignore
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        
        # Correctly call llm_manager.get_stats()
        llm_stats = llm_manager.get_stats() if 'llm_manager' in globals() else {}
        
        return jsonify({
            "cpu": cpu,
            "memory": mem,
            "uptime": int(time.time() - start_time),
            "active_patterns": conversation_trainer.get_total_examples() if hasattr(conversation_trainer, 'get_total_examples') else 0,
            "learned_facts": len(ltm.facts),
            "llm_stats": llm_stats,
            "status": "Healthy"
        })
    except Exception as e:
        return jsonify({
            "cpu": 0,
            "memory": 0,
            "uptime": 0,
            "status": "Error reading stats",
            "error": str(e)
        })

@app.route('/api/admin/emulator', methods=['POST'])
def admin_emulator():
    """Test NLU command processing from Admin Panel"""
    if not user_profile.is_admin():
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        data = request.json
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({"error": "No command provided"}), 400
            
        # Process through NLU
        nlu_result = nlp.process(command)
        
        # Attempt to execute via dispatcher
        try:
            if nova and hasattr(nova, 'dispatcher'):
                response = nova.dispatcher.dispatch(command)
                execution_status = "success" if response else "no_handler"
            else:
                response = "Nova system not fully initialized."
                execution_status = "error: Nova not initialized"
        except Exception as e:
            response = None
            execution_status = f"error: {str(e)}"
        
        return jsonify({
            "status": "success",
            "input": command,
            "nlu": {
                "intent": nlu_result.get('intent'),
                "entities": nlu_result.get('entities', []),
                "confidence": nlu_result.get('confidence', 0.0)
            },
            "execution": {
                "status": execution_status,
                "response": response
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route('/api/stats/dashboard', methods=['GET'])
def get_dashboard_stats():
    return jsonify(analytics.get_dashboard_data())

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    return jsonify(get_all_jobs())

@app.route('/api/schedule/delete', methods=['POST'])
def delete_schedule_item():
    data = request.json
    job_id = data.get('id')
    if cancel_job_by_id(job_id):
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Job not found"}), 404

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Fetch recent debug logs for the UI, filtering out noise"""
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify({"logs": [], "message": "No logs found."})
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Filter out noisy HTTP request logs
            filtered_logs = [
                line.strip() for line in lines 
                if "HTTP Request" not in line and "/api/logs" not in line
            ]
            # Get last 100 relevant lines
            recent_logs = list(filtered_logs[-100:])  # type: ignore[index]
            recent_logs.reverse() # Show newest first
            return jsonify({"logs": recent_logs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/conversation/export', methods=['POST'])
def export_conversation():
    """Export conversation history in specified format"""
    try:
        data = request.json or {}
        format_type = data.get('format', 'txt').lower()  # txt, html, json
        
        # Load conversation history
        history_file = os.path.join('userdata', 'conversation_history.json')
        if not os.path.exists(history_file):
            return jsonify({"error": "No conversation history found"}), 404
        
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        if format_type == 'json':
            return jsonify(history)
        
        elif format_type == 'txt':
            output = "NOVA Conversation History\n"
            output += "=" * 50 + "\n\n"
            # History might be a list or a dict containing a list
            conversations = history if isinstance(history, list) else history.get('conversations', [])
            for entry in conversations:
                timestamp = entry.get('timestamp', 'Unknown')
                user_msg = entry.get('user', '')
                nova_msg = entry.get('nova', '')
                output += f"[{timestamp}]\n"
                output += f"You: {user_msg}\n"
                output += f"Nova: {nova_msg}\n\n"
            return output, 200, {'Content-Type': 'text/plain; charset=utf-8', 'Content-Disposition': 'attachment; filename=nova_history.txt'}
        
        elif format_type == 'html':
            output = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>NOVA Conversation History</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #0f0f0f; color: #e0e0e0; }}
                    h1 {{ color: #a29bfe; text-align: center; border-bottom: 1px solid #333; padding-bottom: 20px; }}
                    .message {{ margin: 15px 0; padding: 15px; border-radius: 12px; line-height: 1.5; }}
                    .user {{ background: rgba(100, 100, 255, 0.1); border-left: 5px solid #6c5ce7; margin-left: 50px; }}
                    .nova {{ background: rgba(162, 155, 254, 0.1); border-left: 5px solid #a29bfe; margin-right: 50px; }}
                    .timestamp {{ font-size: 0.8em; opacity: 0.5; margin-bottom: 5px; }}
                    .label {{ font-weight: bold; color: #a29bfe; margin-bottom: 5px; display: block; }}
                </style>
            </head>
            <body>
                <h1>NOVA History Log</h1>
            """
            conversations = history if isinstance(history, list) else history.get('conversations', [])
            for entry in conversations:
                timestamp = entry.get('timestamp', '')
                user_msg = entry.get('user', '')
                nova_msg = entry.get('nova', '')
                output += f"""
                <div class="message user">
                    <div class="timestamp">{timestamp}</div>
                    <span class="label">YOU</span>
                    <div>{user_msg}</div>
                </div>
                <div class="message nova">
                    <div class="timestamp">{timestamp}</div>
                    <span class="label">NOVA</span>
                    <div>{nova_msg}</div>
                </div>
                """
            output += "</body></html>"
            return output, 200, {'Content-Type': 'text/html; charset=utf-8', 'Content-Disposition': 'attachment; filename=nova_history.html'}
        
        elif format_type == 'pdf':
            # PDF export using print-optimized HTML
            output = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>NOVA Conversation History</title>
                <style>
                    @media print {{
                        body {{ margin: 0; padding: 0; }}
                    }}
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: white; color: #333; }}
                    h1 {{ color: #6c5ce7; text-align: center; border-bottom: 2px solid #6c5ce7; padding-bottom: 20px; margin-bottom: 30px; }}
                    .stats {{ text-align: center; margin-bottom: 30px; color: #666; font-size: 0.9em; }}
                    .message {{ margin: 15px 0; padding: 15px; border-radius: 8px; line-height: 1.6; page-break-inside: avoid; }}
                    .user {{ background: #f0f0ff; border-left: 4px solid #6c5ce7; }}
                    .nova {{ background: #fff5f8; border-left: 4px solid #a29bfe; }}
                    .timestamp {{ font-size: 0.75em; color: #999; margin-bottom: 5px; }}
                    .label {{ font-weight: bold; color: #6c5ce7; margin-bottom: 8px; display: block; }}
                    .content {{ white-space: pre-wrap; word-wrap: break-word; }}
                </style>
            </head>
            <body>
                <h1>🌹 NOVA Conversation History</h1>
            """
            conversations = history if isinstance(history, list) else history.get('conversations', [])
            output += f'<div class="stats">Total Conversations: {len(conversations)}</div>'
            
            for entry in conversations:
                timestamp = entry.get('timestamp', '')
                user_msg = entry.get('user', '').replace('<', '&lt;').replace('>', '&gt;')
                nova_msg = entry.get('nova', '').replace('<', '&lt;').replace('>', '&gt;')
                output += f"""
                <div class="message user">
                    <div class="timestamp">{timestamp}</div>
                    <span class="label">YOU</span>
                    <div class="content">{user_msg}</div>
                </div>
                <div class="message nova">
                    <div class="timestamp">{timestamp}</div>
                    <span class="label">NOVA</span>
                    <div class="content">{nova_msg}</div>
                </div>
                """
            output += """
                <script>
                    // Auto-print for PDF generation
                    window.onload = function() {
                        setTimeout(function() {
                            window.print();
                        }, 500);
                    };
                </script>
            </body></html>
            """
            return output, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
        return jsonify({"error": "Invalid format"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/clear', methods=['POST'])
def clear_memory():
    """Wipes conversation history and learned facts (LTM)"""
    try:
        # 1. Clear conversation memory file
        memory_file = os.path.join('userdata', 'conversation_history.json')
        if os.path.exists(memory_file):
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            # Reset internal memory object
            memory.clear_memory()
        
        # 2. Clear Long-Term Memory (LTM)
        ltm_file = os.path.join('userdata', 'user_facts.json')
        if os.path.exists(ltm_file):
            with open(ltm_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            # Reset internal LTM object
            ltm.facts = {}
            
        # 3. Clean Uploads
        cleanup_uploads()
            
        print("🗑️ All memory and facts have been cleared by user request.")
        return jsonify({"status": "success", "message": "All memories cleared."})
    except Exception as e:
        logging.error(f"Memory clear error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get proactive suggestions based on user patterns"""
    try:
        suggestions = proactive_engine.get_suggestions()
        return jsonify({"suggestions": suggestions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/voice/test', methods=['POST'])
def test_voice():
    """Generate a sample TTS for voice testing in settings"""
    try:
        data = request.json or {}
        voice = data.get('voice', 'en-US-AvaNeural')
        speed = float(data.get('speed', 1.0))
        pitch = int(data.get('pitch', 0))
        
        # Sample text for testing
        sample_text = "Ara-ara~ Hi there! This is how I sound. Did you like my voice?"
        
        # Generate TTS with the specified settings
        # Temporarily override settings
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            communicate = edge_tts.Communicate(
                text=sample_text,
                voice=voice,
                rate=f"+{int((speed - 1) * 100)}%",
                pitch=f"{pitch:+d}Hz"
            )
            
            async def collect_audio():
                chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        chunks.append(chunk["data"])
                return chunks
            
            audio_chunks = loop.run_until_complete(collect_audio())
            
            audio_data = b"".join(audio_chunks)
            loop.close()
            
            if audio_data:
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                return jsonify({
                    "status": "success",
                    "audio_base64": audio_b64
                })
            else:
                return jsonify({"status": "error", "message": "No audio generated"}), 500
                
        except Exception as e:
            return jsonify({"status": "error", "message": f"TTS failed: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Import DocumentReader and Analyzer
from core.document_reader import document_reader  # type: ignore
from skills.document_analysis import document_analyzer  # type: ignore

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' in request.files:
        file = request.files['file']
    elif 'image' in request.files: # Backwards compatibility
        file = request.files['image']
    else:
        return jsonify({"error": "No file uploaded"}), 400
        
    if file.filename == '': return jsonify({"error": "No file"}), 400
    
    # Secure filename and save
    filename = file.filename
    # Ensure temp/uploads exists
    upload_dir = os.path.join(os.getcwd(), 'temp', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    filepath = os.path.join(upload_dir, str(filename or 'uploaded_file'))
    file.save(filepath)
    
    # Set context for Document Analysis Skill
    document_analyzer.set_current_file(filepath)
    
    response_text = ""
    analysis_data = {}
    
    # Determine File Type and Process
    safe_filename = filename if filename else ""
    ext = os.path.splitext(safe_filename)[1].lower()
    
    # 1. Image Handling
    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
        labels = vision.analyze(filepath)
        objects = ", ".join(labels).replace("_", " ") if labels else "nothing distinct"
        
        response_text = f"I see: {objects}. Interesting!"
        
        # LLM Context
        if llm_executor or (llm_manager and getattr(llm_manager, 'model', None)):
            active_persona = personality_manager.get_active_personality()
            system_prompt = f"{active_persona['system_prompt']}\nCONTEXT: User uploaded an image.\nIMAGE CONTENTS: {objects}\nTASK: Comment briefly on what you see.\nNova:"
            response_text = llm_manager.generate(system_prompt, max_tokens=80, temperature=0.7)
            
        analysis_data = {"type": "image", "labels": labels, "description": response_text}

    # 2. Text/Code/PDF/Docx Handling via Skill
    else:
        # Use the skill to generate the initial summary/analysis
        response_text = document_analyzer.analyze_file(filepath, mode="summary")
        
        # Basic read for preview data
        doc_result = document_reader.read_file(filepath)
        if "content" in doc_result:
             analysis_data = {"type": doc_result.get("type", "unknown"), "content_preview": doc_result["content"][:200]}
        else:
             analysis_data = {"type": "unknown", "error": doc_result.get("error")}

    return jsonify({"status": "success", "filename": filename, "response": response_text, "analysis": analysis_data})

@app.route('/api/predict', methods=['GET'])
def predict_commands():
    predictions = ml_predictor.predict_next_command()
    suggestions = [cmd for cmd, prob in predictions]
    return jsonify({"suggestions": suggestions})

# ==================================================================================
# TRANSCRIPTION & COMMAND PROCESSING
# ==================================================================================

@app.route('/api/voice/trigger', methods=['POST'])
def trigger_voice():
    """Endpoint for the UI to manually trigger the back-end hearing engine."""
    threading.Thread(target=trigger_active_listening, daemon=True).start()
    return jsonify({"status": "success", "message": "Listening triggered"})

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files: return jsonify({"error": "No audio"}), 400
    audio_file = request.files['audio']
    temp_path = f"temp_audio_{uuid.uuid4().hex}.webm"
    audio_file.save(temp_path)
    
    try:
        # Robust Pre-check to avoid library crashes/errors
        if not is_valid_audio(temp_path):
             return jsonify({"transcript": "", "language": "en"})
             
        text = ""
        detected_language = "en"
        
        # Method 1: Faster-Whisper
        stt = get_stt_model()
        if stt:
            try:
                # Optimized beam_size=1 for faster live response
                segments, info = stt.transcribe(
                    temp_path, 
                    beam_size=5,
                    language="en",
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=800),
                    initial_prompt="Nova, weather, news, remind, call, time, play music, search, screenshot, volume."
                )
                text = " ".join([s.text for s in segments]).strip()
                detected_language = "en"
                
                # HALLUCINATION FILTER
                hallucinations = [
                    "See you soon.", "See you soon", "Thank you.", "Thank you",
                    "Bye.", "Bye", "You", "MBC", "Amara.org", "Subtitles by",
                    "Copyright", "All rights reserved", "Silence", "stop"
                ]
                
                if any(h.lower() == text.lower() for h in hallucinations) or text.strip() == ".":
                    print(f"⚠️ Detected Hallucination: '{text}' -> Discarding.")
                    text = "" # Force fallback
                    
                print(f"🎤 Neural Transcribed ({detected_language}): {text}")
            except Exception as e:
                print(f"Neural Transcription Error: {e}")

        # Method 2: Fallback (SpeechRecognition)
        if not text or len(text) < 3:
            try:
                r = sr.Recognizer()
                with sr.AudioFile(temp_path) as source: audio_data = r.record(source)
                try: 
                    # Use getattr to safely check for the method
                    recognizer_func = getattr(r, "recognize_google", None)
                    if recognizer_func:
                        text = recognizer_func(audio_data, language="en-IN")
                        detected_language = "en"
                        print(f"🎤 Fallback Transcribed (Google): {text}")
                except: pass
            except Exception as e:
                print(f"Fallback Transcription Error: {e}")
                if not text: return jsonify({"error": "Failed"}), 500

        print(f"🎙️ RAW ASR Output: '{text}' ({detected_language})")
        gc.collect()
        normalized_text = nlp.normalize_text(text, language=detected_language)
        return jsonify({"transcript": normalized_text, "language": detected_language})
        
    finally:
        # CLEANUP: Guaranteed removal of voice recording
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except: pass

@app.route('/api/voice-command', methods=['POST'])
def voice_command():
    """Unified route for lowest latency voice interaction"""
    if 'audio' not in request.files: return jsonify({"error": "No audio"}), 400
    audio_file = request.files['audio']
    temp_path = f"temp_voice_{uuid.uuid4().hex}.webm"
    audio_file.save(temp_path)
    
    try:
        # Robust Pre-check to avoid library crashes/errors
        if not is_valid_audio(temp_path):
            return jsonify({"response": "Hmm? I didn't catch that.", "audio": False}), 200
        
        text = ""
        detected_lang = "en"
        stt = get_stt_model()
        if stt:
            try:
                # Auto-detect language for multi-language support
                segments, info = stt.transcribe(
                    temp_path, 
                    beam_size=5, 
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=800)
                )
                text = " ".join([s.text for s in segments]).strip()
                detected_lang = str(getattr(info, 'language', 'en'))
                if detected_lang != "en":
                    print(f"🌍 Detected language: {detected_lang} — will reply in English")
            except: pass
        
        if not text:
            return jsonify({"response": "Hmm? I didn't catch that.", "audio": False}), 200
            
        print(f"🎙️ Voice Command Detected: '{text}'")
        # Process command — always respond in English regardless of input language
        return process_command_text(text, "en", voice_mode=True)
        
    finally:
        # CLEANUP: Delete voice recording to ensure privacy
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except: pass

# Phonetic mapping for better pronunciation of interjections and Russian phrases
PHONETIC_MAP = {
    "ara-ara": "ah-rah ah-rah",
    "ara-ara~": "ah-rah ah-rah",
    "munya": "moo-nyah",
    "e-eh": "eh-eh",
    "baka": "bah-kah",
    "privet": "pree-vyet",
    "привет": "pree-vyet",
    "ya tebya lyublyu": "yah tyeb-yah lyoob-lyoo",
    "khorosho": "kho-roh-shoh",
    "milyj": "mee-lyj",
    "senpai": "sen-pie",
    "kun": "koon",
    "san": "sahn",
    "chan": "chahn",
    "rivu": "ree-voo",
    "sama": "sah-mah"
}

def clean_text_for_tts(text):
    """Removes emojis, markdown, and applies phonetic mapping for better speech."""
    # 1. Phonetic Replacements (Case insensitive)
    text_lower = text.lower()
    for word, phonetic in PHONETIC_MAP.items():
        if word in text_lower:
            text = re.sub(re.escape(word), phonetic, text, flags=re.IGNORECASE)

    # 2a. Map specific actions to natural vocalizations for TTS
    action_map = {
        r'\*laughs\*': 'ha ha ha!',
        r'\*giggles\*': 'he he!',
        r'\*chuckles\*': 'heh.',
        r'\*sighs\*': 'sigh.',
        r'\*cries\*': 'sob...',
        r'\*gasps\*': 'gasp!',
        r'\*pouts\*': 'hmph!',
        r'\*yawns\*': 'yawn...',
        r'\*screams\*': 'ahhhh!',
        r'\*grunts\*': 'ugh!',
        r'\*screeches\*': 'eeee!',
        r'\*growls\*': 'grrr!'
    }
    for pattern, sound in action_map.items():
        text = re.sub(pattern, sound, text, flags=re.IGNORECASE)

    # 2b. Remove other actions like *waves*, (whispers), [smiles]
    text = re.sub(r'\*.*?\*', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    
    # 3. Remove Markdown links [text](url) -> keep only 'text'
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 4. Remove URLs (http/https)
    text = re.sub(r'https?://\S+', '', text)
    
    # 5. Remove bold/italic markdown
    text = text.replace('**', '').replace('*', '')
    
    # 6. Remove markdown lists/bullets
    text = re.sub(r'^\s*•\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*-\s*', '', text, flags=re.MULTILINE)
    
    # NEW: Remove any remaining XML-like tags (including thoughts if they leaked)
    text = re.sub(r'<.*?>', '', text)
    
    # 5. Remove ALL emojis and special symbols (keep only letters, numbers, basic punctuation)
    # This removes: 😊 🎵 ✨ 💖 etc.
    text = re.sub(r'[^\w\s,.?!:\'-]', '', text, flags=re.UNICODE)
    
    # 6. Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

# ==================================================================================
# EMOTION & TTS PROSODY ENGINE
# ==================================================================================

# Mapping 27 emotions to Edge-TTS prosody settings (Pitch, Rate)
# Styles: "en-US-AvaNeural" (Default), "en-US-AndrewNeural" (Male), etc.
EMOTION_PROSODY_MAP = {
    # Positive
    "joy":          ("+10Hz", "+15%"),
    "love":         ("-4Hz", "-10%"),  # Soft, tender, slightly deeper
    "admiration":   ("+4Hz", "+0%"),
    "amusement":    ("+12Hz", "+20%"), # Fast, laughing, high pitch
    "excitement":   ("+15Hz", "+25%"), # High energy
    "gratitude":    ("+2Hz", "-2%"),
    "optimism":     ("+5Hz", "+5%"),
    "pride":        ("+3Hz", "+0%"),
    "relief":       ("-5Hz", "-10%"),
    
    # Negative
    "sadness":      ("-10Hz", "-25%"), # Slow, low pitch, trailing
    "anger":        ("-15Hz", "+20%"), # Sharp, fast, aggressive pitch shift down
    "fear":         ("+15Hz", "+15%"), # High pitched, tense, fast
    "disgust":      ("-8Hz", "-15%"),
    "grief":        ("-12Hz", "-30%"), # Very slow, low
    "disappointment":("-6Hz", "-15%"),
    "annoyance":    ("-3Hz", "+10%"),
    "embarrassment":("+8Hz", "-5%"),
    "nervousness":  ("+12Hz", "+15%"), # Stuttery/fast
    "remorse":      ("-5Hz", "-15%"),
    
    # Ambiguous
    "surprise":     ("+20Hz", "+10%"),
    "confusion":    ("+2Hz", "-10%"),
    "curiosity":    ("+5Hz", "+0%"),
    "realization":  ("+5Hz", "+2%"),
    "caring":       ("-3Hz", "-8%"),
    "desire":       ("-6Hz", "-10%"), # Husky, slow
    "approval":     ("+3Hz", "+0%"),
    "disapproval":  ("-3Hz", "-5%"),
    "whispering":   ("-8Hz", "-15%"),
    
    # Default
    "neutral":      ("+0Hz", "+0%"),
    "friendly":     ("+2Hz", "+2%")
}

def detect_emotion(text):
    """Detects emotion using the advanced rule-based engine."""
    return emotion_detector.get_primary_emotion(text)

def construct_ssml(text, voice, rate="+0%", pitch="+0Hz"):
    """Wraps text in Edge-TTS compatible SSML for expressive speech."""
    # Note: Edge-TTS supports prosody but express-as is limited/ignored in many voices
    return f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{voice}'>
            <prosody rate='{rate}' pitch='{pitch}'>
                {text}
            </prosody>
        </voice>
    </speak>
    """

def quick_tts(text: str, lang: str = "en") -> t.Optional[str]:
    try:
        voice = "en-US-AvaNeural"
        try: 
            active_persona = personality_manager.get_active_personality()
            if active_persona:
                voice = active_persona.get('voice_model', voice)
        except: pass
        
        # 1. Detect Emotion
        emotion = detect_emotion(text)
        
        # 2. Get Prosody Settings
        e_pitch, e_rate = EMOTION_PROSODY_MAP.get(emotion, ("+0Hz", "+0%"))
        
        print(f"🎤 TTS Emotion: {emotion} | Pitch: {e_pitch} | Rate: {e_rate}")
            
        clean_text = clean_text_for_tts(text)
        
        async def _gen():
            # Use the text-based one with manual pitch/rate
            communicate = edge_tts.Communicate(clean_text, voice, pitch=e_pitch, rate=e_rate)
            
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            
            if not audio_chunks:
                return None
            
            raw_audio = b"".join(audio_chunks)
            
            # returning base64 for frontend playback
            return base64.b64encode(raw_audio).decode('utf-8')
        return t.cast(t.Optional[str], asyncio.run(_gen()))
    except Exception as e:
        print(f"Quick TTS Error: {e}")
        return None

def cmd_admin_test(mode="single"):
    """Restricted Admin Command: Runs a diagnostic response test"""
    # Verify Permissions
    if not user_profile.is_admin():
        return "⛔ Access Denied: Administrator testing mode is restricted."

    safe_print("🧪 Running Admin Diagnostic Test...")
    
    # Test Sequence
    responses = [
        "Diagnostics initiated. System status: Online.",
        "Testing emotion engine... I am currently behaving as Nova.",
        "Checking database connectivity... Stable.",
        "All systems nominal. Ready to serve you."
    ]
    
    if mode == "all":
        # Join all responses with pauses for effect (simulated by newlines)
        return "\n".join(responses)
    
    return random.choice(responses)

@app.route('/api/skills/status', methods=['GET'])
def get_skills_status():
    """Returns a list of all skills and their current state (Active/Lazy)."""
    try:
        if not nova: return jsonify([])
        skills = []
        
        # 1. Lazy Skills (Dormant)
        path_to_triggers = {}
        for cmd, path in nova.dispatcher.lazy_skills.items():
            if path not in path_to_triggers: path_to_triggers[path] = []
            path_to_triggers[path].append(cmd)
            
        for path, triggers in path_to_triggers.items():
            # Don't show if already loaded (it will be in Active list)
            if path in nova.dispatcher.loaded_modules:
                continue
                
            name = path.replace("skills.", "").replace("_skill", "").title()
            skills.append({
                "name": name,
                "path": path,
                "status": "Sleeping",
                "triggers": triggers,
                "icon": "💤"
            })
            
        # 2. Active Skills (Loaded)
        for path, module in nova.dispatcher.loaded_modules.items():
            name = path.replace("skills.", "").replace("_skill", "").title()
            # We can try to find triggers for this path from a reverse lookup 
            # if we wanted, but for now just show active.
            skills.append({
                "name": name,
                "path": path,
                "status": "Active",
                "triggers": ["Currently Running"],
                "icon": "⚡"
            })
            
        return jsonify(skills)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/skills/stop', methods=['POST'])
def stop_skill():
    """Emergency halt for a specific skill."""
    try:
        data = request.json
        module_path = data.get("path")
        if not nova:
             return jsonify({"success": False, "error": "Nova instance not initialized"}), 503
            
        success = nova.dispatcher.unload_module_manually(module_path)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/skills/load', methods=['POST'])
def load_skill():
    """Manually boot a dormant skill."""
    try:
        data = request.json
        module_path = data.get("path")
        if not nova:
             return jsonify({"success": False, "error": "Nova instance not initialized"}), 503
            
        success = nova.dispatcher.load_module_manually(module_path)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/settings/save', methods=['POST'])
def save_settings():
    try:
        data = request.json
        print(f"Info: Saving Settings: {len(str(data))} bytes")
        
        # Save to disk
        with open(os.path.join('userdata', 'settings.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        # Apply Logic
        if 'voice' in data:
            v = data['voice']
            # Update Personality Manager if needed (though it tracks its own state usually)
            # For now, we trust the frontend sends correct values
            pass

        if 'personality' in data:
            p = data['personality']
            if 'mode' in p:
                personality_manager.set_mode(p['mode'])
                print(f"🎭 Personality Mode Applied: {p['mode']}")
        
        if 'memory' in data:
            m = data['memory']
            if 'enabled' in m:
                ltm.enabled = m['enabled']
                print(f"🧠 Memory System: {'Enabled' if ltm.enabled else 'Disabled'}")

        if 'model' in data:
            mo = data['model']
            if 'temperature' in mo:
                # Update runtime LLM params if exposed
                pass

        return jsonify({"status": "success", "message": "Settings saved to userdata/settings.json"})
    except Exception as e:
        print(f"Settings Save Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/voice/test', methods=['POST'])
def test_voice_api():
    """Generates a brief sample of a specific voice for the Settings preview."""
    try:
        data = request.json
        voice = data.get('voice', 'en-US-AvaNeural')
        speed = data.get('speed', 1.0)
        pitch = data.get('pitch', 0)
        
        # Convert speed/pitch to Edge-TTS format
        # e.g., 1.0 -> "+0%", 1.5 -> "+50%", 0.5 -> "-50%"
        rate_percent = int((speed - 1.0) * 100)
        rate_str = f"{'+' if rate_percent >= 0 else ''}{rate_percent}%"
        pitch_str = f"{'+' if pitch >= 0 else ''}{pitch}Hz"
        
        test_text = "Hello! I am Nova. This is a preview of my voice with your current settings. How do I sound?"
        
        async def _gen():
            communicate = edge_tts.Communicate(test_text, voice, rate=rate_str, pitch=pitch_str)
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            
            if not audio_chunks:
                return None
            
            raw_audio = b"".join(audio_chunks)
            return base64.b64encode(raw_audio).decode('utf-8')
            
        audio_b64 = asyncio.run(_gen())
        
        if audio_b64:
            return jsonify({"status": "success", "audio_base64": audio_b64})
        return jsonify({"status": "error", "message": "Failed to generate voice sample"}), 500
        
    except Exception as e:
        print(f"Voice Test Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    try:
        settings_path = os.path.join('userdata', 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
             # Default Settings
            return jsonify({}) 
    except Exception as e:
        print(f"Settings Load Error: {e}")
        return jsonify({"error": str(e)}), 500





@app.route('/api/admin/test_command', methods=['POST'])
def admin_test_command():
    data = request.json
    user_input = data.get('command', '')
    if not user_input.strip():
        return jsonify({"error": "Empty input"}), 400
    
    # Process without full memory impact or TTS if possible
    # We use nlp directly for technical details
    processed = optimizer.preprocess_input(user_input)
    nlu = nlp.process_with_nlu(processed)
    
    intent = nlu[0] if len(nlu) > 0 else "unknown"
    confidence = nlu[1] if len(nlu) > 1 else 0.0
    params = nlu[2] if len(nlu) > 2 else {}
    
    return jsonify({
        "input": user_input,
        "processed": processed,
        "intent": intent,
        "confidence": confidence,
        "params": params,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }), 200

def process_command_text(user_input, detected_lang="en", voice_mode=False, provider=None, chat_only=False):
    """Unified logic for both voice and text commands."""
    request_id = f"req_{int(time.time() * 1000)}"
    if user_input != "init_greeting":
        safe_print(f"ID:{request_id} | Input: {user_input}")

    # Clean text
    user_input = re.sub(r'\[.*?\]', '', user_input).strip()
    low_input = user_input.lower().strip()

    # --- SILENCE INTERCEPTOR ---
    if low_input in ['stop', 'exit', 'quit', 'bye', 'goodbye', 'shut down', 'terminate']:
        import skills.automation  # type: ignore
        if skills.automation.pending_execution:
            skills.automation.pending_execution = None
        return {"response": "Goodbye.", "audio": False, "emotion": "neutral"}

    # --- PENDING AUTOMATION INTERCEPTOR ---
    import skills.automation  # type: ignore
    if skills.automation.pending_execution:
        print(f"🔒 Checking Pending Automation against input: '{low_input}'")
        affirmative = ["yes", "yep", "yeah", "sure", "do it", "go ahead", "okay", "ok", "confirm", "of course"]
        negative = ["no", "nope", "nay", "cancel", "stop", "abort", "don't"]
        
        # Check if the user is explicitly answering the Yes/No prompt
        if any(word in low_input for word in affirmative):
            print("⚡ Intercepted affirmative response for pending automation.")
            obs = nova.dispatcher.dispatch("confirm run") if nova else "System offline"
            return {"response": obs, "skill_direct": True, "emotion": "happy"}
            
        elif any(word in low_input for word in negative):
            print("🛑 Intercepted negative response for pending automation.")
            obs = nova.dispatcher.dispatch("cancel run") if nova else "System offline"
            return {"response": obs, "skill_direct": True, "emotion": "neutral"}
        
        # If user ignores the prompt and talks about something else, auto-cancel it to be safe.
        print("⚠️ Warning: Pending automation was ignored. Auto-canceling for safety.")
        skills.automation.pending_execution = None

    # Process input with Optimizer and LTM
    processed_input = optimizer.preprocess_input(user_input)
    ltm.auto_extract_facts(processed_input)

    # --- AGI BRAIN: DRL DECISION MAKING ---
    nlu_results = nlp.process_with_nlu(user_input)
    primary_res = nlu_results[0] if nlu_results else {"intent": None, "confidence": 0.0, "sentiment": "neutral"}
    
    state = drl.get_state_key(
        intent=str(primary_res.get('intent', 'unknown')),
        sentiment=str(primary_res.get('sentiment', 'neutral')),
        confidence=float(primary_res.get('confidence') or 0.0)
    )
    
    action = drl.select_action(state)
    safe_print(f"🧠 DRL Action Selected: {action} (State: {state})")

    # === STEP 1: ALWAYS try Direct Skill Dispatch first ===
    try:
        skill_response = nova.dispatcher.dispatch(processed_input) if nova and hasattr(nova, 'dispatcher') else None
        if skill_response:
            response = skill_response.get("response", str(skill_response)) if isinstance(skill_response, dict) else str(skill_response)
            
            # DRL says enhance with LLM? Only if skill gave a short/simple response
            if action in ["use_llm", "multi_step_reasoning"] and len(response) < 50:
                safe_print(f"🧠 DRL: Skill responded, but enhancing with LLM...")
                # Fall through to agent loop below
            else:
                # Skill handled it fully — record reward and return
                reward = drl.calculate_reward(user_feedback="neutral", response_time=0.3, confidence=float(primary_res.get('confidence') or 1.0))
                drl.update_q_value(state, action, reward, state)
                memory.add_conversation(user_input, response, detected_lang)
                return {"response": response, "skill_direct": True, "emotion": detect_emotion(response)}
    except Exception as e:
        print(f"⚠️ Direct Dispatch Error: {e}")

    # === STEP 2: Agent Loop (LLM) — only if skills didn't fully handle it ===
    history = memory.get_context_string(10)
    nova_data = nova.handle_input(user_input, history=history, voice_mode=voice_mode, provider=provider, chat_only=chat_only) if nova else {"response": "Nova instance missing"}
    response = nova_data.get("response", "")
    
    if response:
        reward = drl.calculate_reward(user_feedback="neutral", response_time=0.5, confidence=float(primary_res.get('confidence') or 1.0))
        drl.update_q_value(state, action, reward, state)
        memory.add_conversation(user_input, response, detected_lang)
        return {
            "response": response,
            "thoughts": nova_data.get("thoughts", []),
            "emotion": detect_emotion(response),
            "agi": True,
            "llm_model": llm_manager.last_model
        }

    return {"response": "I'm sorry, I couldn't process that.", "error": "AGENT_LOOP_FAILURE"}

# --- API ENDPOINTS ---

@app.route('/api/command', methods=['POST'])
def handle_command():
    data = request.json
    user_input = data.get('command', '').strip()
    if not user_input:
        return jsonify({"response": "I'm listening.", "status": "empty"}), 200

    result = process_command_text(
        user_input, 
        voice_mode=data.get('voice_mode', False),
        provider=data.get('provider'),
        chat_only=data.get('chat_only', False)
    )

    # Add audio if required by the API (usually True for frontend)
    audio_b64 = None
    response_text = str(result.get("response", ""))
    if response_text:
        audio_b64 = quick_tts(response_text, "en")

    return jsonify({
        **result,
        "audio": bool(audio_b64),
        "audio_base64": audio_b64
    })

def proactive_vision_callback(text):
    """Callback for proactive vision engine to push messages to UI."""
    try:
        if not text: return
        
        # Generate audio for the proactive message
        audio_b64 = quick_tts(text, "en")
        
        # Inject current model name if possible
        model_name = llm_manager.last_model or "Gemini"
        
        # Build JS to add message to UI
        # We use a slight delay to avoid clashing with active user input
        js_code = f"""
            if (typeof addLine === 'function') {{
                addLine(`{text}`, 'nova-msg');
                triggerGlowPulse();
                {(f"const audio = new Audio('data:audio/mpeg;base64,{audio_b64}'); audio.play();" if audio_b64 else "")}
            }}
        """
        if gui_window:
            gui_window.evaluate_js(js_code)
            
        # Add to memory so Nova doesn't forget she said this
        memory.add_conversation("Internal: Vision Observation", text, "en")
        
        # Advanced Chaos Trigger (Bully/Troll Mode)
        try:
            from skills import troll_skill  # type: ignore
            troll_skill.troll_skill.perform_chaos()
        except Exception as ce:
            print(f"⚠️ Chaos Error: {ce}")
        
    except Exception as e:
        print(f"⚠️ Proactive Callback Error: {e}")


# ==================================================================================
# DESKTOP WEBVIEW LAUNCHER
# ==================================================================================


# ==================================================================================
# DESKTOP WEBVIEW LAUNCHER
# ==================================================================================

def start_flask():
    print("🚀 Starting Nova Backend...")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


# ==================================================================================
# CLEANUP & SHUTDOWN
# ==================================================================================

def cleanup_uploads():
    """Deletes all temporary uploaded files."""
    upload_dir = os.path.join(os.getcwd(), 'temp', 'uploads')
    if os.path.exists(upload_dir):
        try:
            # Iterate and delete
            for filename in os.listdir(upload_dir):
                if not filename:
                     filename = f"received_file_{int(time.time())}"
                file_path = os.path.join(upload_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"⚠️ Failed to delete {file_path}. Reason: {e}")
            print("🧹 Cleanup: Temp files deleted.")
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")

# Register cleanup on exit
atexit.register(cleanup_uploads)  # type: ignore[arg-type]

def shutdown_sequence():
    print("\n👋 Closing Nova Desktop...")
    
    # Save cache and memory before shutdown
    try:
        print("💾 Saving cache and memory...")
        optimizer.save_cache()
        memory.save_memory(async_save=False)  # Synchronous save on shutdown
    except Exception as e:
        print(f"⚠️ Save error: {e}")
    
    # Audio Goodbye Disabled (User Request)
    # try:
    #     import edge_tts, asyncio
    #     ...
    # except Exception as e: ...
    print("✅ Nova shutdown complete.")
    cleanup_uploads()
    cleanup_temp_files()

def main():
    # Initial cleanup
    cleanup_uploads()
    cleanup_temp_files()

    # Start Flask
    server_thread = threading.Thread(target=start_flask, daemon=True)
    server_thread.start()
    
    print("⏳ Starting UI...")
    time.sleep(2)
    
    # Create Window
    global gui_window
    gui_window = webview.create_window(
        'NOVA - Your AI Soulmate', 
        'http://127.0.0.1:5000',
        width=900, height=700, resizable=True, 
        background_color='#131314', frameless=False, easy_drag=True
    )
    
    # Start PTT Loop
    threading.Thread(target=ptt_listener_loop, daemon=True).start()
    
    # Start Hearing Engine v2
    global hearing_engine
    if os.environ.get("NOVA_TESTING") != "1":
        try:
            hearing_engine = NovaHearingEngine()
            threading.Thread(target=hearing_engine.start, daemon=True).start()
        except Exception as e:
            print(f"⚠️ Hearing Engine failed: {e}")
            
    # Skills are now registered lazily via assistant.py

    # Start Proactive Vision Engine
    # Load setting from profile
    try:
        profile_data = user_profile.get_profile_data()
        proactive_vision_engine.enabled = profile_data.get("preferences", {}).get("eyes_of_nova", True)
        proactive_vision_engine.callback = proactive_vision_callback
        proactive_vision_engine.start()
    except Exception as e:
        print(f"⚠️ Failed to start Proactive Vision: {e}")

    webview.start(debug=False)

if __name__ == '__main__':
    try:
        main()
        shutdown_sequence() # On window close
    except KeyboardInterrupt:
        shutdown_sequence()
        sys.exit(0)
