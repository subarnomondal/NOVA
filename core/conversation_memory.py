"""
Conversation Memory Module for CLIO
Stores and retrieves conversation history for context-aware responses
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import threading

class ConversationMemory:
    def __init__(self, memory_file=os.path.join("userdata", "conversation_history.json"), max_context=15):
        self.memory_file = memory_file
        self.max_context = max_context
        self.conversations = []
        self._lock = threading.Lock()
        self.load_memory()
    
    def load_memory(self):
        """Load conversation history from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conversations = data.get('conversations', [])
                print(f" Loaded {len(self.conversations)} previous conversations")
        except Exception as e:
            print(f"⚠️ Could not load memory: {e}")
            self.conversations = []
    
    def save_memory(self, async_save=True):
        """Save conversation history to file"""
        def _save():
            try:
                os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
                with open(self.memory_file, 'w', encoding='utf-8') as f:
                    json.dump({'conversations': self.conversations}, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"⚠️ Could not save memory: {e}")
        
        if async_save:
            threading.Thread(target=_save, daemon=True).start()
        else:
            _save()
    
    def add_conversation(self, user_input: str, clio_response: str, language: str = "en"):
        """Add a conversation turn to memory with thread safety and auto fact learning"""
        if not user_input or not clio_response:
            return

        user_input_str = str(user_input).strip()
        clio_response_str = str(clio_response).strip()

        # Filter internal system strings
        if user_input_str in ["init_greeting", "ping"]:
            return

        with self._lock:
            # Avoid duplicate consecutive entries
            if self.conversations:
                last_conv = self.conversations[-1]
                if last_conv.get('user') == user_input_str and last_conv.get('clio') == clio_response_str:
                    return

            conversation = {
                'timestamp': datetime.now().isoformat(),
                'user': user_input_str,
                'clio': clio_response_str,
                'language': language
            }
            
            self.conversations.append(conversation)
            
            # Cap archive at 1500 items to prevent RAM bloat
            if len(self.conversations) > 1500:
                self.conversations = self.conversations[-1500:]
            
            self.save_memory()
            print(f" Conversation saved. History size: {len(self.conversations)}")

        # Auto-extract facts, goals, and mood asynchronously via PersonalBrain
        try:
            from core.personal_brain import personal_brain
            personal_brain.learn_from_exchange(user_input_str, clio_response_str)
        except Exception:
            pass

    def get_messages_for_llm(self, limit: int = 15) -> List[Dict[str, str]]:
        """
        Returns recent conversation turns formatted as OpenAI-compatible messages:
        [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}]
        """
        with self._lock:
            if not self.conversations:
                return []
            
            recent = self.conversations[-limit:]
            messages = []
            for turn in recent:
                u = turn.get('user', '').strip()
                a = turn.get('clio', '').strip()
                if u:
                    messages.append({"role": "user", "content": u})
                if a:
                    messages.append({"role": "assistant", "content": a})
            return messages

    def find_relevant_memories(self, query: str, limit: int = 3) -> str:
        """Simple keyword and semantic retrieval of older relevant conversations"""
        with self._lock:
            if len(self.conversations) <= self.max_context:
                return ""
                
            query_words = set(w.lower() for w in query.split() if len(w) > 3)
            if not query_words:
                return ""

            scored_memories = []
            # Search older archive (excluding the immediate context window)
            archive = self.conversations[:-self.max_context]
            
            for conv in archive:
                score = 0
                user_text = conv.get('user', '').lower()
                clio_text = conv.get('clio', '').lower()
                for word in query_words:
                    if word in user_text:
                        score += 2
                    elif word in clio_text:
                        score += 1
                if score > 0:
                    scored_memories.append((score, conv))
                    
            # Sort by score desc, then timestamp desc
            scored_memories.sort(key=lambda x: (x[0], x[1].get('timestamp', '')), reverse=True)
            
            relevant = scored_memories[:limit]
            if not relevant:
                return ""
                
            output = "\nPAST RELEVANT CONVERSATION RECALL:\n"
            for _, conv in relevant:
                ts = conv.get('timestamp', '')[:10]
                output += f"- [{ts}] User: \"{conv.get('user', '')}\" -> Clio: \"{conv.get('clio', '')[:120]}\"\n"
            return output
    
    def get_recent_context(self, n: int = 10) -> List[Dict]:
        """Get recent conversation context with thread safety"""
        with self._lock:
            if n is None:
                n = self.max_context
            return list(self.conversations[-n:]) if self.conversations else []
    
    def get_context_string(self, n: int = 10) -> str:
        """Get recent context as formatted string for LLM (User: ... Clio: ...)"""
        recent = self.get_recent_context(n)
        if not recent:
            return ""
        
        context_lines = []
        for conv in recent:
            context_lines.append(f"User: {conv.get('user', '')}")
            context_lines.append(f"Clio: {conv.get('clio', '')}")
        
        return "\n".join(context_lines)
    
    def get_history_for_ui(self, limit: int = 100) -> List[Dict]:
        """Returns history formatted for web UI presentation"""
        with self._lock:
            return list(self.conversations[-limit:]) if self.conversations else []

    def clear_memory(self):
        """Clear all conversation history"""
        with self._lock:
            self.conversations = []
            self.save_memory(async_save=False)
            print("️ Conversation memory cleared")
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        with self._lock:
            return {
                'total_conversations': len(self.conversations),
                'memory_file': self.memory_file,
                'max_context': self.max_context
            }

    @property
    def conversation_history(self):
        """Backward compatibility alias for conversations"""
        return self.conversations

    @property
    def history(self):
        """Backward compatibility alias for chat_history.history"""
        return self.conversations

    def save_chat(self, user_input, assistant_response):
        """Backward compatibility method for chat_history.save_chat"""
        self.add_conversation(user_input, assistant_response)

    def clear_history(self):
        """Alias for clear_memory for backward compatibility"""
        return self.clear_memory()

# Singleton instance
conversation_memory = ConversationMemory()

