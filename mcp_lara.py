
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

from core.assistant import Clio

# Initialize Clio in a background thread to avoid blocking MCP startup
clio_instance = None
clio_lock = threading.Lock()

def get_clio():
    global clio_instance
    with clio_lock:
        if clio_instance is None:
            print(" Initializing CLIO for MCP...")
            clio_instance = Clio()
        return clio_instance

# Create FastMCP server
mcp = FastMCP("CLIO")

@mcp.tool()
def ask_clio(query: str) -> str:
    """
    Send a natural language query to CLIO. CLIO can perform system tasks, 
    web searches, automation, and more.
    """
    n = get_clio()
    result = n.handle_input(query)
    if isinstance(result, dict):
        return result.get("response", "No response from CLIO.")
    return str(result)

@mcp.tool()
def execute_skill(command: str) -> str:
    """
    Directly execute a CLIO skill by command keyword.
    Example: 'weather Mumbai', 'volume up', 'lock pc'
    """
    n = get_clio()
    response = n.dispatcher.dispatch(command)
    return str(response) if response else "Skill executed (no output)."

@mcp.tool()
def get_system_health() -> str:
    """Get the current system health report (CPU, RAM, Disk, Battery)."""
    n = get_clio()
    result = n.dispatcher.dispatch("status health")
    return str(result) if result else "No health data available."

@mcp.tool()
def list_skills() -> List[str]:
    """List all currently active and available CLIO skills."""
    n = get_clio()
    active = list(n.dispatcher.commands.keys())
    lazy = list(n.dispatcher.lazy_skills.keys())
    return sorted(list(set(active + lazy)))

@mcp.tool()
def take_screenshot() -> str:
    """Take a screenshot of the primary display and save to userdata/screenshots."""
    n = get_clio()
    result = n.dispatcher.dispatch("screenshot")
    return str(result) if result else "Screenshot captured."

@mcp.tool()
def search_web(query: str) -> str:
    """Perform a web and knowledge search using DuckDuckGo and Wikipedia."""
    n = get_clio()
    result = n.dispatcher.dispatch(f"search {query}")
    if isinstance(result, dict):
        return result.get("response", str(result))
    return str(result) if result else "No search results found."

@mcp.tool()
def calculate(expression: str) -> str:
    """Solve mathematical or scientific calculation queries."""
    n = get_clio()
    result = n.dispatcher.dispatch(f"calculate {expression}")
    return str(result) if result else "Could not solve the expression."

@mcp.tool()
def add_expense(expense_text: str) -> str:
    """Log an expense (e.g. '50 for coffee' or 'lunch 25')."""
    n = get_clio()
    result = n.dispatcher.dispatch(f"add expense {expense_text}")
    return str(result) if result else "Expense logged."

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
