import json
import os
from datetime import datetime

class ChatHistory:
    def __init__(self, history_file=os.path.join("userdata", "chat_history.json")):
        self.history_file = history_file
        self.history = self.load_history()
        self.session_history = []  # Fresh context on every startup

    def load_history(self):
        """Load history from JSON file and purge data older than 7 days."""
        if not os.path.exists(self.history_file):
            return []
        try:
            from datetime import timedelta
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Auto-delete messages older than 7 days
                now = datetime.now()
                cutoff_date = now - timedelta(days=7)
                
                filtered_data = []
                for item in data:
                    try:
                        timestamp = datetime.fromisoformat(item.get("timestamp", ""))
                        if timestamp >= cutoff_date:
                            filtered_data.append(item)
                    except Exception:
                        filtered_data.append(item)
                        
                return filtered_data
        except Exception as e:
            print(f"⚠️ Error loading chat history: {e}")
            return []

    def save_chat(self, user_input, assistant_response):
        """Save a new chat exchange to the log (using LLM background summarization)."""
        import threading
        
        # Add to the fresh session history immediately so the LLM remembers the exact current conversation
        self.session_history.append({
            "user": user_input,
            "assistant": assistant_response
        })
        
        def _save_task():
            try:
                from core.llm_manager import LLMManager
                llm = LLMManager()
                
                # Ask LLM if this is important or small talk
                prompt = (
                    f"Evaluate this exchange:\nUser: {user_input}\nNova: {assistant_response}\n\n"
                    "Is this important/noteworthy (contains facts, tasks, deep thoughts, complex instructions) "
                    "OR is it just trivial small talk (greetings, simple reactions, meaningless chatter)? "
                    "If important, reply with a 1-sentence summary of the exchange. "
                    "If it is trivial small talk, reply with EXACTLY 'SKIP'."
                )
                
                evaluation = llm.generate(prompt, max_tokens=100, raw_gen=True)
                
                if evaluation and "SKIP" not in evaluation:
                    # Clean up the summary text
                    summary = evaluation.replace("1-sentence summary: ", "").replace("Summary: ", "").strip()
                    
                    exchange = {
                        "timestamp": datetime.now().isoformat(),
                        "user": user_input,
                        "assistant": summary
                    }
                    self.history.append(exchange)
                    self._cleanup_and_save()
            except Exception as e:
                print(f"⚠️ Error in smart chat save: {e}")
                
        # Run in background to avoid blocking the main chat response
        threading.Thread(target=_save_task, daemon=True).start()

    def _cleanup_and_save(self):
        from datetime import timedelta
        now = datetime.now()
        cutoff_date = now - timedelta(days=7)
        
        new_history = []
        for item in self.history:
            try:
                timestamp = datetime.fromisoformat(item.get("timestamp", ""))
                if timestamp >= cutoff_date:
                    new_history.append(item)
            except Exception:
                new_history.append(item)
                
        self.history = new_history
        
        # Keep the disk file relatively lean (last 1000 messages)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
            
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            print(f"⚠️ Error saving chat history: {e}")

    def get_recent_context(self, limit=10):
        """Get the last N items in a format for the LLM."""
        context = ""
        for exchange in self.session_history[-limit:]:
            context += f"User: {exchange['user']}\n"
            context += f"Nova: {exchange['assistant']}\n"
        return context

# Singleton instance
chat_history = ChatHistory()
