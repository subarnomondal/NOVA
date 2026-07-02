
"""
Instant Reply Generator for Nova
Uses GPT4All LLM to generate fast, dynamic, personality-aligned responses
"""

import random
from datetime import datetime

class InstantReplyGenerator:
    def __init__(self, personality_manager):
        self.personality_manager = personality_manager
        
        # Use optimized LLM Manager (singleton)
        from core.llm_manager import llm_manager
        self.llm_manager = llm_manager
        
        # Intent-specific prompt templates for fast LLM generation
        # REMOVED: thanks, goodbye, apology, compliment, how_are_you to allow natural LLM variation
        # Only keep truly instant/skill-based intents
        self.intent_prompts = {
            "joke": "joke",
            # Removed conversational intents to prevent repetitive responses
            # All greeting/thanks/goodbye now go through main LLM for variety
        }
        
    def _load_llm(self):
        """Load LLM via optimized manager."""
        if self.llm_manager.provider:
            return True # Assume manager handles its own loading status
        return self.llm_manager.load_model()
        
    def can_instant_reply(self, intent, confidence):
        """Check if this intent can be handled with an instant reply."""
        # Only use instant replies for high-confidence, simple intents
        if confidence < 0.75:
            return False
            
        return intent in self.intent_prompts
    
    def generate(self, intent, user_input=""):
        """Generate an instant reply using optimized LLMManager."""
        if intent not in self.intent_prompts:
            return None
        
        # Load LLM if needed
        if not self._load_llm():
            return self._fallback_response(intent)
        
        # Use optimized manager for generation
        intent_key = self.intent_prompts.get(intent)
        
        try:
            response = self.llm_manager.generate(
                user_input if user_input else f"User triggered {intent}",
                intent=intent_key,
                max_tokens=50,
                temperature=0.7
            )
            
            if response:
                # Apply personality humanization
                try:
                    response = self.personality_manager.humanize_text(response)
                except:
                    pass
                return response
            else:
                # If filtered out, use fallback
                return self._fallback_response(intent)
                
        except Exception as e:
            print(f"⚠️ LLM generation error: {e}")
            return self._fallback_response(intent)
    
    def _fallback_response(self, intent):
        """Static fallback if LLM fails."""
        fallbacks = {
            "greeting": "Hey there! What can I do for you? ✨",
            "thanks": "You're welcome! *smiles*",
            "apology": "It's fine. Don't worry about it. ",
            "affection": "*blushes* W-What are you saying all of a sudden?!",
            "joke": "Why did the AI go to school? To improve its learning algorithms! *giggles*",
            "compliment": "*blushes* T-Thank you... That's very kind of you to say. ",
            "goodbye": "Bye for now! I'll be here when you need me. ✨",
            "how_are_you": "I'm doing well! Thanks for asking. How about you? ",
            "gaming": "Gaming? I enjoy strategy games. They keep my mind sharp! "
        }
        
        response = fallbacks.get(intent, "I'm here! What do you need? ✨")
        
        try:
            response = self.personality_manager.humanize_text(response)
        except:
            pass
            
        return response
    
    def get_stats(self):
        """Get statistics about instant reply coverage."""
        llm_stats = self.llm_manager.get_stats() if hasattr(self, 'llm_manager') else {}
        return {
            "total_intents": len(self.intent_prompts),
            "supported_intents": list(self.intent_prompts.keys()),
            "llm_loaded": llm_stats.get("model_loaded", False),
            "memory_size": llm_stats.get("memory_size", 0)
        }

if __name__ == "__main__":
    # Test
    class MockPM:
        def humanize_text(self, text):
            return text
    
    irg = InstantReplyGenerator(MockPM())
    print(f" Instant Reply Stats: {irg.get_stats()}")
    print(f"\n Testing LLM Generation...")
    print(f"Greeting: {irg.generate('greeting')}")
    print(f"Thanks: {irg.generate('thanks')}")
