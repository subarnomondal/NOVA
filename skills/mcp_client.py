import os
import json
import asyncio
import threading
from rich.console import Console

console = Console()

# We will store active sessions here
_mcp_sessions = {}
_loop = None

def start_mcp_loop():
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_forever()

# Start the background asyncio loop
_thread = threading.Thread(target=start_mcp_loop, daemon=True)
_thread.start()

async def _connect_server(server_name, config, dispatcher):
    from mcp.client.stdio import stdio_client, StdioServerParameters
    from mcp.client.session import ClientSession
    
    server_params = StdioServerParameters(
        command=config["command"],
        args=config.get("args", []),
        env=None
    )
    
    console.print(f"[dim]Connecting to MCP server: {server_name}[/dim]")
    
    try:
        # We need to keep the context managers open.
        # This requires a slightly more complex async structure, but for simplicity
        # we will use an AsyncExitStack
        from contextlib import AsyncExitStack
        stack = AsyncExitStack()
        
        read, write = await stack.enter_async_context(stdio_client(server_params))
        session = await stack.enter_async_context(ClientSession(read, write))
        
        await session.initialize()
        _mcp_sessions[server_name] = (session, stack)
        
        # Discover tools
        tools_response = await session.list_tools()
        for tool in tools_response.tools:
            tool_name = tool.name
            trigger_name = f"mcp {server_name} {tool_name}"
            
            # Create a synchronous wrapper for dispatcher
            def tool_handler(user_input, s_name=server_name, t_name=tool_name):
                # We need to parse arguments from user_input (LLM output usually)
                # For simplicity, we just pass the user input as a string argument "query"
                # In a real scenario, LLM would output JSON.
                import json
                try:
                    args = json.loads(user_input)
                except:
                    args = {"query": user_input}
                    
                if _loop is None:
                    return "Error: Event loop not initialized"
                future = asyncio.run_coroutine_threadsafe(
                    _mcp_sessions[s_name][0].call_tool(t_name, arguments=args),
                    _loop
                )
                try:
                    res = future.result(timeout=30)
                    return str(res.content)
                except Exception as e:
                    return f"Error executing MCP tool: {e}"
            
            # Register in dispatcher
            dispatcher.register(trigger_name, tool_handler)
            console.print(f"[green]✅ Registered MCP Tool:[/green] {trigger_name}")
            
    except Exception as e:
        console.print(f"[red]❌ Failed to connect to MCP {server_name}: {e}[/red]")


def register(dispatcher):
    config_path = os.path.join("userdata", "config", "mcp_clients.json")
    if not os.path.exists(config_path):
        return
        
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            
        if _loop is None:
            return
            
        for name, config in data.get("servers", {}).items():
            asyncio.run_coroutine_threadsafe(_connect_server(name, config, dispatcher), _loop)
            
    except Exception as e:
         console.print(f"[red]Error loading MCP clients: {e}[/red]")

def unload(dispatcher):
    # Cleanup logic if needed
    if _loop is not None:
        for name, (session, stack) in _mcp_sessions.items():
            asyncio.run_coroutine_threadsafe(stack.aclose(), _loop)
    _mcp_sessions.clear()
