"""
Windows Command & System Automation Skill for Nova
Provides advanced control over Windows internals, networking, and system maintenance.
"""

import os
import subprocess
import psutil
import socket
import platform
import requests
from datetime import datetime

def cmd_system_info(args):
    """Usage: system info, pc details"""
    try:
        uname = platform.uname()
        boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        
        # Disk Info
        partitions = psutil.disk_partitions()
        disk_usage = ""
        for partition in partitions:
            if 'fixed' in partition.opts or 'cdrom' in partition.opts: continue
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage += f"- {partition.device}: {usage.percent}% used ({usage.free // (2**30)} GB free)\n"
            except: pass

        response = f"### 🖥️ Windows System Report\n\n"
        response += f"**OS:** {uname.system} {uname.release} ({uname.version})\n"
        response += f"**Processor:** {uname.processor}\n"
        response += f"**System Uptime:** Since {boot_time}\n"
        response += f"\n**💾 Disk Usage:**\n{disk_usage if disk_usage else 'No fixed drives detected.'}\n\n"
        response += "*smiles* Your system is looking healthy! Let me know if you need any maintenance. ✨"
        
        return response
    except Exception as e:
        return f"I had trouble gathering system info: {e}"

def cmd_network_status(args):
    """Usage: network status, ip info, check internet"""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Get public IP
        try:
            public_ip = requests.get('https://api.ipify.org', timeout=3).text
        except:
            public_ip = "Unavailable"
            
        response = f"### 🌐 Network Diagnostics\n\n"
        response += f"**Hostname:** {hostname}\n"
        response += f"**Local IP:** {local_ip}\n"
        response += f"**Public IP:** {public_ip}\n"
        response += f"\n**Connection:** {'✅ Online' if public_ip != 'Unavailable' else '❌ Offline'}\n\n"
        response += "*nods* Everything seems to be flowing correctly. 🌊"
        return response
    except Exception as e:
        return f"Network check failed: {e}"

def cmd_process_list(args):
    """Usage: task list, show processes"""
    try:
        # Get top 10 processes by memory usage
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        processes = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:10]
        
        response = "### 📑 Resource Intensive Processes\n\n"
        response += "| PID | Process Name | RAM % |\n"
        response += "| :--- | :--- | :--- |\n"
        for p in processes:
            response += f"| {p['pid']} | {p['name']} | {p['memory_percent']:.1f}% |\n"
        
        response += "\n*smiles* Need me to terminate any of these for you? Just say 'kill process name'."
        return response
    except Exception as e:
        return f"Process check failed: {e}"

def cmd_kill_process(args):
    """Usage: kill <process name>"""
    name = args.lower().replace("kill", "").replace("terminate", "").replace("stop process", "").strip()
    if not name:
        return "Which process should I terminate? Please be careful! ⚠️"
        
    try:
        terminated = 0
        for proc in psutil.process_iter(['name']):
            if name in proc.info['name'].lower():
                proc.kill()
                terminated += 1
        
        if terminated > 0:
            return f"*nods* I've terminated {terminated} instances of '{name}'. System breathing room restored! 🌬️"
        else:
            return f"I couldn't find any running process with the name '{name}'. 🔍"
    except Exception as e:
        return f"I failed to kill the process: {e}"

def cmd_flush_dns(args):
    """Usage: flush dns, fix network"""
    try:
        print("[System] Flushing DNS...")
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
        return "*smiles* DNS cache has been flushed! This might help with your connection issues. 🌐✨"
    except Exception as e:
        return f"Failed to flush DNS: {e}"

def cmd_disk_cleanup(args):
    """Usage: disk cleanup, clean drives"""
    try:
        # This opens the Windows Disk Cleanup utility
        subprocess.Popen("cleanmgr.exe /d C", shell=True)
        return "I've launched the Windows Disk Cleanup utility for you. *smiles* It's good to keep things tidy! 🧹"
    except Exception as e:
        return f"Couldn't launch cleanmgr: {e}"

def register(dispatcher):
    dispatcher.register("system info", cmd_system_info)
    dispatcher.register("pc details", cmd_system_info)
    dispatcher.register("specs", cmd_system_info)
    
    dispatcher.register("network status", cmd_network_status)
    dispatcher.register("ip info", cmd_network_status)
    dispatcher.register("check internet", cmd_network_status)
    
    dispatcher.register("task list", cmd_process_list)
    dispatcher.register("show processes", cmd_process_list)
    dispatcher.register("resource usage", cmd_process_list)
    
    dispatcher.register("kill process", cmd_kill_process)
    dispatcher.register("terminate process", cmd_kill_process)
    
    dispatcher.register("flush dns", cmd_flush_dns)
    dispatcher.register("clean drives", cmd_disk_cleanup)
    dispatcher.register("disk cleanup", cmd_disk_cleanup)
