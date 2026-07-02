import requests
import time

class OfflineManager:
    def __init__(self):
        self.is_online = True
        self.last_check = 0
        self.check_interval = 30  # Check every 30 seconds
    
    def check_connection(self):
        """Check if internet is available"""
        if time.time() - self.last_check < self.check_interval:
            return self.is_online
        
        try:
            requests.get('https://www.google.com', timeout=3)
            self.is_online = True
        except:
            self.is_online = False
        
        self.last_check = time.time()
        return self.is_online
    
    def get_offline_response(self, intent):
        """Return cached response for offline mode"""
        offline_responses = {
            "search": "I can't search the web right now because I'm offline. Try again when internet is back! ",
            "weather": "Weather data requires an internet connection. I'm currently offline. ☁️",
            "news": "Can't fetch news while offline. Check back when you're connected! ",
            "default": "I'm currently offline, so some features are limited. But I'm still here to chat! "
        }
        return offline_responses.get(intent, offline_responses['default'])
