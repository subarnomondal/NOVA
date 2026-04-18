import os
import subprocess
import psutil # type: ignore
import pyautogui # type: ignore
from datetime import datetime
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL, CoInitialize
from rich.console import Console

console = Console()

def get_volume_interface():
    try:
        CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        if not devices: return None
        
        # Method 1: Pycaw built-in activation (robust)
        try:
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None) # type: ignore
            return interface.QueryInterface(IAudioEndpointVolume)
        except:
            # Method 2: Fallback if Activate fails
            if hasattr(devices, "EndpointVolume"):
                return devices.EndpointVolume
            return None
    except Exception as e:
        return None

import re

def cmd_volume(args):
    """Usage: volume <0-100>"""
    try:
        # Extract the first number found in the string
        match = re.search(r'(\d+)', args)
        if not match:
            return "I can adjust the volume for you! Just let me know what percentage you'd like - anywhere from 0 to 100! 🔊"
        
        target = float(match.group(1))
        target = max(0.0, min(100.0, target))
        
        volume = get_volume_interface()
        if volume:
            volume.SetMasterVolumeLevelScalar(target / 100.0, None)
            import random
            responses = [
                f"Done! Volume is now at {target}%. 🔊",
                f"All set! I've adjusted the volume to {target}%. ✨",
                f"Perfect! Volume's at {target}% now. 🎵"
            ]
            return random.choice(responses)
        else:
            return "Hmm, I'm having trouble accessing the audio controls right now. Mind trying again? 🔄"
    except Exception as e:
        return "Oops, I had a little hiccup adjusting the volume. Let's try that again! 💙"


def cmd_open_app(args):
    """Usage: open <app name>"""
    try:
        app_name = args.lower().replace("open", "").replace("launch", "").replace("start", "").strip()
        
        # Common app mappings
        app_map = {
            "chrome": "chrome",
            "google chrome": "chrome",
            "browser": "chrome",
            "notepad": "notepad",
            "calculator": "calc",
            "calc": "calc",
            "file explorer": "explorer",
            "explorer": "explorer",
            "paint": "mspaint",
            "cmd": "cmd",
            "command prompt": "cmd",
            "powershell": "powershell",
            "task manager": "taskmgr",
            "settings": "ms-settings:",
            "control panel": "control",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
            "whatsapp": "whatsapp"
        }
        if app_name in app_map:
            print(f"🚀 Opening {app_name}...")
            os.system(f"start {app_map[app_name]}")
            import random
            responses = [
                f"Oki doki! Launching {app_name} for you! 🚀",
                f"You got it! Starting {app_name} now. Hehe~ ✨",
                f"On it! {app_name.title()} coming right up! (≧◡≦) 💫"
            ]
            return random.choice(responses)
        else:
            os.system(f"start {app_name}")
            return f"Trying to open {app_name} for you! 🔍"
            
    except Exception as e:
        print(f"Open App Error: {e}")
        return f"Hmm, I couldn't open that app. Here's what happened: {str(e)}"

def cmd_type_text(args):
    """Usage: type <text>"""
    try:
        text = args.replace("type", "").strip()
        if not text:
            return "What would you like me to type? Just let me know! ⌨️"
        
        print(f"⌨️ Typing: {text}")
        pyautogui.write(text, interval=0.1)
    
        return f"All done! I've typed: '{text}' for you. ✅"
    except Exception as e:
        return f"Oops, I couldn't type that. Error: {str(e)}"

