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

# State dictionary for tracking confirmations
pending_actions = {}

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
            except Exception:
                pass

        response = f"**System:** Windows {uname.release} | **CPU:** {uname.processor.split(' ')[0]} | **Uptime:** Since {boot_time}\n"
        if disk_usage:
            response += f"**Disks:**\n{disk_usage}"
        return response.strip()
    except Exception as e:
        return f"Error gathering system info: {e}"

def cmd_network_status(args):
    """Usage: network status, ip info, check internet"""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Get public IP
        try:
            public_ip = requests.get('https://api.ipify.org', timeout=3).text
        except Exception:
            public_ip = "Unavailable"
            
        status = '✅ Online' if public_ip != 'Unavailable' else '❌ Offline'
        return f"**Network:** {status} | **Local IP:** {local_ip} | **Public IP:** {public_ip}"
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
        
        processes = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:5]
        
        response = "**Top 5 Resource Intensive Processes:**\n"
        for p in processes:
            response += f"- **{p['name']}** (PID: {p['pid']}, RAM: {p['memory_percent']:.1f}%)\n"
        return response.strip()
    except Exception as e:
        return f"Process check failed: {e}"

def cmd_kill_process(args):
    """Usage: kill <process name>"""
    name = args.lower().replace("kill", "").replace("terminate", "").replace("stop process", "").strip()
    if not name:
        return "Which process should I terminate? Please be careful! ⚠️"
        
    action_key = f"kill_{name}"
    if action_key not in pending_actions:
        pending_actions[action_key] = True
        return f"⚠️ CONFIRMATION REQUIRED: Are you sure you want to terminate '{name}'? Please ask me to do it again to confirm."
    
    del pending_actions[action_key]
        
    try:
        terminated = 0
        for proc in psutil.process_iter(['name']):
            if name in proc.info['name'].lower():
                proc.kill()
                terminated += 1
        
        if terminated > 0:
            return f"✅ Terminated {terminated} instances of '{name}'."
        else:
            return f"❌ Couldn't find process '{name}'."
    except Exception as e:
        return f"Failed to kill process: {e}"

def cmd_flush_dns(args):
    """Usage: flush dns, fix network"""
    if "flush_dns" not in pending_actions:
        pending_actions["flush_dns"] = True
        return "⚠️ CONFIRMATION REQUIRED: Are you sure you want to flush the DNS cache? Ask me again to confirm."
        
    del pending_actions["flush_dns"]
    try:
        print("[System] Flushing DNS...")
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
        return "✅ DNS cache flushed."
    except Exception as e:
        return f"Failed to flush DNS: {e}"

def cmd_disk_cleanup(args):
    """Usage: disk cleanup, clean drives"""
    if "disk_cleanup" not in pending_actions:
        pending_actions["disk_cleanup"] = True
        return "⚠️ CONFIRMATION REQUIRED: Are you sure you want to launch Disk Cleanup? Ask me again to confirm."
        
    del pending_actions["disk_cleanup"]
    try:
        # This opens the Windows Disk Cleanup utility
        subprocess.Popen(["cleanmgr.exe", "/d", "C"])
        return "✅ Launched Disk Cleanup utility."
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
