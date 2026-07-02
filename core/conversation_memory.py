"""
Conversation Memory Module for NOVA
Stores and retrieves conversation history for context-aware responses
"""

import json
import os
from datetime import datetime
from typing import List, Dict
import threading

class ConversationMemory:
    def __init__(self, memory_file=os.path.join("userdata", "conversation_history.json"), max_context=15):
        self.memory_file = memory_file
        self.max_context = max_context  # Increased for 1.5B model
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
                print(f"💾 Loaded {len(self.conversations)} previous conversations")
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
            import threading
            threading.Thread(target=_save, daemon=True).start()
        else:
            _save()
    
    def add_conversation(self, user_input: str, nova_response: str, language: str = "en"):
        """Add a conversation turn to memory with thread safety"""
        with self._lock:
            conversation = {
                'timestamp': datetime.now().isoformat(),
                'user': user_input,
                'nova': nova_response,
                'language': language
            }
            
            self.conversations.append(conversation)
            
            # Cap archive at 1000 items to prevent RAM bloat
            if len(self.conversations) > 1000:
                self.conversations = self.conversations[-1000:]
            
            self.save_memory()
            print(f"💾 Conversation saved. History size: {len(self.conversations)}")

    def find_relevant_memories(self, query: str, limit: int = 3) -> str:
        """Simple keyword-based retrieval of older relevant conversations"""
        if len(self.conversations) <= self.max_context:
            return ""
            
        query_words = set(query.lower().split())
        scored_memories = []
        
        # Search archive (excluding the immediate context which is handles separately)
        archive = self.conversations[:-self.max_context]
        
        for conv in archive:
            score = 0
            user_text = conv.get('user', '').lower()
            for word in query_words:
                if len(word) > 3 and word in user_text:
                    score += 1
            if score > 0:
                scored_memories.append((score, conv))
                
        # Sort by score and then recency
        scored_memories.sort(key=lambda x: (x[0], x[1]['timestamp']), reverse=True)
        
        relevant = scored_memories[:limit]
        if not relevant:
            return ""
            
        output = "\nPAST RELEVANT MEMORIES:\n"
        for _, conv in relevant:
            output += f"- On {conv['timestamp'][:10]}, you said: '{conv['user']}' and I replied: '{conv['nova']}'\n"
        return output
    
    def get_recent_context(self, n: int = 10) -> List[Dict]:
        """Get recent conversation context with thread safety"""
        with self._lock:
            if n is None:
                n = self.max_context
            return list(self.conversations[-n:]) if self.conversations else []
    
    def get_context_string(self, n: int = 10) -> str:
        """Get recent context as formatted string for LLM"""
        recent = self.get_recent_context(n)
        if not recent:
            return ""
        
        context_lines = ["Recent conversation history:"]
        for conv in recent:
            # Calculate relative time if possible
            time_str = ""
            try:
                dt = datetime.fromisoformat(conv['timestamp'])
                diff = datetime.now() - dt
                if diff.total_seconds() < 60:
                    time_str = "[Just now]"
                elif diff.total_seconds() < 3600:
                    mins = int(diff.total_seconds() / 60)
                    time_str = f"[{mins}m ago]"
                else:
                    hours = int(diff.total_seconds() / 3600)
                    time_str = f"[{hours}h ago]"
            except:
                pass
                
            context_lines.append(f"{time_str} User: {conv['user']}")
            context_lines.append(f"Nova: {conv['nova']}")
        
        return "\n".join(context_lines)
    
    def clear_memory(self):
        """Clear all conversation history"""
        self.conversations = []
        self.save_memory()
        print("🗑️ Conversation memory cleared")
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            'total_conversations': len(self.conversations),
            'memory_file': self.memory_file,
            'max_context': self.max_context
        }

    @property
    def conversation_history(self):
        """Backward compatibility alias for conversations"""
        return self.conversations

    def clear_history(self):
        """Alias for clear_memory for backward compatibility"""
        return self.clear_memory()
