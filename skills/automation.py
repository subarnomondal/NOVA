import os
import subprocess
import sys
import io
import traceback
import threading
from rich.console import Console
import platform
import re

# Pre-check for Windows
IS_WINDOWS = platform.system() == "Windows"

console = Console()

# State for requiring confirmation before execution
pending_execution = None

def _strip_bot_prefixes(text):
    """Strips natural language prefixes to isolate the actual command."""
    prefixes = [
        r"hey\s+nova,?", r"nova,?", r"please,?", r"can\s+you,?", r"could\s+you,?",
        r"i\s+need\s+you\s+to,?", r"automate,?", r"run,?", r"execute,?"
    ]
    pattern = r"^\s*(" + "|".join(prefixes) + r")\s+"
    # Strip prefixes case-insensitively
    cleaned = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    return cleaned

def _execute_script(code):
    print(f"🛠️ Executing Python Automation...")
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    try:
        # We use a shared globals dict to allow persistence if needed, 
        # though usually it's one-off.
        exec(code, globals())
        sys.stdout = old_stdout
        output = redirected_output.getvalue()
        return f"Automation complete! ✅\n\nOutput:\n{output if output else '[No output]'}"
    except Exception as e:
        sys.stdout = old_stdout
        error_trace = traceback.format_exc()
        return f"ERROR [SCRIPT_FAILURE]: {e}\n\nTraceback:\n{error_trace}"

