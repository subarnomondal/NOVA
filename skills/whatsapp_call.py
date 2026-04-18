"""
WhatsApp Auto-Call Monitor for NOVA
=====================================
Runs as a background thread from startup.
Automatically detects incoming WhatsApp voice call popups and:
  - Accepts them (voice only, ignores video calls).
  - Runs a dedicated Python audio loop to talk with the caller.
    The caller's voice is captured via Stereo Mix (system audio loopback)
    and Nova's responses are spoken via edge-tts (Neural Voice).
"""

import threading
import time
import io
import wave
import tempfile
import os
import requests # type: ignore
import numpy as np
import sounddevice as sd
import pyautogui # type: ignore
import pygetwindow as gw

# ─── Audio Config ─────────────────────────────────────────────────────────────
_SAMPLE_RATE    = 16000
_CHANNELS       = 1
_RECORD_SECONDS = 3.5        # Slightly shorter chunk for faster response
_SILENCE_THRESH = 0.002      # Lower threshold to be more sensitive

def _get_user_name():
    """Dynamically load user's name from profile instead of hardcoding."""
    try:
        import json
        profile_path = os.path.join("userdata", "user_profile.json")
        if os.path.exists(profile_path):
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            name = profile.get('name') or profile.get('personal_info', {}).get('name')
            if name:
                return name
    except Exception:
        pass
    return "my user"