def cmd_screenshot(args):
    """Usage: screenshot"""
    try:
        ss_dir = os.path.join("userdata", "screenshots")
        if not os.path.exists(ss_dir):
            os.makedirs(ss_dir)
        
        filename = os.path.join(ss_dir, f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        pyautogui.screenshot(filename)
        return f"Got it! Screenshot saved as {filename}. 📸"
    except Exception as e:
        return f"Oops, I couldn't take that screenshot. Here's what went wrong: {e}"

def cmd_usage(args):
    """Usage: usage"""
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        return f"Here's how your system is doing! 💻\n\nCPU: {cpu}%\nRAM: {ram}%"
    except Exception as e:
        return f"I had trouble checking system usage. Here's the error: {e}"

def cmd_battery(args):
    """Usage: battery"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = "charging" if battery.power_plugged else "on battery"
            emoji = "🔌" if battery.power_plugged else "🔋"
            return f"{emoji} You're at {percent}% and {plugged}!"
        else:
            return "Hmm, I can't seem to find battery info on this device. Are you on a desktop? 🖥️"
    except Exception as e:
        return f"I couldn't check the battery status. Here's why: {e}"

def cmd_media(args):
    """Usage: play, pause, next, previous, stop"""
    try:
        cmd = args.lower()
        if "play" in cmd or "pause" in cmd or "resume" in cmd:
            pyautogui.press("playpause")
            return "Toggled playback! ⏯️"
        elif "next" in cmd or "skip" in cmd:
            pyautogui.press("nexttrack")
            return "Skipped to the next track! ⏭️"
        elif "previous" in cmd or "back" in cmd:
            pyautogui.press("prevtrack")
            return "Went back to the previous track! ⏮️"
        elif "stop" in cmd:
            pyautogui.press("stop")
            return "Stopped playback. ⏹️"
        elif "mute" in cmd:  # Toggle mute
            pyautogui.press("volumemute")
            return "Toggled mute. 🔇"
        return "I can control media for you. Try saying 'play', 'next', or 'pause'! 🎵"
    except Exception as e:
        return f"Oops, media control failed: {e}"

def cmd_window(args):
    """Usage: minimize all, switch window"""
    try:
        cmd = args.lower()
        if "minimize" in cmd:
            if "all" in cmd:
                pyautogui.hotkey('win', 'd')
                return "Desktop revealed! 🖥️"
            else:
                pyautogui.hotkey('win', 'down') # Minimizes current window usually
                return "Minimized the window. 📉"
        elif "maximize" in cmd:
            pyautogui.hotkey('win', 'up')
            return "Maximized! 📈"
        elif "switch" in cmd:
            pyautogui.hotkey('alt', 'tab')
            return "Switched windows. 🔄"
        return "Unsure which window command to run. Try 'minimize all' or 'switch window'."
    except Exception as e:
        return f"Window control error: {e}"

def extract_delay_seconds(args):
    """
    Extract delay in seconds from natural language.
    Example: '5 min' -> 300, '30 sec' -> 30
    """
    if not args: return 0
    
    # Matches patterns like "5 min", "5 minutes", "10 sec", "10 seconds"
    match = re.search(r'(\d+)\s*(min|minute|sec|second)', args.lower())
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        if unit.startswith('min'):
            return value * 60
        return value
    
    # Fallback to just a number (assumed minutes if small, seconds if large?)
    # For safety, if no unit, we'll look for a standalone number and treat as seconds
    match = re.search(r'\b(\d+)\b', args)
    if match:
        return int(match.group(1))
        
    return 0

def cmd_power(args):
    """Usage: shutdown, restart, lock, sleep, abort [delay]"""
    try:
        cmd = args.lower()
        from core.agi_context import agi_context
        
        # Check for pending confirmation
        is_confirmed = any(word in cmd for word in ["yes", "confirm", "do it", "sure", "yep", "yeah"])
        pending = agi_context.chain_data.get("pending_power_command")
        pending_delay = agi_context.chain_data.get("pending_power_delay", 0)

        if "abort" in cmd or "cancel" in cmd:
            os.system("shutdown /a")
            # If there was a background sleep process, we can't easily kill it here 
            # without pid tracking, but shutdown /a handles Windows shutdown timer.
            agi_context.chain_data["pending_power_command"] = None
            agi_context.chain_data["pending_power_delay"] = 0
            return "Shutdown/Restart aborted! That was close. 🛑✨"

        if "lock" in cmd:
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return "Locking your PC now. Stay safe! 🔒"
        
        delay = extract_delay_seconds(cmd)
        if not is_confirmed:
            # Store delay for confirmation step
            agi_context.chain_data["pending_power_delay"] = delay
        else:
            # Use stored delay if confirmed
            delay = pending_delay or delay

        delay_str = f" in {delay} seconds" if delay > 0 else " now"

        if "sleep" in cmd or (pending == "sleep" and is_confirmed):
            if is_confirmed or "force" in cmd:
                # Sleep doesn't have a native delay in Windows cmd
                # We use a background process to wait and then sleep
                sleep_cmd = "powershell -command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState([System.Windows.Forms.PowerState]::Suspend, $false, $false)\""
                if delay > 0:
                    subprocess.Popen(f"timeout /t {delay} && {sleep_cmd}", shell=True)
                    agi_context.chain_data["pending_power_command"] = None
                    return f"Oki doki! I'll put the system to sleep in {delay} seconds. Goodnight! 🌙💤"
                else:
                    os.system(sleep_cmd)
                    return "Putting the system to sleep. Goodnight! 🌙"
            else:
                agi_context.chain_data["pending_power_command"] = "sleep"
                return f"Are you sure you want to put the PC to sleep{delay_str}? (Say 'yes' to confirm) 🌙"
            
        elif "shutdown" in cmd or (pending == "shutdown" and is_confirmed):
            if is_confirmed or "force" in cmd:
                # shutdown /s /t <seconds> handles the delay natively
                os.system(f"shutdown /s /t {delay if delay > 0 else 60}")
                agi_context.chain_data["pending_power_command"] = None
                return f"Initiating shutdown{delay_str}. Run 'abort' to cancel! 🛑"
            else:
                agi_context.chain_data["pending_power_command"] = "shutdown"
                return f"Are you absolutely sure you want to shut down{delay_str}? (Say 'yes' to confirm) ⚠️"
            
        elif "restart" in cmd or (pending == "restart" and is_confirmed):
            if is_confirmed or "force" in cmd:
                os.system(f"shutdown /r /t {delay if delay > 0 else 60}")
                agi_context.chain_data["pending_power_command"] = None
                return f"Restarting{delay_str}. Run 'abort' to cancel! 🔄"
            else:
                agi_context.chain_data["pending_power_command"] = "restart"
                return f"Are you sure you want to restart{delay_str}? (Say 'yes' to confirm) 🔄"
            
        return "I can handle power options commands like 'lock', 'sleep', 'shutdown', or 'restart'. Be careful! ⚡"
    except Exception as e:
        return f"Power command failed: {e}"

def cmd_voice_status(args):
    """Usage: voice status"""
    # This is a placeholder for actual voice authentication status
    # In a full implementation, this might check for a registered .wav profile
    return "Your voice profile is active and recognized! I'm listening closely to you. 🎤✨"

def cmd_browser(args):
    """Usage: new tab, close tab, reopen tab, next tab, previous tab"""
    try:
        cmd = args.lower()
        if "new" in cmd:
            pyautogui.hotkey('ctrl', 't')
            return "Opened a new tab. 📑"
        elif "close" in cmd:
            pyautogui.hotkey('ctrl', 'w')
            return "Closed current tab. ❌"
        elif "reopen" in cmd or "restore" in cmd:
            pyautogui.hotkey('ctrl', 'shift', 't')
            return "Reopened the last closed tab. 🔙"
        elif "next" in cmd:
            pyautogui.hotkey('ctrl', 'tab')
            return "Switched to next tab. ⏩"
        elif "previous" in cmd or "back" in cmd:
            pyautogui.hotkey('ctrl', 'shift', 'tab')
            return "Switched to previous tab. ⏪"
        return "I can manage tabs for you. Try 'new tab' or 'close tab'. 🌐"
    except Exception as e:
        return f"Browser control failed: {e}"

def cmd_nav(args):
    """Usage: scroll up/down, go back/forward"""
    try:
        cmd = args.lower()
        if "down" in cmd:
            pyautogui.press('pgdn')
            return "Scrolled down. ⬇️"
        elif "up" in cmd:
            pyautogui.press('pgup')
            return "Scrolled up. ⬆️"
        elif "back" in cmd:
            pyautogui.hotkey('alt', 'left')
            return "Went back. ⬅️"
        elif "forward" in cmd:
            pyautogui.hotkey('alt', 'right')
            return "Went forward. ➡️"
        return "I can scroll or navigate history. Try 'scroll down' or 'go back'. 🖱️"
    except Exception as e:
        return f"Navigation failed: {e}"

def cmd_edit(args):
    """Usage: copy, paste, cut, undo, select all"""
    try:
        cmd = args.lower()
        if "copy" in cmd:
            pyautogui.hotkey('ctrl', 'c')
            return "Copied to clipboard. 📋"
        elif "paste" in cmd:
            pyautogui.hotkey('ctrl', 'v')
            return "Pasted. 📥"
        elif "cut" in cmd:
            pyautogui.hotkey('ctrl', 'x')
            return "Cut selection. ✂️"
        elif "undo" in cmd:
            pyautogui.hotkey('ctrl', 'z')
            return "Undid last action. ↩️"
        elif "select all" in cmd:
            pyautogui.hotkey('ctrl', 'a')
            return "Selected everything. 🟦"
        elif "save" in cmd:
            pyautogui.hotkey('ctrl', 's')
            return "Saved. 💾"
        return "I can help edit text. Try 'copy' or 'select all'. 📝"
    except Exception as e:
        return f"Edit command failed: {e}"

def cmd_input(args):
    """Usage: press [key], click, right click"""
    try:
        cmd = args.lower()
        if "click" in cmd:
            if "right" in cmd:
                pyautogui.rightClick()
                return "Right clicked. 🖱️"
            elif "double" in cmd:
                pyautogui.doubleClick()
                return "Double clicked. 🖱️"
            else:
                pyautogui.click()
                return "Clicked. 🖱️"
        elif "press" in cmd or "hit" in cmd:
            # Extract key name
            key = cmd.replace("press", "").replace("hit", "").strip()
            if "enter" in key: pyautogui.press('enter')
            elif "esc" in key: pyautogui.press('esc')
            elif "space" in key: pyautogui.press('space')
            elif "backspace" in key: pyautogui.press('backspace')
            elif "delete" in key: pyautogui.press('delete')
            elif "tab" in key: pyautogui.press('tab')
            elif "alt f4" in key: pyautogui.hotkey('alt', 'f4')
            else:
                # Type generic key if safe
                if len(key) == 1 and key.isalnum():
                    pyautogui.press(key)
                else: 
                     return f"I pressed '{key}' for you."
            return f"Pressed {key}. ⌨️"
        return "I can simulate input. Try 'press enter' or 'click'. ⌨️"
    except Exception as e:
        return f"Input simulation failed: {e}"

def cmd_file_ops(args):
    """Usage: create folder, show desktop"""
    try:
        cmd = args.lower()
        if "folder" in cmd and "create" in cmd:
            # Create folder on desktop
            name = cmd.replace("create", "").replace("folder", "").replace("make", "").strip()
            if not name: name = "New Folder"
            
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            path = os.path.join(desktop, name)
            if not os.path.exists(path):
                os.makedirs(path)
                return f"Created folder '{name}' on your Desktop. 📁"
            else:
                return f"Folder '{name}' already exists! 📁"
        
        elif "desktop" in cmd and "show" in cmd:
            pyautogui.hotkey('win', 'd')
            return "Showing Desktop. 🖥️"
            
        elif "explorer" in cmd:
            pyautogui.hotkey('win', 'e')
            return "Opened File Explorer. 📂"
        return "I can help with files. Try 'create folder test' or 'show desktop'. 📁"
    except Exception as e:
        return f"File operation failed: {e}"

def register(dispatcher):
    dispatcher.register("volume", cmd_volume)
    dispatcher.register("sound", cmd_volume)
    dispatcher.register("audio", cmd_volume)
    dispatcher.register("screenshot", cmd_screenshot)
    dispatcher.register("usage", cmd_usage)
    dispatcher.register("system", cmd_usage)
    dispatcher.register("status", cmd_usage)
    dispatcher.register("status usage", cmd_usage)
    dispatcher.register("system status", cmd_usage)
    dispatcher.register("battery", cmd_battery)
    
    # Media Controls (toggle/transport only — "play <query>" is handled by media.py)
    dispatcher.register("pause", cmd_media)
    dispatcher.register("resume", cmd_media)
    dispatcher.register("toggle playback", cmd_media)
    dispatcher.register("next", cmd_media)
    dispatcher.register("previous", cmd_media)
    dispatcher.register("skip", cmd_media)
    dispatcher.register("next track", cmd_media)
    dispatcher.register("mute", cmd_media)
    
    # Window Management
    dispatcher.register("minimize", cmd_window)
    dispatcher.register("maximize", cmd_window)
    dispatcher.register("switch window", cmd_window)
    
    # Power Controls
    dispatcher.register("lock", cmd_power)
    # dispatcher.register("sleep", cmd_power) - REMOVED as requested
    dispatcher.register("shutdown", cmd_power)
    dispatcher.register("restart", cmd_power)
    dispatcher.register("abort", cmd_power)
    dispatcher.register("cancel", cmd_power)
    
    # Advanced Automation (Browser, Nav, Edit)
    dispatcher.register("new tab", cmd_browser)
    dispatcher.register("close tab", cmd_browser)
    dispatcher.register("reopen tab", cmd_browser)
    dispatcher.register("next tab", cmd_browser)
    dispatcher.register("previous tab", cmd_browser)
    
    dispatcher.register("scroll down", cmd_nav)
    dispatcher.register("scroll up", cmd_nav)
    dispatcher.register("go back", cmd_nav)
    dispatcher.register("go forward", cmd_nav)
    
    dispatcher.register("copy", cmd_edit)
    dispatcher.register("paste", cmd_edit)
    dispatcher.register("cut", cmd_edit)
    dispatcher.register("undo", cmd_edit)
    dispatcher.register("select all", cmd_edit)
    dispatcher.register("save", cmd_edit)
    
    # Ultimate Automation (Files, Input)
    dispatcher.register("create folder", cmd_file_ops)
    dispatcher.register("show desktop", cmd_file_ops)
    dispatcher.register("open explorer", cmd_file_ops)
    dispatcher.register("explorer", cmd_file_ops)
    
    # Consolidated Automation
    dispatcher.register("open", cmd_open_app)
    dispatcher.register("launch", cmd_open_app)
    dispatcher.register("start", cmd_open_app)
    dispatcher.register("type", cmd_type_text)
    
    # Standalone Shorthand Triggers
    dispatcher.register("switch", cmd_window)
    dispatcher.register("scroll", cmd_nav)
    dispatcher.register("minimize", cmd_window)
    dispatcher.register("maximize", cmd_window)
    
    dispatcher.register("click", cmd_input)
    dispatcher.register("right click", cmd_input)
    dispatcher.register("double click", cmd_input)
    dispatcher.register("press", cmd_input)
    dispatcher.register("hit", cmd_input)
    
    # New handlers for verification
    dispatcher.register("voice_status", cmd_voice_status)
    dispatcher.register("debug_parameters", lambda args: f"Current Model: OpenRouter Cloud\\nPersona: Nova\\nMood: Stable\\nUptime: Active")