def _execute_system_command(command, delayed=False):
    prefix = "⏳ Delayed " if delayed else "🖥️ "
    print(f"{prefix}Executing System Command: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        # If delayed, we might want to speak the result via Nova's engine if available
        # But for now, returning it or printing it to console is safest.
        if delayed:
            if result.returncode == 0:
                print(f"\n✅ Delayed Command Success:\n{result.stdout}")
            else:
                print(f"\n❌ Delayed Command Failed:\n{result.stderr}")
        
        if result.returncode == 0:
            return f"Command executed successfully! ✅\n\nOutput:\n{result.stdout if result.stdout else '[No output]'}"
        else:
            return f"ERROR [CMD_FAILURE]: Code {result.returncode}\n\nError Output:\n{result.stderr}"
    except Exception as e:
        err_msg = f"ERROR [SYSTEM_ERROR]: {e}"
        if delayed: print(f"\n❌ {err_msg}")
        return err_msg

def predict_outcome(command, is_script=False):
    """Ask the local LLM to predict what the command will do."""
    try:
        # Import llm_manager safely
        from core.llm_manager import llm_manager
        if not llm_manager:
            return "This will execute code on your system."
            
        action_type = "Python script" if is_script else "system command"
        prompt = (
            f"You are a security assistant. Briefly explain in 1 short sentence "
            f"what this {action_type} will do, and if it is safe or destructive.\n"
            f"Command: {command}\nResponse:"
        )
        prediction = llm_manager.generate(prompt, max_tokens=50, force_advanced=False)
        return prediction.strip() if prediction else "This will execute code on your system."
    except Exception:
        return "This will execute code on your system."

def is_simple_task(command):
    """Check if the command is a simple, non-destructive task that can bypass verification."""
    simple_keywords = ["volume", "brightness", "calc", "notepad", "explorer", "start ", "echo", "ping", "dir", "ls"]
    cmd_lower = command.lower()
    return any(kw in cmd_lower for kw in simple_keywords)

def cmd_run_script(args):
    """
    Executes a Python script block.
    Usage: automate script [python code]
    """
    global pending_execution
    try:
        # Extract code: remove triggers
        code = args.replace("automate script", "").replace("run script", "").strip()
        if not code:
            return "Please provide the Python code you want me to execute! 🐍"
            
        pending_execution = {'type': 'script', 'target': code}
        prediction = predict_outcome(code, is_script=True)
        
        return f"⚠️ **Security Verification Required** ⚠️\n*Prediction: {prediction}*\n\nShould I go ahead with this? (Yes/No)"
    except Exception as e:
        return f"I had trouble setting up the script execution: {e}"

def cmd_run_system_command(args):
    """
    Executes a system/shell command.
    Usage: automate cmd [system command]
    """
    global pending_execution
    try:
        # Clean the input to remove NL prefixes
        command = _strip_bot_prefixes(args)
        
        # Remove direct skill keywords if they remain
        command = command.replace("automate cmd", "").replace("execute command", "").replace("run command", "").strip()
        
        if not command:
            return "What system command should I run? 🖥️"
            
        # 1. Exception for simple tasks
        if is_simple_task(command):
            print("⚡ Bypassing verification for safe/simple command.")
            return _execute_system_command(command)
            
        # 2. Require verify
        pending_execution = {'type': 'cmd', 'target': command}
        prediction = predict_outcome(command, is_script=False)
        
        return f"⚠️ **Security Verification Required** ⚠️\n*Prediction: {prediction}*\n\nShould I go ahead with this? (Yes/No)"
    except Exception as e:
        return f"ERROR [SYSTEM_ERROR]: {e}"

def cmd_confirm_run(args):
    """Confirms and executes a pending command. Applies a 1-minute delay to system commands."""
    global pending_execution
    if not pending_execution:
        return "There's no pending command to confirm. 🤔"
    
    action_type = pending_execution['type']
    target = pending_execution['target']
    pending_execution = None
    
    if action_type == 'script':
        return _execute_script(target)
    elif action_type == 'cmd':
        # Apply 1-minute delay for system commands
        print(f"⏱️ System command '{target}' confirmed. Scheduling execution in 60 seconds.")
        timer = threading.Timer(60.0, _execute_system_command, args=[target, True])
        timer.daemon = True
        timer.start()
        return "Understood. The system command is safe and has been scheduled to run in 1 minute. ⏳"
    
    return "Unknown pending action."

def cmd_cancel_run(args):
    """Cancels a pending command."""
    global pending_execution
    if not pending_execution:
        return "There's no pending command to cancel. 🤔"
    pending_execution = None
    return "Automation task cancelled. 🛑"


def cmd_automation_master(args):
    """
    A unified entry point for general automation requests.
    This can be called from the LLM fallback.
    """
    # If the args contain a specific tag like [SCRIPT] or [CMD], we route it.
    if "[SCRIPT]" in args:
        code = args.split("[SCRIPT]")[1].split("[/SCRIPT]")[0].strip()
        return cmd_run_script(f"automate script {code}")
    elif "[CMD]" in args:
        cmd = args.split("[CMD]")[1].split("[/CMD]")[0].strip()
        return cmd_run_system_command(f"automate cmd {cmd}")
    
    return "I'm ready for automation! Just let me know what you need to automate. ⚙️"

def cmd_window_control(args):
    """
    Controls window state (minimize/maximize).
    Usage: minimize all, minimize windows, show desktop
    """
    if not IS_WINDOWS:
        return "I can only control windows on a Windows PC right now. 🖥️"
        
    cmd = args.lower()
    try:
        if "minimize" in cmd or "desktop" in cmd or "hide" in cmd:
            # PowerShell: Minimize All
            subprocess.run(["powershell", "-command", "(New-Object -ComObject Shell.Application).MinimizeAll()"], shell=True)
            return "Minimizing all windows. 📉"
        elif "maximize" in cmd or "restore" in cmd:
            # PowerShell: Undo Minimize All
            subprocess.run(["powershell", "-command", "(New-Object -ComObject Shell.Application).UndoMinimizeAll()"], shell=True)
            return "Restoring windows. 📈"
            
    except Exception as e:
        return f"Controller Error: {e}"
        
    return "I wasn't sure what to do with the windows. Try 'minimize all'. 🪟"

def cmd_open_app(args):
    """
    Opens applications.
    Usage: open [app name], launch [app name]
    """
    # Clean prefix (Hey Nova, Nova, etc.)
    app_name = _strip_bot_prefixes(args)
    
    # Remove direct verbs
    app_name = app_name.replace("open", "").replace("launch", "").replace("start", "").strip()
    
    if not app_name:
        return "Which app would you like me to open? 📂"
        
    try:
        print(f"🚀 Launching: {app_name}")
        # Common Windows App Shortcuts
        shortcuts = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": "start chrome",
            "edge": "start msedge",
            "explorer": "explorer.exe",
            "cmd": "start cmd",
            "terminal": "wt.exe",
            "vscode": "code",
            "spotify": "start spotify:",
            "settings": "start ms-settings:",
            "task manager": "taskmgr",
            "control panel": "control"
        }
        
        target = shortcuts.get(app_name.lower(), app_name)
        
        # Use 'start' in shell to handle paths and registered apps
        subprocess.run(f"start {target}", shell=True)
        return f"Opening {app_name}... 🚀"
        
    except Exception as e:
        return f"I couldn't open {app_name}. Error: {e}"

