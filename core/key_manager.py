
"""
Key Manager for NOVA
Centralized handling of API keys for various services
"""

import json
import os
import threading

class KeyManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KeyManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, key_file=os.path.join("userdata", "keys.json")):
        if not hasattr(self, 'initialized'):
            self.key_file = key_file
            self.keys = {}
            self.key_status = {} # Track cohesive load balancing states
            self.load_keys()
            self.initialized = True

    def load_keys(self):
        """Load keys from JSON file"""
        import base64
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Load keys as plaintext (new policy)
                self.keys = {}
                for k, v in data.items():
                    self.keys[k] = v
                    
                print(f"🔑 Key Manager: Loaded {len(self.keys)} keys")
            except Exception as e:
                print(f"⚠️ Key load error: {e}")
                self.keys = {}
        else:
            # Create default structure if not exists
            self.keys = {
                "gemini": "",
                "openai": "",
                "weather_api": "",
                "news_api": "",
                "elevenlabs": ""
            }
            self.save_keys()

    def save_keys(self):
        """Save keys to JSON file (Encoded)"""
        import base64
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
                # Keep keys in plaintext as requested by user
                encoded_data = {}
                for k, v in self.keys.items():
                    encoded_data[k] = v
                        
                with open(self.key_file, 'w', encoding='utf-8') as f:
                    json.dump(encoded_data, f, indent=4)
            except Exception as e:
                print(f"⚠️ Key save error: {e}")

    def get_key(self, service_name):
        """Retrieve a specific API key (Raw)"""
        return self.keys.get(service_name, "")
        
    def get_working_key(self, service_name):
        """
        Smart Load Balancer: Returns the next available healthy key. 
        Rotates via Round-Robin and automatically skips keys on cooldown.
        """
        import time
        keys = self.keys.get(service_name, "")
        
        # Normalize to list
        if isinstance(keys, str):
            keys = [keys] if keys else []
        elif not isinstance(keys, list):
            keys = []
            
        keys = [k for k in keys if k and isinstance(k, str) and k.strip()]
        if not keys: return None
        
        if service_name not in self.key_status:
            self.key_status[service_name] = {"index": 0, "cooldowns": {}}
            
        status = self.key_status[service_name]
        cooldowns = status["cooldowns"]
        
        # Clean expired cooldowns
        now = time.time()
        for k in list(cooldowns.keys()):
            if now > cooldowns[k]:
                del cooldowns[k]
                
        # Find the next working key
        attempts = 0
        while attempts < len(keys):
            idx = status["index"]
            candidate = keys[idx]
            
            # Advance pointer for round-robin
            status["index"] = (idx + 1) % len(keys)
            
            if candidate not in cooldowns:
                return candidate
            attempts += 1
            
        # Fallback: if all keys are exhausted, just return the first one
        # to let the request fail normally, or hope it magically revived.
        print(f"⚠️ SmartKey: ALL keys for {service_name} are currently heavily rate-limited! Forcing fallback.")
        return keys[0]
        
    def report_key_failure(self, service_name, key, error_type="rate_limit"):
        """
        Marks an API key as failed and places it on cooldown.
        error_type: "rate_limit" (429) -> 60s cooldown
        error_type: "quota_exceeded" (401/403) -> 1hr cooldown
        """
        import time
        if service_name not in self.key_status:
            self.key_status[service_name] = {"index": 0, "cooldowns": {}}
            
        cooldown_time = 60 # 60 seconds default for rate limits
        if error_type == "quota_exceeded":
            cooldown_time = 3600 # 1 hour for auth/quota errors
            
        self.key_status[service_name]["cooldowns"][key] = time.time() + cooldown_time
        safe_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "UNKNOWN"
        print(f"🛑 SmartKey: Marked provider '{service_name}' key {safe_key} on '{error_type}' cooldown for {cooldown_time}s.")

    def set_key(self, service_name, key_value):
        """Set or update an API key"""
        self.keys[service_name] = key_value
        self.save_keys()
        print(f"✅ Key updated for: {service_name}")

# Global instance
key_manager = KeyManager()

