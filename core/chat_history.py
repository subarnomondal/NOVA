import json
import os
from datetime import datetime

class ChatHistory:
    def __init__(self, history_file=os.path.join("userdata", "chat_history.json")):
        self.history_file = history_file
        self.history = self.load_history()

    def load_history(self):
        """Load history from JSON file."""
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading chat history: {e}")
            return []

    def save_chat(self, user_input, assistant_response):
        """Save a new chat exchange to the log."""
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": assistant_response
        }
        self.history.append(exchange)
        
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
        for exchange in self.history[-limit:]:
            context += f"User: {exchange['user']}\n"
            context += f"Nova: {exchange['assistant']}\n"
        return context

# Singleton instance
chat_history = ChatHistory()
