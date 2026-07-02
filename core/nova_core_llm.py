import logging
from core.llm_manager import llm_manager

class NovaCoreLLM:
    """
    Nova Core LLM (High-performance Local Brain)
    Acts as a wrapper around the unified LLMManager to provide
    conversational capabilities using the API.
    """
    def __init__(self):
        self.initialized = True
        self.llm = llm_manager
        print(" Nova Core: Linked to Main LLM Manager (API-Only)")
        
    def predict(self, text):
        """
        Legacy/Placeholder for intent prediction. 
        Real intent classification is handled by NeuralChat (custom_llm) or NLU.
        """
        return {"response": None, "confidence": 0.0}

    def select_emotion(self, user_input, history):
        """
        Selects an emotion tag based on context. 
        For now, we can simple return 'neutral' or use simple heuristics,
        or ask the LLM (expensive). 
        Let's use a simple heuristic for speed.
        """
        text = user_input.lower()
        if any(w in text for w in ['sad', 'cry', 'grief', 'upset']): return "Empathy"
        if any(w in text for w in ['happy', 'joy', 'lol', 'haha', 'great']): return "Joy/Playful"
        if any(w in text for w in ['angry', 'hate', 'mad']): return "Calm/De-escalation"
        return "Neutral/Professional"

    def generate_response(self, user_input, history, custom_emotion=None, ltm_context=None):
        """
        Generates a response using the local LLM via LLMManager.
        """
        try:
            # Construct a system prompt context
            emotion_instruction = f"(Emotional State: {custom_emotion})" if custom_emotion else ""
            ltm_instruction = f"\nLONG TERM MEMORY:\n{ltm_context}" if ltm_context else ""
            
            system_prompt = (
                f"You are Nova. {emotion_instruction}"
                f"{ltm_instruction}"
                "\nProvide a concise, helpful, and character-driven response."
            )
            
            # Delegate to LLM Manager
            # We use raw_gen=False to allow LLM Manager to handle its own context if needed,
            # but here we are providing specific history/context.
            # actually llm_manager.generate handles history if we don't pass system_prompt with "RECENT CONVERSATION".
            # But the caller passes `history` (list of dicts or string?).
            # desktop.py line 1677: history = memory.get_recent_context(10) -> returns list of dicts typically?
            # Let's check memory.get_recent_context. usually it returns a list.
            # For simplicity, we'll let llm_manager handle the context insertion if we don't force it.
            
            # However, looking at desktop.py line 1685, we pass `history`.
            # llm_manager.generate signature: 
            # generate(self, user_input, intent=None, max_tokens=250, temperature=0.7, system_prompt=None, raw_gen=False, provider=None)
            
            # We'll construct a prompt string from history + input if we want strict control,
            # or just pass user_input and let llm_manager append to its internal memory?
            # desktop.py calls memory.add_conversation AFTER generation (line 1616).
            # So llm_manager might not have the *latest* context if we don't pass it?
            # llm_manager.generate() uses self.conversation_memory.
            
            # Let's just pass the user input and a good system prompt.
            # We will ignore the `history` argument here relying on LLMManager's internal memory 
            # OR we should format `history` into system_prompt.
            
            formatted_history = ""
            if isinstance(history, list):
                formatted_history = "\nRECENT CHAT:\n" + "\n".join([f"{h.get('role','User')}: {h.get('content','')}" for h in history])
            
            full_prompt = f"{system_prompt}\n{formatted_history}"
            
            response = self.llm.generate(
                user_input=user_input,
                system_prompt=full_prompt,
                max_tokens=150, # Fast response
                temperature=0.7
            )
            return response
            
        except Exception as e:
            print(f"❌ Nova Core Generation Error: {e}")
            return None

    def generate(self, prompt, **kwargs):
        """Legacy generate method"""
        return self.generate_response(prompt, [], **kwargs)

nova_core_llm = NovaCoreLLM()