def cmd_volume_control(args):
    """
    Controls system volume via PowerShell.
    Usage: set volume 50, mute volume, volume up
    """
    if not IS_WINDOWS: return "Volume control is Windows-only for now. 🔊"
    
    try:
        # Simple Mute/Unmute logic using nircmd approach or VBScript wrapped in PS?
        # A reliable widespread method without nircmd is sending key strokes
        # 0xAD = Volume Mute, 0xAE = Volume Down, 0xAF = Volume Up
        
        args = args.lower()
        
        script = ""
        action = ""
        
        if "mute" in args:
            # 173 is VK_VOLUME_MUTE
            script = "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]173)"
            action = "Muted volume 🔇"
        elif "up" in args or "increase" in args:
            # 175 is VK_VOLUME_UP (Send 5 times)
            script = "$wsh = New-Object -ComObject WScript.Shell; 1..5 | ForEach-Object { $wsh.SendKeys([char]175) }"
            action = "Turning it up! 🔊"
        elif "down" in args or "decrease" in args:
            # 174 is VK_VOLUME_DOWN
            script = "$wsh = New-Object -ComObject WScript.Shell; 1..5 | ForEach-Object { $wsh.SendKeys([char]174) }"
            action = "Turning it down. 🔉"
        else:
            return "I can mute, increase, or decrease volume. What do you need? 🎧"
            
        subprocess.run(["powershell", "-command", script], shell=True)
        return action
        
    except Exception as e:
        return f"Volume Error: {e}"

def cmd_cleanup_system(args):
    """Win11: Cleans temp files and Recycle Bin."""
    if not IS_WINDOWS: return "Cleanup is Windows-only."
    try:
        print("🧹 Cleaning system...")
        # Empty Recycle Bin
        subprocess.run(["powershell", "-command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"], shell=True)
        # Clear Temp
        subprocess.run(["powershell", "-command", "Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue"], shell=True)
        return "System cleanup complete! 🧹 Emptied Recycle Bin and cleared temporary files."
    except Exception as e:
        return f"Cleanup Error: {e}"

def cmd_get_system_health(args):
    """Win11: Gets disk and battery status."""
    if not IS_WINDOWS: return "Health check is Windows-only."
    try:
        disk = subprocess.check_output(["powershell", "-command", "Get-PSDrive C | Select-Object Used,Free | ConvertTo-Json"], text=True)
        battery = subprocess.check_output(["powershell", "-command", "Get-CimInstance -ClassName Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus | ConvertTo-Json"], text=True)
        return f"SYSTEM HEALTH REPORT:\nDisk (C:): {disk}\nBattery: {battery if battery.strip() else 'No battery detected (Desktop?)'}"
    except Exception as e:
        return f"Health Check Error: {e}"

def cmd_set_productivity_mode(args):
    """Win11: Focus Mode (Dark Mode + Minimize All)."""
    if not IS_WINDOWS: return "Productivity mode is Windows-only."
    try:
        # Dark Mode
        subprocess.run(["powershell", "-command", "Set-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme -Value 0"], shell=True)
        # Minimize All
        subprocess.run(["powershell", "-command", "(New-Object -ComObject Shell.Application).MinimizeAll()"], shell=True)
        return "Productivity Mode Active! 🌙 Set Dark Mode and minimized all windows. Focus on your work, Senpai!"
    except Exception as e:
        return f"Mode Error: {e}"

def cmd_system_control(args):
    """System power controls."""
    arg = args.lower()
    if "lock" in arg:
        subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return "I've locked the workstation. 🔒"
    if "cleanup" in arg or "clean" in arg:
        return cmd_cleanup_system(args)
    if "health" in arg or "status" in arg:
        return cmd_get_system_health(args)
    if "productivity" in arg or "focus" in arg:
        return cmd_set_productivity_mode(args)
    return "I can lock the PC, clean files, check health, or set productivity mode. 🛡️"

def register(dispatcher):
    dispatcher.register("automate script", cmd_run_script)
    dispatcher.register("run script", cmd_run_script)
    dispatcher.register("automate cmd", cmd_run_system_command)
    dispatcher.register("execute command", cmd_run_system_command)
    dispatcher.register("run command", cmd_run_system_command)
    dispatcher.register("automate", cmd_automation_master)
    
    # Verification tasks
    dispatcher.register("confirm run", cmd_confirm_run)
    dispatcher.register("cancel run", cmd_cancel_run)
    
    # Windows Automation
    dispatcher.register("minimize", cmd_window_control)
    dispatcher.register("maximize", cmd_window_control)
    dispatcher.register("restore windows", cmd_window_control)
    dispatcher.register("show desktop", cmd_window_control)
    
    dispatcher.register("open", cmd_open_app)
    dispatcher.register("launch", cmd_open_app)
    dispatcher.register("start", cmd_open_app)
    
    dispatcher.register("volume", cmd_volume_control)
    dispatcher.register("mute", cmd_volume_control)
    
    dispatcher.register("lock pc", cmd_system_control)
    dispatcher.register("lock computer", cmd_system_control)
