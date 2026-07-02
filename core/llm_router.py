import re
from core.llm_manager import llm_manager

class IntentRouter:
    def __init__(self):
        # We prefer Groq for routing because it is ultra-fast.
        self.preferred_provider = "groq"

    def determine_skill(self, user_input, dispatcher):
        """
        Uses the LLM to map a natural language user request to an exact system command keyword.
        """
        if not user_input or len(user_input.split()) < 2:
             return None # Too short for complex intent routing

        # 1. Gather all valid commands from the dispatcher
        # Filter out emergency/panic commands or very short ones to prevent false positives
        valid_commands = []
        
        all_keys = list(dispatcher.commands.keys()) + list(dispatcher.lazy_skills.keys())
        for key in all_keys:
            if key not in ["stop all skills", "emergency abort"]:
                valid_commands.append(key)
        
        if not valid_commands:
            return None
            
        commands_list_str = "\n".join([f"- {cmd}" for cmd in valid_commands])

        # 2. Build the zero-shot prompt
        system_prompt = (
            "You are an intent-routing engine for Nova AI.\n"
            "Your ONLY job is to map the user's natural language request to exactly ONE of the available system commands.\n"
            "If the user is asking you to perform an action (e.g. searching the web, opening an app, taking a screenshot), output the EXACT command string from the list.\n"
            "If the user is just chatting, asking a conversational question, or no command matches, output 'NONE'.\n"
            "DO NOT output anything else except the exact command string or 'NONE'.\n\n"
            "Available commands:\n"
            f"{commands_list_str}"
        )

        # 3. Call the LLM in "raw" mode (no memory, no personality, fast response)
        try:
            print(" Advanced Router: Analyzing intent...")
            response = llm_manager.generate(
                user_input=user_input,
                system_prompt=system_prompt,
                raw_gen=True,
                provider=self.preferred_provider, # Try ultra-fast Groq first
                max_tokens=20,
                temperature=0.1
            )
            
            if not response:
                return None
                
            result = response.strip()
            
            # Clean up the result just in case the LLM added quotes or extra text
            result = re.sub(r'["\']', '', result)
            
            # 4. Validate the response against the allowed commands
            for cmd in valid_commands:
                if result.lower() == cmd.lower():
                    print(f" Advanced Router Map: '{user_input}' => '{cmd}'")
                    return cmd
                    
            return None
            
        except Exception as e:
            print(f"⚠️ Intent Router Error: {e}")
            return None

# Singleton instance
intent_router = IntentRouter()
