
"""
Optimized LLM Manager for Nova (Strictly API-Only)
Uses Google Gemini API (free tier) as primary LLM provider.
"""

import threading
import re
import os
from core.emotion_detector import emotion_detector
from core.personality_manager import PersonalityManager
from core.key_manager import key_manager
import base64
import json
import requests # type: ignore

class LLMManager:
    _instance = None
    _llm = None
    _load_lock = threading.Lock()
    _execution_lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._llm = None 
            self.provider = "custom" # Locked to Local
            self.conversation_memory = []
            self.max_memory = 5 
            self.emotion_detector = emotion_detector
            self.initialized = True
            
            # Runtime stats
            self.last_provider = "Unknown"
            self.last_model = "None"
            self.last_error_code = 0
            
            self._gemini_key = self._load_gemini_key()
            self.online_mode = bool(self._gemini_key)
            
            # Load settings from centralized userdata
            try:
                settings_path = os.path.join("userdata", "settings.json")
                if os.path.exists(settings_path):
                    with open(settings_path, "r", encoding='utf-8') as f:
                        settings = json.load(f)
                        self.show_thoughts = settings.get("llm", {}).get("show_thoughts", False)
                else:
                    self.show_thoughts = False
            except:
                self.show_thoughts = False
            
            if self.show_thoughts:
                print("🧠 Thought Process Visualization Enabled")
            
            self.personality_manager = PersonalityManager()
            self.base_persona = self.personality_manager.get_active_personality()["system_prompt"]

    @property
    def model(self):
        """Compatibility property for old 'model' access."""
        return self._llm

    def get_few_shot_examples(self, user_input, limit=3):
        """Load relevant reasoning examples from the dataset based on user input keywords."""
        examples = []
        dataset_path = os.path.join("userdata", "datasets", "nova_skills_dataset.jsonl")
        try:
            if os.path.exists(dataset_path):
                # Basic keyword extraction for relevance
                keywords = re.findall(r'\w+', user_input.lower())
                
                with open(dataset_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # Filter for relevance first
                    relevant_lines = []
                    for line in lines[-100:]: # Look at recent/complex ones
                        if line.strip():
                            line_lower = line.lower()
                            if any(kw in line_lower for kw in keywords if len(kw) > 3):
                                relevant_lines.append(line)
                    
                    # Fallback to random if no keyword match
                    import random
                    if not relevant_lines:
                        relevant_lines = lines[-20:]
                    
                    selected = random.sample(relevant_lines, min(len(relevant_lines), limit))
                    for line in selected:
                        ex = json.loads(line)
                        user_msg = ex["messages"][0]["content"]
                        assistant_msg = ex["messages"][1]["content"]
                        examples.append(f"User: {user_msg}\nNova: {assistant_msg}")
        except Exception as e:
            print(f"⚠️ Error loading few-shot examples: {e}")
        return "\n\n".join(examples)
    
    def load_model(self, provider_override=None):
        """No-op. We no longer load a local model."""
        print("🧠 Skipping local brain load (API-Only Mode Enabled)...")
        return True



    def add_to_memory(self, user_input, assistant_response):
        """Add exchange to conversation memory."""
        self.conversation_memory.append({
            "user": user_input,
            "assistant": assistant_response
        })
        if len(self.conversation_memory) > self.max_memory:
            self.conversation_memory.pop(0)
    
    def get_temporal_context(self, user_profile=None):
        """Build temporal and profile context."""
        try:
            from core.time_context import TimeContextManager
            
            if user_profile:
                up = user_profile
            else:
                from core.user_profile import UserProfile
                up = UserProfile()
            
            tc = TimeContextManager()
            day_context = tc.get_day_context()
            user_name = up.get_name()
            
            context = "\n\nCURRENT SITUATION:\n"
            context += f"- User Name: {user_name}\n"
            
            time_prompt = tc.get_time_prompt()
            context += f"- Time Context: {time_prompt}\n"
            
            context += f"- Current Date: {day_context['date']}\n"
            context += f"- Day of Week: {day_context['day_of_week']}\n"
            
            personal_context = up.get_personalization_context()
            if personal_context:
                context += f"- {personal_context}\n"

            # Added: Long-Term Memory (Facts)
            try:
                from core.ltm_manager import LTMManager
                ltm_temp = LTMManager(memory_file=os.path.join("userdata", "user_facts.json"))
                if ltm_temp.facts:
                    facts_str = ", ".join(list(ltm_temp.facts.values())[-5:])
                    context += f"- User Facts: {facts_str}\n"
            except: pass

            # Added: User Patterns
            try:
                patterns_path = os.path.join("userdata", "user_patterns.json")
                if os.path.exists(patterns_path):
                    with open(patterns_path, "r") as f:
                        patterns = json.load(f)
                        if patterns:
                            context += f"- Behavior Patterns: {list(patterns.keys())[:3]}\n"
            except: pass
            
            return context
        except:
            return ""

    def get_context_prompt(self):
        if not self.conversation_memory: return ""
        context = "\n\nRECENT CONVERSATION:\n"
        for exchange in self.conversation_memory[-3:]:
            context += f"User: {exchange['user']}\n"
            context += f"Nova: {exchange['assistant']}\n"
        return context
    
    def filter_response(self, response):
        if not response: return None
        
        response = re.sub(r'<\|im_start\|>.*?<\|im_end\|>', '', response, flags=re.DOTALL)
        response = re.sub(r'<\|im_start\|>.*', '', response)
        response = re.sub(r'<\|im_end\|>', '', response)
        response = re.sub(r'TASK:.*', '', response, flags=re.IGNORECASE)
        
        # Remove thoughts (robust to colons/spacing)
        # ONLY remove thoughts if show_thoughts is FALSE
        if not getattr(self, 'show_thoughts', False):
            response = re.sub(r'<THOUGHT>.*?</THOUGHT>', '', response, flags=re.DOTALL | re.IGNORECASE)
            response = re.sub(r'<THOUGHT>.*', '', response, flags=re.DOTALL | re.IGNORECASE) # Catch unclosed thoughts at end
        
        # Strip XML-like tags only, keep *personality* markers
        response = re.sub(r'<[a-zA-Z/][^>]*>', '', response) 
        
        response = re.sub(r'\[.*?\]', '', response)
        # removed: response = re.sub(r'\*.*?\*', '', response)
        response = re.sub(r'\((?:allows|adjusts|looks|smiles|sighs|chuckles|laughs).*?\)', '', response, flags=re.IGNORECASE)
        
        bad_headers = [
            r"THOUGHT:", r"Example:", r"Scenario:", r"Internal reasoning:", 
            r"Action Performed:", r"Character Response:", 
            r"Nova:", r"Rivu:", r"Riva:", r"User:", r"Speaker:"
        ]
        for header in bad_headers:
            response = re.sub(header, '', response, flags=re.IGNORECASE)
            
        response = response.strip()
        response = re.sub(r'^[\":\s]+', '', response)
        if "User:" in response:
            response = response.split("User:")[0].strip()
            
        return response
    
    def detect_repetition(self, new_response):
        if not new_response or len(self.conversation_memory) < 2:
            return False
        
        recent_responses = [exchange['assistant'] for exchange in self.conversation_memory[-3:]]
        if new_response in recent_responses:
            return True
        
        for prev_response in recent_responses:
            if len(new_response) > 20 and len(prev_response) > 20:
                new_words = set(new_response.lower().split())
                prev_words = set(prev_response.lower().split())
                if len(new_words) > 0:
                    overlap = len(new_words & prev_words) / len(new_words)
                    if overlap > 0.8:
                        return True
        return False
    
    def break_loop(self):
        self.conversation_memory.clear()
        return "Let me clear my head for a sec... Okay, what were we talking about?"

    def _load_gemini_key(self):
        return key_manager.get_key("gemini")

    # Gemini blocked by user request
    def _generate_gemini(self, user_input, system_prompt, history=None):
        return None

    def _load_openrouter_swarm(self):
        """Deprecated: Replaced by Smart Key Manager get_working_key()"""
        pass


    def _generate_openrouter(self, user_input, system_prompt, history=None):
        """Primary Brain via OpenRouter API with Smart Multi-Key Swarm support."""
        try:
            import requests # type: ignore
            headers_base = {
                "Content-Type": "application/json",
                "HTTP-Referer": "https://nova-assistant.local", 
                "X-Title": "Nova AI"
            }
            
            # Current validated free models on OpenRouter (Swarm priorities)
            models = [
                "mistralai/pixtral-12b:free" if user_input.get("image_path") else "openrouter/free", 
                "google/gemini-flash-1.5-free",
                "openrouter/free", # Let OpenRouter choose a working free model
                "google/gemma-2-9b-it:free",
                "meta-llama/llama-3.1-8b-instruct:free",
                "qwen/qwen-2.5-72b-instruct:free",
                "meta-llama/llama-3.2-3b-instruct:free",
                "deepseek/deepseek-r1:free"
            ]

            
            for model in models:
                # Max 3 retries (swarm rotations) per model
                for attempt in range(3):
                    api_key = key_manager.get_working_key("openrouter")
                    if not api_key:
                        print("⚠️ No valid OpenRouter keys available.")
                        return None
                        
                    headers = headers_base.copy()
                    headers["Authorization"] = f"Bearer {api_key}"
                    
                    # Added: Few-Shot Examples for Reasoning
                    few_shot = self.get_few_shot_examples(user_input)
                    
                    # Persona-first instructions for the model
                    enhanced_system_prompt = f"{system_prompt}\n" \
                                             f"- Be reactive — respond emotionally to what the user says. Laugh, show surprise, be genuinely engaged.\n" \
                                             f"- Stay in character as Nova at all times.\n" \
                                             f"### FEW-SHOT REASONING EXAMPLES:\n{few_shot}"
                    
                    # Construct messages
                    messages_payload = [{"role": "system", "content": enhanced_system_prompt}]
                    
                    if history:
                        lines = history.strip().split('\n')
                        for line in lines:
                            if line.startswith("User:"):
                                messages_payload.append({"role": "user", "content": line.replace("User:", "").strip()})
                            elif line.startswith("Nova:"):
                                messages_payload.append({"role": "assistant", "content": line.replace("Nova:", "").strip()})
                    
                    # Multimodal Support (Image + Text)
                    if isinstance(user_input, dict) and user_input.get("image_path"):
                        from core.vision_manager import vision_manager
                        b64_image = vision_manager.encode_image_base64(user_input["image_path"])
                        if b64_image:
                            content_blocks = [
                                {"type": "text", "text": user_input.get("text", "")},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{b64_image}"
                                    }
                                }
                            ]
                            # Ensure content is passed as string if the provider doesn't support blocks
                            messages_payload.append({"role": "user", "content": str(content_blocks)})
                        else:
                            messages_payload.append({"role": "user", "content": user_input.get("text", "")})
                    else:
                        messages_payload.append({"role": "user", "content": user_input})

                    data = {
                        "model": model,
                        "messages": messages_payload,
                        "temperature": 0.5 if isinstance(user_input, dict) and user_input.get("image_path") else 0.7,
                        "max_tokens": 800 if isinstance(user_input, dict) and user_input.get("image_path") else 500
                    }

                    
                    print(f"📡 Requesting {model} OpenRouter (Attempt {attempt+1}/3)...")
                    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
                    self.last_error_code = response.status_code
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "choices" in result and result["choices"]:
                            self.last_provider = "OpenRouter"
                            self.last_model = model
                            return result["choices"][0]["message"]["content"]
                    elif response.status_code == 429:
                        print(f"⚠️ OpenRouter Rate Limited (429) for {model}. Flagging key for cooldown.")
                        key_manager.report_key_failure("openrouter", api_key, "rate_limit")
                        continue # Try next key in swarm
                    elif response.status_code in [401, 403, 402]:
                        print(f"⚠️ OpenRouter Quota/Auth Error for {model}. Flagging key for heavy cooldown.")
                        key_manager.report_key_failure("openrouter", api_key, "quota_exceeded")
                        continue
                    else:
                        print(f"⚠️ OpenRouter Error {response.status_code} for {model}: {response.text[:100]}")
                        break # Skip this model on fatal non-auth/non-limit error
                        
            return None
        except Exception as e:
            print(f"⚠️ OpenRouter Exception: {e}")
            return None

    def _generate_groq(self, user_input, system_prompt, history=None):
        """Generate response via Groq API (Smart Swarm Mode)."""
        try:
            import requests
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            # Try multiple models for the free tier
            models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
            
            for model in models:
                # Max 3 retries (swarm rotations) per model
                for attempt in range(3):
                    api_key = key_manager.get_working_key("groq")
                    if not api_key:
                        print("⚠️ No valid Groq keys available.")
                        return None
                        
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    messages = [{"role": "system", "content": system_prompt}]
                    if history:
                        lines = history.strip().split('\n')
                        for line in lines:
                            if line.startswith("User:"):
                                messages.append({"role": "user", "content": line.replace("User:", "").strip()})
                            elif line.startswith("Nova:"):
                                messages.append({"role": "assistant", "content": line.replace("Nova:", "").strip()})
                    
                    messages.append({"role": "user", "content": user_input})

                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500
                    }

                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    self.last_error_code = response.status_code
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "choices" in result and result["choices"]:
                            self.last_provider = "Groq"
                            self.last_model = model
                            return result["choices"][0]["message"]["content"]
                            
                    elif response.status_code == 429:
                        print(f"⚠️ Groq Rate Limited (429). Flagging key for cooldown.")
                        key_manager.report_key_failure("groq", api_key, "rate_limit")
                        continue
                    elif response.status_code in [401, 403]:
                        print(f"⚠️ Groq Quota/Auth Error. Flagging key for heavy cooldown.")
                        key_manager.report_key_failure("groq", api_key, "quota_exceeded")
                        continue
                    else:
                        print(f"⚠️ Groq {model} Error: {response.status_code}")
                        break # Fatal error, try next model
            
        except Exception as e:
            print(f"⚠️ Groq Exception: {e}")
        return None

    def _generate_ollama(self, user_input, system_prompt, model_name="llama3"):
        """High-Power Local Brain via Ollama."""
        try:
            import requests
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model_name,
                "prompt": f"{system_prompt}\n\nUser: {user_input}\nAssistant:",
                "stream": False
            }
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get("response", "")
            return None
        except Exception as e:
            print(f"⚠️ Ollama Error: {e}")
            return None

    def generate(self, user_input, intent=None, max_tokens=250, temperature=0.7, system_prompt=None, raw_gen=False, provider=None, history=None, include_tags=False, force_advanced=False, image_path=None):
        """Generate response using the OpenRouter or Ollama API."""
        
        # Multimodal handling: user_input becomes a dict if image is present
        actual_input = user_input
        if image_path:
            actual_input = {"text": user_input, "image_path": image_path}

        if raw_gen:
            full_system_prompt = system_prompt if system_prompt else ""
        else:
            # Detect emotion based on text only
            text_for_emotion = user_input if not isinstance(user_input, dict) else user_input.get("text", "")
            emotions = self.emotion_detector.detect_emotion(text_for_emotion, top_k=2)
            primary_emotion = emotions[0] if emotions else {"emotion": "neutral", "confidence": 0.0}
            
            # Load UserProfile once for context and gender
            user_profile = None
            try:
                from core.user_profile import UserProfile
                user_profile = UserProfile()
            except: pass

            context = self.get_temporal_context(user_profile)
            
            # History is now handled separately in the prompt_format section below
            # to ensure it uses proper dialogue turns.
            if history:
                 pass # Will be processed in generation loop
            elif not system_prompt or "RECENT CONVERSATION:" not in system_prompt:
                # context += self.get_context_prompt() # Removing from context to avoid duplication
                pass
                
            emotion_guide = ""
            # Ensure confidence is float for comparison
            confidence = float(primary_emotion.get('confidence', 0))
            if confidence > 0.4:
                emotion = primary_emotion['emotion']
                if emotion in ["sadness", "grief"]: emotion_guide = "\n(The user seems down — be warm, supportive, and don't be overly cheerful.)"
                elif emotion in ["anger", "annoyance"]: emotion_guide = "\n(The user seems frustrated — stay calm, acknowledge their feelings, and focus on solutions.)"
                elif emotion in ["joy", "love"]: emotion_guide = "\n(User is happy.)"
      
            intent_guide = ""
            if intent == "greeting": intent_guide = "\n(Respond with a warm short greeting)"
            
            gender_guide = ""
            if user_profile:
                try:
                    user_name = user_profile.get_name()
                    if user_name and user_name != "User":
                        gender_guide = f"\n(The user's name is {user_name}. Use it naturally when appropriate.)"
                except: pass
            
            current_persona = self.personality_manager.get_active_personality()["system_prompt"]
            if system_prompt:
                # Merge: Persona first, then technical instructions if any
                full_system_prompt = f"{current_persona}\n\n{system_prompt}{context}{emotion_guide}{intent_guide}{gender_guide}"
            else:
                full_system_prompt = f"{current_persona}{context}{emotion_guide}{intent_guide}{gender_guide}"
        
            try: # Outer try block for overall generation process
                # ADVANCED BRAIN TRIGGER
                # Route to Gemini if:
                # 1. Specifically forced
                # 2. Online Mode is enabled AND query is complex/long
                # 3. Intent is knowledge-seeking
                is_complex = len(user_input.split()) > 15 or "?" in user_input
                knowledge_intents = ['knowledge_query', 'science_query', 'history_query', 'philosophical_queries', 'problem_solving', 'search_query', 'news_query', 'news', 'search']
                
                # Provider Routing: OpenRouter -> Groq -> Gemini -> Ollama
                if not raw_gen:
                    # 1. Try OpenRouter first (Verified working free swarm)
                    if provider == "free" or not provider:
                        print("🚀 Routing to OpenRouter (Verified Free Swarm)...")
                        try:
                            resp = self._generate_openrouter(actual_input, full_system_prompt, history=history)
                            if resp:
                                return self._process_response_text(resp, text_for_emotion, include_tags)

                        except Exception as e:
                            print(f"⚠️ OpenRouter failed: {e}")

                    # 2. Try Groq (Ultra-Fast but check keys)
                    if provider == "groq" or (not provider and not self.last_provider == "OpenRouter"):
                        print("⚡ Routing to Groq (Ultra-Fast)...")
                        try:
                            resp = self._generate_groq(user_input, full_system_prompt, history=history)
                            if resp:
                                return self._process_response_text(resp, user_input, include_tags)
                        except Exception as e:
                            print(f"⚠️ Groq failed: {e}")

                    # 2. Fallback to Ollama (Standard local-only)
                    # (Gemini fallback removed by user request)

                # OLLAMA PROVIDER (Fallback)
                if provider == "ollama" or (not provider and os.getenv("USE_OLLAMA") == "true"):
                    print("🦙 Routing to Ollama...")
                    ollama_resp = self._generate_ollama(user_input, full_system_prompt)
                    if ollama_resp:
                        return self._process_response_text(ollama_resp, user_input, include_tags)

                if self.last_error_code == 429:
                    return "My brain is a bit overwhelmed right now (Rate Limit). Please try again in a few seconds!"
                return "I'm having trouble waking up my brain. Please check your API keys in keys.json."

            except Exception as e:
                print(f"❌ Generation failed: {e}")
                return None

    def load_model(self):
        """Dummy method for compatibility with CAR workflow/hybrid versions."""
        print("ℹ️ LLM Manager: API-Only mode active. No local model loading required.")
        return True

    def load_scratch_model(self):
        """Dummy method for compatibility."""
        return True


    def _process_response_text(self, response_text, user_input, include_tags):
        """Helper to filter and store response text"""
        if include_tags:
            self.add_to_memory(user_input, response_text)
            return response_text

        filtered = self.filter_response(response_text)
        
        if filtered:
            if self.detect_repetition(filtered):
                return self.break_loop()
            
            # Humanize the final text to remove 'model' feel
            humanized = self.personality_manager.humanize_text(filtered)
            self.add_to_memory(user_input, humanized)
            return humanized
        return None

    def get_stats(self):
        """Get LLM statistics status."""
        return {
            "model_loaded": True,
            "provider": f"{self.last_provider} API",
            "model_name": self.last_model,
            "memory_size": len(self.conversation_memory)
        }

# Singleton
llm_manager = LLMManager()
