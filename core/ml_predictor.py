
import json
import os
from datetime import datetime
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

class MLPredictor:
    def __init__(self, history_file="usage_history.json"):
        self.history_file = history_file
        self.history_data = []
        self.time_context_model = defaultdict(Counter) # (weekday, hour) -> command counts
        self.load_history()
        
    def load_history(self):
        """Load usage history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history_data = json.load(f)
                    # Rebuild in-memory model
                    for entry in self.history_data:
                        self._update_model(entry)
                print(f" ML Predictor: Loaded {len(self.history_data)} actions.")
            except Exception as e:
                print(f"⚠️ ML Load Error: {e}")
    
    def save_history(self):
        """Save usage history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history_data[-1000:], f) # Keep last 1000 entries
        except Exception as e:
            print(f"⚠️ ML Save Error: {e}")

    def _update_model(self, entry):
        """Update internal probability model"""
        timestamp = datetime.fromisoformat(entry['timestamp'])
        key = (timestamp.weekday(), timestamp.hour)
        command = entry['command']
        self.time_context_model[key][command] += 1

    def log_command(self, command: str):
        """Log a command execution and update model"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command
        }
        self.history_data.append(entry)
        self._update_model(entry)
        self.save_history()

    def predict_next_command(self) -> List[Tuple[str, float]]:
        """
        Predict probable next commands based on current context.
        Returns list of (command, probability).
        """
        now = datetime.now()
        key = (now.weekday(), now.hour)
        
        # Get counts for this specific hour
        counts = self.time_context_model.get(key, Counter())
        
        # If no data for this hour, look at adjacent hours (+/- 1)
        if not counts:
            prev_key = (key[0], (key[1] - 1) % 24)
            next_key = (key[0], (key[1] + 1) % 24)
            counts = self.time_context_model.get(prev_key, Counter()) + self.time_context_model.get(next_key, Counter())
            
        if not counts:
            return []
            
        total = sum(counts.values())
        predictions = []
        for cmd, count in counts.most_common(3):
            predictions.append((cmd, count / total))
            
        return predictions
