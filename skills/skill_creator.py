import os
import uuid
from rich.console import Console

console = Console()

def create_temp_skill(user_input):
    """
    Dynamically generates a temporary skill using the LLM and registers it.
    Input example: "create temp skill that tells a random joke"
    """
    from core.llm_manager import llm_manager
    from core.assistant import Nova # Assuming we can get the dispatcher instance from global or context if needed.
    
    # Actually, we need access to the dispatcher. Since handlers get called, 
    # we can use the AGI context or we can just access the dispatcher from the skill creator.
    # The dispatcher is passed during register, but we need to pass it to the handler or store it.
    
    prompt = f"""
Write a Python script for a new NOVA skill based on the following request:
"{user_input}"

REQUIREMENTS:
1. It MUST contain a function `def register(dispatcher):` that registers at least one command trigger. Example: `dispatcher.register("my trigger", my_handler_function)`
2. The handler function MUST accept a single argument `user_input` and return a string (the response).
3. Do NOT include any markdown code blocks (like ```python). Return ONLY raw Python code.
4. Keep dependencies to standard library or packages already in NOVA's environment.
"""
    
    console.print(f"[bold cyan]🧠 Generating Temp Skill for:[/bold cyan] {user_input}")
    
    # Generate code using LLM
    raw_code = llm_manager.generate(prompt, max_tokens=1500)
    
    if not raw_code:
         return "Failed to generate skill code."
         
    # Clean up any potential markdown backticks from LLM output
    code = raw_code.replace("```python", "").replace("```", "").strip()
    
    # Generate unique ID for the skill
    skill_id = str(uuid.uuid4())[:8]
    skill_filename = f"temp_skill_{skill_id}.py"
    skill_path = os.path.join("skills", "temp_skills", skill_filename)
    
    try:
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        console.print(f"[green]✅ Temp Skill code saved to {skill_filename}[/green]")
        
        # Load the module manually
        module_path = f"skills.temp_skills.temp_skill_{skill_id}"
        
        # We need the dispatcher. We'll store it as a global in this module when register() is called.
        global _dispatcher
        if _dispatcher:
            success = _dispatcher.load_module_manually(module_path)
            if success:
                return f"Successfully created and loaded temporary skill '{skill_filename}'. You can now use it!"
            else:
                return f"Failed to load the generated skill '{skill_filename}'."
        else:
            return "Error: Dispatcher not initialized in skill_creator."
            
    except Exception as e:
        return f"Error creating temp skill: {e}"

_dispatcher = None

def register(dispatcher):
    global _dispatcher
    _dispatcher = dispatcher
    # Register the trigger
    dispatcher.register("create temp skill", create_temp_skill)
