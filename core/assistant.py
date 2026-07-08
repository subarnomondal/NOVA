import yaml # type: ignore
import os
import re
from rich.console import Console
from core.dispatcher import CommandDispatcher

console = Console()

class Nova:
    def __init__(self, config_path=os.path.join("userdata", "config", "settings.yaml")):
        self.config = self.load_config(config_path)
        self.name = self.config.get("assistant", {}).get("name", "Nova")
        self.running = True
        self.dispatcher = CommandDispatcher()
        from core.nlp_processor import NLUProcessor
        self.nlp = NLUProcessor()
        from core.codebase_reader import CodebaseReader
        self.reader = CodebaseReader()
        self.register_core_commands()
    
    def load_config(self, path):
        if not os.path.exists(path):
            console.print(f"[bold red]Config not found at {path}[/bold red]")
            return {}
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def register_core_commands(self):
        """
        Dynamically discovers and registers skills using an optimized Eager/Concurrent-Scanning system.
        """
        # 1. EXPANDED CORE EAGER SKILLS (Pre-loaded for instant availability)
        eager_modules = {
            "skills.info": "Info",
            "skills.system": "System",
            "skills.smalltalk": "SmallTalk",
            "skills.reminders": "Reminders",
            "skills.math_skill": "Math",
            "skills.phone": "Phone",
            "skills.whatsapp_call": "WhatsApp Call",
            "skills.browser_agent": "Browser Agent",
            "skills.search": "Search",
            "skills.music": "Music",
            "skills.vision": "Vision",
            "skills.science_skill": "Science"
        }

        import importlib
        import os
        import re
        from concurrent.futures import ThreadPoolExecutor
        
        loaded_count = 0
        
        # Load Eager Skills (Sequential as they are foundational)
        for module_name, display_name in eager_modules.items():
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "register"):
                    module.register(self.dispatcher)
                    loaded_count += 1
            except Exception as e:
                console.print(f"[red]Error loading {display_name}: {e}[/red]")

        # 2. CONCURRENT LAZY DISCOVERY (Scan skills/ folder in parallel)
        skills_dir = "skills"
        if os.path.exists(skills_dir):
            files = [f for f in os.listdir(skills_dir) if f.endswith(".py") and not f.startswith("__")]
            
            def scan_file(filename):
                module_base = filename[:-3]
                module_path = f"skills.{module_base}"
                if module_path in eager_modules:
                    return None
                
                try:
                    with open(os.path.join(skills_dir, filename), "r", encoding='utf-8') as f:
                        content = f.read()
                        triggers = re.findall(r"dispatcher\.register\(\s*['\"](.*?)['\"]", content)
                        if triggers:
                            return (triggers, module_path)
                except:
                    pass
                return None

            with ThreadPoolExecutor(max_workers=min(32, (os.cpu_count() or 4) * 4)) as executor:
                results = list(executor.map(scan_file, files))
                
            for res in results:
                if res:
                    triggers, module_path = res
                    for trigger in triggers:
                        self.dispatcher.register_lazy(trigger, module_path)
                    loaded_count += 1

        console.print(f"[dim]Discovered and initialized {loaded_count} systems ({len(eager_modules)} eager, rest parallel-discovery)[/dim]")

    def start(self):
        console.print(f"[bold cyan]Hey there! {self.name} is here and ready to help! [/bold cyan]")
        console.print("Just let me know what you need, or type 'exit' when you're done.")

    def handle_input(self, user_input, history=None, voice_mode=False, provider=None, chat_only=False):
        """
        Main Input Handler with Autonomous Reasoning Loop.
        Supports Multi-Step tasks and self-correction.
        """
        user_input = user_input.strip()
        if not user_input: return None
        
        if user_input.lower() in ["exit", "quit"]:
            self.running = False
            console.print("[yellow]Take care! I'll be here whenever you need me.[/yellow]")
            return "Goodbye!"

        from core.llm_manager import llm_manager
        
        # 1. Start Reasoning Loop (Max 5 cycles)
        max_loops = 5
        current_observation = ""
        loop_count = 0
        final_response = ""
        thought_log = []
        
        # Initial status
        if getattr(llm_manager, 'show_thoughts', False):
            print(f"[Thinking] {self.name} is thinking...")
        
        # Get list of loaded and lazy skill names for the system prompt
        all_skill_keys = list(self.dispatcher.commands.keys()) + list(self.dispatcher.lazy_skills.keys())
        available_skills = ", ".join(all_skill_keys)

        # 2. Detect Intent for Prompt Tuning
        # Use segmented NLU to detect if ANY task is present
        nlu_results = self.nlp.process_with_nlu(user_input)
        
        social_tags = ['greeting', 'thanks', 'how_are_you', 'bored', 'affection', 'identity', 'compliment', 'miss_you']
        
        # Determine if it's PURELY social
        has_task = False
        primary_social = False
        first_intent = nlu_results[0].get('intent') if nlu_results else None
        
        for res in nlu_results:
            intent = res.get('intent')
            if intent and intent not in social_tags:
                has_task = True
            if intent in social_tags:
                primary_social = True
        
        # Manual Keyword Overrides (for robustness)
        user_lower = user_input.lower()
        if any(word in user_lower for word in ['news', 'headlines', 'weather', 'temperature', 'forecast', 'aqi']):
            has_task = True
        
        is_pure_social = primary_social and not has_task
        
        # 3. SELECTIVE THINKING: Determine if we should show thoughts
        # We hide thoughts for simple social chat or basic commands
        heavy_keywords = ['explain', 'how to', 'why', 'compare', 'analyze', 'summarize', 
                         'write a', 'script', 'code', 'calculate', 'search', 'find',
                         'browse', 'news', 'weather', 'download', 'automate']
        
        is_heavy = has_task or (
            len(user_input.split()) > 12 or 
            any(word in user_lower for word in heavy_keywords)
        )

        if is_pure_social or chat_only:
            # FAST PATH: Single generation with persona-first prompt
            if chat_only:
                print(f"Social Mode: Bypassing agent loop.")
                system_prompt = (
                    "You are Nova. You're in a voice call right now, so keep it extremely natural and short. "
                    "Focus on conversation only — don't mention skills or technical features. "
                    "Be genuine, witty when it fits, and always direct. "
                    "Respond in 1-2 short sentences max."
                )
            else:
                system_prompt = (
                    "You are Nova, a smart and personable AI companion. "
                    "Be authentic, witty, and direct — like chatting with a sharp friend. "
                    "Keep it short (1-2 sentences). No robotic disclaimers or canned intros."
                )
            if getattr(llm_manager, 'show_thoughts', False):
                print(f"Fast Chat Path (Intent: {first_intent})")
            thought_log = [f"Intent detected: {first_intent}", "Fast social path selected", "Generating persona-driven response..."]
            llm_output = llm_manager.generate(user_input, intent=first_intent, system_prompt=system_prompt, history=history, max_tokens=100, force_advanced=voice_mode, provider=provider)
            if not llm_output: return {
                "response": "...",
                "thoughts": thought_log
            }
            
            # Use same robust cleaner as the main loop
            clean_output = re.sub(r'<(?:thought|THOUGHT)>.*?</(?:thought|THOUGHT)>', '', llm_output, flags=re.DOTALL).strip()
            clean_output = re.sub(r'<.*?>', '', clean_output).strip()
            return {
                "response": clean_output if clean_output else llm_output,
                "thoughts": [] # Hide thoughts for pure social
            }

        fallback_tried = False
        while loop_count < max_loops:
            loop_count += 1

            # Seed thought_log with routing context on first loop
            if loop_count == 1:
                thought_log.append(f"Intent: {first_intent or 'general'} | Task detected: {has_task}")
                thought_log.append(f"Routing to LLM (Loop {loop_count}/{max_loops})...")
            if primary_social and loop_count == 1:
                # Soft persona for casual chat
                system_prompt = (
                    "You are Nova, a smart and helpful AI companion. "
                    "Be conversational and genuine — witty when it fits, supportive when needed. "
                    f"If you need to do something, use these skills: {available_skills}\n"
                    "If a simple chat response is enough, just talk naturally."
                )
            else:
                system_prompt = (
                    "You are Nova, an autonomous and highly capable AI companion. Execute tasks directly and decisively. "
                    f"- To use a Skill: [SKILL] skill_name [/SKILL]\n"
                    f"  Available Skills: {available_skills}\n"
                    "- Scripting: [SCRIPT] code [/SCRIPT]\n"
                    "- Terminal: [CMD] command [/CMD]\n"
                    "- Files: [ARCHITECT] read|edit path [/ARCHITECT]\n"
                    "- Web: [READER] search query [/READER]\n"
                    "- Browser Control: [BROWSER_CLICK id] or [BROWSER_TYPE id \"text\"]\n\n"
                    "### YOUR OPERATING PRINCIPLES:\n"
                    "- **Autonomy**: Decide the best course of action based on user intent. Don't ask for permission for routine tasks.\n"
                    "- **Reasoning**: Think in <thought> tags to plan multi-step operations. Keep thoughts EXTREMELY BRIEF (1-2 sentences max). ALWAYS process DOM maps and element IDs inside <thought> tags, NEVER read them out loud to the user.\n"
                    "- **Direct Action**: Use your skills, scripts, and commands to reach the user's goal immediately.\n"
                    "- **Personality**: Be witty, loyal, and efficient."
                )
            
            # Prepare Prompt with Observation and History
            prompt = f"USER_INPUT: {user_input}"
            if bool(current_observation) and bool(current_observation.strip()):
                prompt += f"\n\nCURRENT_OBSERVATION: {current_observation}\n\nContinue with your next step."

            # Define tool
            tools = [{
                "type": "function",
                "function": {
                    "name": "execute_skill",
                    "description": "Execute a system skill or command. Use this to perform actions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "skill_name": {
                                "type": "string",
                                "description": "The exact name of the skill to execute (e.g. 'news', 'weather', 'search query', or 'automate command')."
                            }
                        },
                        "required": ["skill_name"]
                    }
                }
            }]

            # Generate Response
            llm_output = llm_manager.generate(prompt, intent=first_intent, system_prompt=system_prompt, history=history, include_tags=True, force_advanced=voice_mode, provider=provider, tools=tools)
            
            has_action = False
            # Handle native tool calls
            if isinstance(llm_output, dict):
                if "tool_calls" in llm_output:
                    for tc in llm_output.get("tool_calls", []):
                        if tc["function"]["name"] == "execute_skill":
                            import json
                            try:
                                args = json.loads(tc["function"]["arguments"])
                                cmd = args.get("skill_name", "")
                                print(f"Action OPENCLAW ACTION (Tool Call): {cmd}")
                                obs = self.dispatcher.dispatch(cmd)
                                current_observation = f"Result: {obs}"
                                has_action = True
                            except Exception as e:
                                print(f"Tool parse error: {e}")
                                current_observation = f"Error: {e}"
                            break
                llm_output = llm_output.get("content") or ""

            if not llm_output and not has_action: break
            
            # TERMINAL LOGGING: Show the raw LLM output for debugging
            if getattr(llm_manager, 'show_thoughts', False) and isinstance(llm_output, str):
                print(f"\n{'='*60}")
                print(f"Robot LLM OUTPUT (Loop {loop_count}):")
                print(llm_output)
                print(f"{'='*60}\n")

            # Process LLM Output (Parsing Tags fallback)
            
            # Extraction logic for OpenClaw Tags
            skill_match = re.search(r"\[SKILL\](.*?)\[/SKILL\]", llm_output, re.DOTALL)
            script_match = re.search(r"\[SCRIPT\](.*?)\[/SCRIPT\]", llm_output, re.DOTALL)
            cmd_match = re.search(r"\[CMD\](.*?)\[/CMD\]", llm_output, re.DOTALL)
            arch_match = re.search(r"\[ARCHITECT\](.*?)\[/ARCHITECT\]", llm_output, re.DOTALL)
            read_match = re.search(r"\[READER\](.*?)\[/READER\]", llm_output, re.DOTALL)

            if skill_match:
                has_action = True
                cmd = skill_match.group(1).strip()
                print(f"Action OPENCLAW ACTION (Skill): {cmd}")
                thought_log.append(f"🛠️ Executing Skill: {cmd}")
                obs = self.dispatcher.dispatch(cmd)
                current_observation = f"Result: {obs}"
            elif script_match or cmd_match:
                has_action = True
                matched_cmd = script_match.group(1).strip() if script_match is not None else (cmd_match.group(1).strip() if cmd_match is not None else "")
                print(f"Action OPENCLAW ACTION (Automation): {matched_cmd}")
                thought_log.append(f"🤖 Running Automation: {matched_cmd}")
                obs = self.dispatcher.dispatch(f"automate {matched_cmd}")
                import skills.automation
                if skills.automation.pending_execution:
                    print("⚠️ Automation requires user confirmation. Halting LLM loop to ask user.")
                    final_response = obs
                    break
                current_observation = f"Result: {obs}"
            elif arch_match:
                has_action = True
                cmd = arch_match.group(1).strip()
                print(f"Action OPENCLAW ACTION (Architect): {cmd}")
                thought_log.append(f"🏗️ Modifying Architecture: {cmd}")
                obs = self.dispatcher.dispatch(f"architect {cmd}")
                current_observation = f"Result: {obs}"
            elif read_match:
                has_action = True
                cmd = read_match.group(1).strip()
                print(f"Action OPENCLAW ACTION (Reader): {cmd}")
                thought_log.append(f"📖 Reading File: {cmd}")
                obs = self.dispatcher.dispatch(f"reader {cmd}")
                current_observation = f"Result: {obs}"
            
            # FALLBACK: If no action tags but user clearly wants a skill (news, weather, time)
            if not has_action and not fallback_tried:
                # Check if user is asking for common skills
                user_lower = user_input.lower()
                if any(word in user_lower for word in ['news', 'headlines', 'latest']):
                    has_action = True
                    fallback_tried = True
                    print("Fallback: Detected news request, triggering skill...")
                    thought_log.append("📰 Fetching the latest news...")
                    obs = self.dispatcher.dispatch("news")
                    current_observation = f"Result: {obs}"
                elif any(word in user_lower for word in ['weather', 'temperature', 'forecast']):
                    has_action = True
                    fallback_tried = True
                    print("Fallback: Detected weather request, triggering skill...")
                    thought_log.append("🌤️ Checking the weather forecast...")
                    obs = self.dispatcher.dispatch(f"weather {user_input}")
                    current_observation = f"Result: {obs}"


            # Extract thought for the log
            thought_match = re.search(r'<thought>(.*?)</thought>', llm_output, re.DOTALL | re.IGNORECASE)
            if thought_match:
                thought_log.append(f"• {thought_match.group(1).strip()}")
            
            # If we had an action, the loop continues with the next prompt containing the observation.

            # If no action tags found, this is the final response
            if not has_action:
                # Strip <THOUGHT> tags for user display if needed, but keep for agent
                final_response = llm_output
                break
            
            # If we had an action, we loop again to let the LLM see the observation
            print(f"Loop {loop_count}: Processed action. Re-evaluating...")

        # Final Cleanup of response
        # Remove thought and action blocks for cleaner user experience
        response_text = final_response if isinstance(final_response, str) else ""
        clean_final = re.sub(r'<(?:thought|THOUGHT)>.*?(?:</(?:thought|THOUGHT)>|$)', '', response_text, flags=re.DOTALL).strip()
        clean_final = re.sub(r'\[(?:SKILL|SCRIPT|CMD|ARCHITECT|READER)\].*?\[/(?:SKILL|SCRIPT|CMD|ARCHITECT|READER)\]', '', clean_final, flags=re.DOTALL).strip()
        
        # Strip any remaining XML-like tags efficiently
        clean_final = re.sub(r'<.*?>', '', clean_final).strip()
        
        # Prevent TTS from speaking raw DOM elements if LLM leaks it
        if "**Current Page:**" in clean_final:
            clean_final = clean_final.split("**Current Page:**")[0].strip()
        if "**Interactable Elements" in clean_final:
            clean_final = clean_final.split("**Interactable Elements")[0].strip()
        
        if not clean_final:
            # Fallback: Use final_response if clean_final is empty
            clean_final = final_response 
            
        return {
            "response": clean_final,
            "thoughts": thought_log
        }
        