# Stereo Mix = captures speaker output (caller's voice)
def _find_stereo_mix_device():
    """Find the best available audio loopback device (Stereo Mix, What U Hear, etc.)."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        # Priority order for loopback/monitor devices
        keywords = ["Stereo Mix", "What U Hear", "Speakers", "Output", "Loopback"]
        
        found_devices = []
        for i, d in enumerate(devices):
            name = d['name']
            inputs = d['max_input_channels']
            if inputs > 0:
                for kw in keywords:
                    if kw.lower() in name.lower():
                        # Score based on keyword index (lower is better)
                        found_devices.append((keywords.index(kw), i, name))
                        break
        
        if found_devices:
            found_devices.sort()
            best_idx = found_devices[0][1]
            best_name = found_devices[0][2]
            print(f"🎙️ [AudioConfig] Auto-selected recording device: {best_name} (Index {best_idx})")
            return best_idx
            
        print("⚠️ [AudioConfig] No Stereo Mix or loopback device found. Listing all input devices for debug:")
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                print(f"   - Device {i}: {d['name']}")
        return None
    except Exception as e:
        print(f"⚠️ [AudioConfig] Device discovery error: {e}")
        return None

_STEREO_MIX_DEVICE = _find_stereo_mix_device()

# ─── Global Monitor State ─────────────────────────────────────────────────────
_monitor_thread = None
_monitor_running = False
_call_active    = False      # True while a call is in progress
_call_thread    = None

# Keywords that identify incoming call popups
_CALL_KEYWORDS  = ["incoming", "voice call", "calling"]
_VIDEO_KEYWORDS = ["video"]



def _find_call_window():
    """
    Scans ALL open windows to find a WhatsApp call notification popup.
    Strategy:
      1. Check all windows for 'WhatsApp' in title.
      2. If no small popup found, check ALL windows for call keywords.
    Returns the window object if found, else None.
    """
    try:
        all_wins = gw.getAllWindows()
        candidates = []

        for win in all_wins:
            if not win.title or win.width <= 0 or win.height <= 0:
                continue
            title_lower = win.title.lower()
            is_whatsapp = "whatsapp" in title_lower
            has_call_keyword = any(k in title_lower for k in _CALL_KEYWORDS)
            
            # STRICT CHECK: Must be a small window (notification popup)
            # Main WhatsApp window is usually > 800px wide
            is_popup_size = win.width < 500 and win.height < 400

            if is_whatsapp and has_call_keyword and is_popup_size:
                # High priority: small WhatsApp popup with call keywords
                candidates.append((0, win))
            elif has_call_keyword and is_popup_size:
                # Medium priority: small notification with call keywords (might not have 'whatsapp' in title)
                candidates.append((1, win))

        if candidates:
            # Sort by priority (lower = better)
            candidates.sort(key=lambda x: x[0])
            chosen = candidates[0][1]
            print(f"📞 [CallMonitor] MATCH! Found call window: '{chosen.title}' ({chosen.width}x{chosen.height})")
            return chosen

    except Exception as e:
        print(f"⚠️ [CallMonitor] Window scan error: {e}")
    return None


def _is_video_call(window_title):
    """
    Heuristic: Check if it looks like a video call.
    WhatsApp video call popups often have 'Video' in the title.
    """
    title_lower = window_title.lower()
    return any(k in title_lower for k in _VIDEO_KEYWORDS)



def _accept_call(win):
    """
    Click the green Accept (voice) button on the popup.
    Strategy:
      1. Take a screenshot of the call popup region.
      2. Scan pixels for WhatsApp green (#00a884 / #25D366 range) — that's the Accept button.
      3. Click the center of the green region found.
      4. Fallback: try multiple fixed positions across the bottom-right area.
    """
    try:
        try:
            if win.isMinimized:
                win.restore()
            win.activate()
        except: pass
        time.sleep(0.8)

        # Take a screenshot of just the call popup window region
        popup_img = pyautogui.screenshot(region=(
            win.left, win.top, win.width, win.height
        ))

        # Scan for green pixels (WhatsApp green range)
        # We increase tolerance for different screen calibrations/themes
        green_pixels = []
        step = 2  # Faster and more precise
        for px in range(0, win.width, step):
            for py in range(0, win.height, step):
                try:
                    r, g, b = popup_img.getpixel((px, py))[:3]
                    # Robust green detection: Green must be the dominant color and above a threshold
                    if g > 130 and g > r * 1.15 and g > b * 1.15: 
                        green_pixels.append((px, py))
                except Exception:
                    pass

        if green_pixels:
            # Click the center of the largest cluster of green (usually the button)
            avg_x = sum(p[0] for p in green_pixels) // len(green_pixels)
            avg_y = sum(p[1] for p in green_pixels) // len(green_pixels)
            abs_x = win.left + avg_x
            abs_y = win.top + avg_y
            print(f"🟢 Green 'Accept' button confirmed at ({abs_x}, {abs_y})")
            pyautogui.click(abs_x, abs_y)
            return True

        # Fallback: try several positions across the lower-right area
        # WhatsApp call buttons are in the bottom half, roughly 60-80% from top
        print("⚠️ Green pixel not found — trying fallback click positions...")
        fallback_positions = [
            (0.75, 0.65),  # far right center
            (0.70, 0.70),
            (0.80, 0.60),
            (0.65, 0.75),
            (0.60, 0.65),
        ]
        for (fx, fy) in fallback_positions:
            cx = win.left + int(win.width * fx)
            cy = win.top + int(win.height * fy)
            print(f"   🖱️ Trying fallback click at ({cx}, {cy})")
            pyautogui.click(cx, cy)
            time.sleep(0.3)

        return True  # Attempted at least

    except Exception as e:
        print(f"⚠️ Failed to accept call: {e}")
        return False



def _speak_tts(text):
    """
    Speak text using Nova's real voice (edge_tts AnaNeural).
    Audio plays through PC speakers → WhatsApp mic picks it up.
    """
    import asyncio
    import tempfile
    import subprocess
    try:
        import edge_tts

        # Load voice from settings if available, else use default (Ava is premium quality)
        voice = "en-US-AvaNeural"
        try:
            import json
            settings_path = os.path.join("userdata", "settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, encoding="utf-8") as f:
                    s = json.load(f)
                voice_setting = s.get("voice", voice)
                if isinstance(voice_setting, dict):
                    voice = voice_setting.get("model", voice)
                else:
                    voice = voice_setting
        except Exception:
            pass

        # Generate TTS audio via edge_tts
        fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd) # Close handle, edge_tts will open it
        
        async def generate_audio():
            communicate = edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz")
            await communicate.save(tmp_path)

        asyncio.run(generate_audio())

        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            print("⚠️ edge_tts failed to generate audio file.")
            return

        # Play via pygame (more reliable and already in project)
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.set_volume(1.0)  # Max volume
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            print(f"🔊 Playing Nova's voice: '{text[:50]}...'")
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            pygame.mixer.music.unload()
        except Exception as py_err:
            print(f"⚠️ Pygame Playback Error: {py_err}")
            # Fallback to powershell with escaped path
            p_path = tmp_path.replace("'", "''")
            subprocess.run(
                ["powershell", "-c",
                 f'Add-Type -AssemblyName PresentationCore; '
                 f'$m=[System.Windows.Media.MediaPlayer]::new(); '
                 f'$m.Open([Uri]::new("{p_path}")); '
                 f'$m.Volume = 1.0; $m.Play(); Start-Sleep -Seconds 10'],
                timeout=30, capture_output=True
            )

        try:
            os.remove(tmp_path)
        except Exception:
            pass

    except Exception as e:
        print(f"⚠️ TTS Exception: {e}")


def _record_chunk():
    """
    Record a chunk of audio from the loopback device (caller's voice).
    Includes sanitization, normalization, and device fallback.
    """
    try:
        dev = _STEREO_MIX_DEVICE
        audio = sd.rec(
            int(_RECORD_SECONDS * _SAMPLE_RATE),
            samplerate=_SAMPLE_RATE,
            channels=_CHANNELS,
            dtype='float32',
            device=dev
        )
        sd.wait()
        flat = audio.flatten()
        
        # 1. Sanitize: Replace NaNs and Infs with zeros
        if np.isnan(flat).any() or np.isinf(flat).any():
            print(f"⚠️ [CallLoop] Invalid values detected in buffer from Device {dev}. Sanitizing...")
            flat = np.nan_to_num(flat, nan=0.0, posinf=0.0, neginf=0.0)
            
            # If the entire buffer was invalid, try fallback immediately
            if np.all(flat == 0):
                print("🔄 [CallLoop] Buffer is empty after sanitization. Falling back to default input.")
                audio = sd.rec(int(_RECORD_SECONDS * _SAMPLE_RATE), samplerate=_SAMPLE_RATE, channels=_CHANNELS, dtype='float32', device=None)
                sd.wait()
                flat = np.nan_to_num(audio.flatten())

        # 2. Normalize: Boost quiet signals if needed
        max_val = np.max(np.abs(flat))
        if max_val > 0.0001 and max_val < 0.1:
            # Boost to a reasonable peak level (~0.5)
            boost_factor = 0.5 / max_val
            # print(f"   (Boosting audio x{boost_factor:.1f})") # Debug boost
            flat = flat * boost_factor
            
        return flat
    except Exception as e:
        print(f"⚠️ Recording Error: {e}")
        try:
            audio = sd.rec(int(_RECORD_SECONDS * _SAMPLE_RATE), samplerate=_SAMPLE_RATE, channels=_CHANNELS, dtype='float32')
            sd.wait()
            return np.nan_to_num(audio.flatten())
        except:
            return None


def _audio_to_wav_bytes(audio_data):
    """Convert numpy float32 audio to WAV bytes for Whisper."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(_CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(_SAMPLE_RATE)
        pcm = (audio_data * 32767).astype(np.int16)
        wf.writeframes(pcm.tobytes())
    buf.seek(0)
    return buf.read()


def _transcribe_audio(audio_data):
    """Send audio to Nova's STT backend and return the transcript."""
    try:
        wav_bytes = _audio_to_wav_bytes(audio_data)
        files = {'audio': ('chunk.wav', wav_bytes, 'audio/wav')}
        data = {'language': 'auto'}
        resp = requests.post(
            "http://127.0.0.1:5000/api/transcribe",
            files=files, data=data, timeout=8
        )
        result = resp.json()
        return result.get('transcript', '').strip()
    except Exception as e:
        print(f"⚠️ STT Error: {e}")
        return ''


def _get_nova_response(text):
    """Send caller's text to Nova's LLM and return the reply."""
    try:
        user_name = _get_user_name()
        prompt = (
            f"You are Nova, {user_name}'s AI assistant answering a WhatsApp call. "
            f"The caller just said: '{text}'. "
            f"Reply helpfully in English in 1-3 short sentences. "
            f"Always refer to your user as {user_name}."
        )
        resp = requests.post(
            "http://127.0.0.1:5000/api/command",
            json={"command": prompt, "language": "en", "provider": "free", "chat_only": True},
            timeout=12
        )
        data = resp.json()
        return data.get('response', "Sorry, I didn't quite catch that.")
    except Exception as e:
        print(f"⚠️ LLM Error: {e}")
        return "Sorry, I'm having a little trouble right now."


def _call_audio_loop():
    """
    Dedicated call conversation loop:
    - Records caller's voice from Stereo Mix (system loopback)
    - Transcribes via Whisper STT
    - Gets Nova's reply from LLM
    - Speaks reply via edge-tts (Neural Voice)
    """
    global _call_active
    print("🎙️ [CallLoop] Call audio loop started!")

    # Give Nova's intro greeting first
    user_name = _get_user_name()
    intro = (
        f"Hi! I'm Nova, {user_name}'s personal AI assistant. "
        f"I'm answering on their behalf. How can I help you today?"
    )
    _speak_tts(intro)

    while _call_active:
        try:
            print("👂 [CallLoop] Listening for caller...")
            audio = _record_chunk()

            if audio is None:
                time.sleep(1)
                continue

            # Skip silent chunks
            rms = float(np.sqrt(np.mean(audio ** 2)))
            if rms < _SILENCE_THRESH:
                # print(f"   (silence: {rms:.5f})") # Debug silence
                continue

            print(f"🔊 [CallLoop] Audio detected (RMS={rms:.4f}), transcribing...")
            text = _transcribe_audio(audio)

            if not text:
                print("   (empty transcript, skipping)")
                continue

            print(f"📝 [CallLoop] Caller said: '{text}'")
            reply = _get_nova_response(text)
            print(f"💬 [CallLoop] Nova replies: '{reply[:80]}'")

            _speak_tts(reply)

        except Exception as e:
            print(f"⚠️ [CallLoop] Error: {e}")
            time.sleep(1)

    print("🛑 [CallLoop] Call audio loop ended.")


def _start_call_audio_loop():
    """Start the call conversation loop in a background thread."""
    global _call_active, _call_thread
    _call_active = True
    _call_thread = threading.Thread(target=_call_audio_loop, daemon=True)
    _call_thread.start()


def _stop_call_audio_loop():
    """Stop the call conversation loop."""
    global _call_active
    _call_active = False


def _trigger_live_mode():

    """
    Notify NOVA's backend to enter Live Mode so it listens
    to the user's voice and talks back.
    """
    try:
        requests.post(
            "http://127.0.0.1:5000/api/settings/live",
            json={"active": True},
            timeout=2
        )
        print("🎙️ Auto-triggered Nova Live Mode for WhatsApp call!")
    except Exception as e:
        print(f"⚠️ Could not trigger Live Mode: {e}")


def _send_call_summary():
    """
    Sends a 'daily summary' command to Nova's backend right after
    a call is accepted. Nova will speak a brief briefing to the user.
    """
    try:
        user_name = _get_user_name()
        summary_prompt = (
            f"You are Nova, {user_name}'s personal AI assistant. "
            f"You just picked up an incoming WhatsApp voice call on {user_name}'s behalf. "
            f"Greet the caller warmly, introduce yourself as Nova — {user_name}'s AI assistant — "
            f"and let them know you're answering on {user_name}'s behalf. "
            f"Ask the caller how you can help them or if they'd like to leave a message for {user_name}. "
            f"Be friendly, professional, and keep it to 3-4 sentences. "
            f"IMPORTANT: Always reply in English only, even if the caller speaks in another language."
        )
        resp = requests.post(
            "http://127.0.0.1:5000/api/command",
            json={"command": summary_prompt, "language": "en", "provider": "free"},
            timeout=10
        )
        data = resp.json()
        if data.get("response"):
            print(f"📋 Call Summary Sent: {data['response'][:80]}...")
        else:
            print("⚠️ Call summary: no response from backend.")
    except Exception as e:
        print(f"⚠️ Could not send call summary: {e}")


def _monitor_loop():
    """
    Background loop that polls for incoming WhatsApp call popups.
    Runs every POLL_INTERVAL seconds.
    """
    global _monitor_running
    print("👀 WhatsApp Call Monitor: Started (watching for calls every 1s...)")
    heartbeat = 0

    while _monitor_running:
        try:
            call_win = _find_call_window()
            if call_win:
                title = call_win.title
                print(f"🔔 Incoming call detected! Window: '{title}' ({call_win.width}x{call_win.height})")

                if _is_video_call(title):
                    print("📹 Video call detected — ignoring (voice only mode).")
                else:
                    print("☎️ Voice call! Accepting...")
                    accepted = _accept_call(call_win)
                    if accepted:
                        print("✅ Call accepted! Starting call audio loop in 2s...")
                        time.sleep(2.0)
                        _start_call_audio_loop()   # handles caller voice + Nova TTS

                # After handling a call, wait before polling again
                time.sleep(6)
            else:
                # Periodic heartbeat to confirm monitor is alive
                heartbeat += 1
                if heartbeat % 30 == 0:
                    print("👂 [CallMonitor] Listening... (no call yet)")

        except Exception as e:
            print(f"⚠️ Call Monitor Error: {e}")

        time.sleep(1.0)  # Poll every 1 second for fast detection

    print("� WhatsApp Call Monitor: Stopped.")


def start_call_monitor():
    """Start the background call monitoring thread."""
    global _monitor_thread, _monitor_running
    if _monitor_running:
        return  # Already running

    _monitor_running = True
    _monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
    _monitor_thread.start()


def stop_call_monitor():
    """Stop the background call monitoring thread."""
    global _monitor_running
    _monitor_running = False


# ─── Manual Commands (still usable via voice) ───────────────────────────────

def cmd_accept_whatsapp_call(args=""):
    """Manually accept an incoming WhatsApp voice call."""
    win = _find_call_window()
    if not win:
        return "I don't see an incoming call notification right now. Is it ringing? 🔔"

    if _is_video_call(win.title):
        return "That looks like a video call — I only accept voice calls per your instructions! 📹"

    accepted = _accept_call(win)
    if accepted:
        time.sleep(2.0)
        _trigger_live_mode()
        time.sleep(1.0)
        _send_call_summary()
        return "WHATSAPP_CALL_ACCEPTED: Picked up! Giving you a quick summary then entering voice mode. 🎙️"
    return "I tried to accept but something went wrong. 😅"


def cmd_reject_whatsapp_call(args=""):
    """Manually reject an incoming WhatsApp call."""
    win = _find_call_window()
    if not win:
        return "I don't see any call to reject. 🛑"

    try:
        win.activate()
        time.sleep(0.4)
        # Decline button is on the left side (~25% from left)
        click_x = win.left + int(win.width * 0.25)
        click_y = win.top + int(win.height * 0.60)
        pyautogui.click(click_x, click_y)
        return "Declined the call. 🔕"
    except Exception as e:
        return f"ERROR [REJECT_FAILURE]: {e}"


def cmd_stop_call_monitor(args=""):
    """Stop the auto call monitor."""
    stop_call_monitor()
    return "Auto call monitor stopped. I'll no longer auto-pick calls. 🛑"


def cmd_start_call_monitor(args=""):
    """Start/restart the auto call monitor."""
    start_call_monitor()
    return "Auto call monitor started! I'll pick up WhatsApp voice calls automatically. 📞"


def register(dispatcher):
    # The monitor starts automatically when this skill is loaded (via desktop.py)
    # WARNING (Permanent Fix): Auto-starting this monitor locks the Windows audio
    # drivers, preventing the main `NovaHearingEngine` from accessing the microphone.
    # Users must manually trigger this skill to avoid deafening Nova.
    # start_call_monitor()

    dispatcher.register("accept whatsapp call", cmd_accept_whatsapp_call)
    dispatcher.register("pick up call", cmd_accept_whatsapp_call)
    dispatcher.register("pick up whatsapp call", cmd_accept_whatsapp_call)
    dispatcher.register("answer call", cmd_accept_whatsapp_call)
    dispatcher.register("answer whatsapp", cmd_accept_whatsapp_call)

    dispatcher.register("reject whatsapp call", cmd_reject_whatsapp_call)
    dispatcher.register("decline call", cmd_reject_whatsapp_call)
    dispatcher.register("reject call", cmd_reject_whatsapp_call)

    dispatcher.register("stop call monitor", cmd_stop_call_monitor)
    dispatcher.register("start call monitor", cmd_start_call_monitor)
