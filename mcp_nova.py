
import os
import sys
import threading
from typing import Any, List
from mcp.server.fastmcp import FastMCP

# Add project root to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Ensure userdata directories exist before any core imports
os.makedirs("userdata", exist_ok=True)
os.makedirs("userdata/temp", exist_ok=True)

from core.assistant import Nova

# Initialize Nova in a background thread to avoid blocking MCP startup
nova_instance = None
nova_lock = threading.Lock()

def get_nova():
    global nova_instance
    with nova_lock:
        if nova_instance is None:
            print(" Initializing NOVA for MCP...")
            nova_instance = Nova()
        return nova_instance

# Create FastMCP server
mcp = FastMCP("NOVA")

@mcp.tool()
def ask_nova(query: str) -> str:
    """
    Send a natural language query to NOVA. NOVA can perform system tasks, 
    web searches, automation, and more.
    """
    n = get_nova()
    result = n.handle_input(query)
    if isinstance(result, dict):
        return result.get("response", "No response from NOVA.")
    return str(result)

@mcp.tool()
def execute_skill(command: str) -> str:
    """
    Directly execute a NOVA skill by command keyword.
    Example: 'weather Mumbai', 'volume up', 'lock pc'
    """
    n = get_nova()
    response = n.dispatcher.dispatch(command)
    return str(response) if response else "Skill executed (no output)."

@mcp.tool()
def get_system_health() -> str:
    """Get the current system health report (CPU, RAM, Disk, Battery)."""
    n = get_nova()
    result = n.dispatcher.dispatch("status health")
    return str(result) if result else "No health data available."

@mcp.tool()
def list_skills() -> List[str]:
    """List all currently active and available NOVA skills."""
    n = get_nova()
    active = list(n.dispatcher.commands.keys())
    lazy = list(n.dispatcher.lazy_skills.keys())
    return sorted(list(set(active + lazy)))

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
