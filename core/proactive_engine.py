import json
import os
from datetime import datetime, timedelta

class ProactiveEngine:
    def __init__(self):
        self.patterns_file = os.path.join("userdata", "user_patterns.json")
        self.patterns = self.load_patterns()
    
    def load_patterns(self):
        if os.path.exists(self.patterns_file):
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        return {
            "last_weather_check": None,
            "last_news_check": None,
            "daily_routines": [],
            "frequent_commands": {}
        }
    
    def save_patterns(self):
        with open(self.patterns_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)
    
    def log_activity(self, intent):
        """Track user activity patterns"""
        if intent == "weather":
            self.patterns["last_weather_check"] = datetime.now().isoformat()
        elif intent == "news":
            self.patterns["last_news_check"] = datetime.now().isoformat()
        
        # Track frequency
        self.patterns["frequent_commands"][intent] = \
            self.patterns["frequent_commands"].get(intent, 0) + 1
        
        self.save_patterns()
    
    def get_suggestions(self):
        """Generate proactive suggestions"""
        suggestions = []
        now = datetime.now()
        
        # Weather reminder (if not checked today)
        last_weather = self.patterns.get("last_weather_check")
        if last_weather:
            last_check = datetime.fromisoformat(last_weather)
            if (now - last_check).days >= 1 and now.hour >= 7 and now.hour <= 10:
                suggestions.append({
                    "type": "weather",
                    "message": "Good morning! Haven't checked the weather today. Want me to get the forecast? ☀️",
                    "action": "weather"
                })
        
        # News reminder (if not checked in 2 days)
        last_news = self.patterns.get("last_news_check")
        if last_news:
            last_check = datetime.fromisoformat(last_news)
            if (now - last_check).days >= 2:
                suggestions.append({
                    "type": "news",
                    "message": "It's been a while since you checked the news. Catch up? 📰",
                    "action": "news"
                })
        
        return suggestions
