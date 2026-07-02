
import time
import importlib
import re

class CommandDispatcher:
    def __init__(self):
        self.commands = {}
        self.lazy_skills = {} # Mapping of trigger -> module_path
        self.loaded_modules = {} # Mapping of module_path -> module object
        
        # AGI Session Context: Persistent data during a multi-step chain
        from core.agi_context import agi_context
        self.agi_context = agi_context
        
        # Register core "Panic" command
        self.register("stop all skills", self._panic_stop)
        self.register("emergency abort", self._panic_stop)

    def register(self, keyword, handler):
        self.commands[keyword.lower()] = handler
        # If it was in lazy_skills, remove it
        if keyword.lower() in self.lazy_skills:
            del self.lazy_skills[keyword.lower()]

    def register_lazy(self, keyword, module_path):
        """Registers a command that triggers a module load on first use."""
        if keyword.lower() not in self.commands:
            self.lazy_skills[keyword.lower()] = module_path

    def _load_lazy_skill(self, keyword):
        """Loads a skill from its module path and registers it."""
        module_path = self.lazy_skills.get(keyword)
        if not module_path:
            return False
        return self.load_module_manually(module_path)

    def load_module_manually(self, module_path):
        """Directly loads and registers a module by path."""
        try:
            print(f"⚡ Loading Skill Module: {module_path}...")
            module = importlib.import_module(module_path)
            if hasattr(module, "register"):
                module.register(self)
                self.loaded_modules[module_path] = module
                return True
            else:
                print(f"⚠️ Warning: Module {module_path} has no 'register' function.")
        except Exception as e:
            print(f"❌ Failed to Load {module_path}: {e}")
            
        return False

    def unload_module_manually(self, module_path):
        """Calls the 'unload' hook on a skill module to stop its activity."""
        module = self.loaded_modules.get(module_path)
        if module and hasattr(module, "unload"):
            try:
                print(f" Unloading Skill Module: {module_path}...")
                module.unload(self)
                # We don't remove from loaded_modules (Python caching)
                # But the module is now 'Quiet'.
                return True
            except Exception as e:
                print(f"❌ Error during unload of {module_path}: {e}")
        return False

    def _panic_stop(self, args=None):
        """Emergency stop for all active lazy skills."""
        count = 0
        for path in list(self.loaded_modules.keys()):
            if self.unload_module_manually(path):
                count += 1
        return f"Emergency Abort triggered!  I've attempted to stop {count} active systems."

    def dispatch(self, user_input, nlp_results=None):
        """
        AGI-Enabled Multi-Step Dispatcher.
        """
        # Reset relative context for new utterance
        self.agi_context.reset_chain()
        
        # 1. Handle Multi-Intent Sequence
        if nlp_results and isinstance(nlp_results, list):
            responses = []
            print(f"⛓️ AI Orchestrator: Executing {len(nlp_results)} tasks with context support...")
            
            for i, result in enumerate(nlp_results):
                cmd = result.get('command')
                text = result.get('original_text')
                
                if cmd:
                    # Check if it needs lazy loading
                    if cmd not in self.commands and cmd in self.lazy_skills:
                        self._load_lazy_skill(cmd)
                        
                    if cmd in self.commands:
                        print(f" Step {i+1}: Executing '{cmd}'")
                        try:
                            raw_resp = self.commands[cmd](text)
                            
                            # Process Result (String or Dict)
                            if isinstance(raw_resp, dict):
                                 msg = raw_resp.get("response", "")
                                 self.agi_context.set_result(raw_resp.get("data"))
                                 # Check for PROACTIVE SUGGESTIONS
                                 suggestion = raw_resp.get("suggested_next")
                                 if suggestion:
                                     print(f" Skill Suggested: {suggestion}")
                                     nlp_results.insert(i + 1, {"command": suggestion, "original_text": text})
                            else:
                                 msg = raw_resp
                            
                            responses.append(msg)
                            
                            # if i < len(nlp_results) - 1:
                            #     time.sleep(1) # Optimized from 2s to 1s - REMOVED for speed
                        except Exception as e:
                            print(f"⚠️ Dispatch Step Error: {e}")
            
            if responses:
                return "\n\n".join([str(r) for r in responses if r])
            return None

        # 2. Legacy/Fallback direct string match
        user_input_lower = user_input.lower()
        if not user_input_lower.strip():
            return None
        
        # We need to check both active commands and lazy commands
        all_keys = list(self.commands.keys()) + list(self.lazy_skills.keys())
        sorted_keys = sorted(all_keys, key=len, reverse=True)
        
        for key in sorted_keys:
            # Match whole words only to avoid substring collisions (e.g. 'open' in 'opening')
            # Explicitly cast key to string to satisfy type checker
            if re.search(rf"\b{re.escape(str(key))}\b", user_input_lower):
                # Load if lazy
                if key in self.lazy_skills:
                    self._load_lazy_skill(key)
                
                # Double check after potential load
                if key in self.commands:
                    print(f" Dispatcher: Legacy match for '{key}'")
                    return self.commands[key](user_input)
        
        return None

