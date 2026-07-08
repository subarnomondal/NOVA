"""
Response Optimization System for NOVA
Provides both fast caching and thoughtful reasoning modes
"""

import json
import os
import time
from typing import Dict, Optional
import hashlib

class ResponseOptimizer:
    def __init__(self, cache_file=os.path.join("userdata", "response_cache.json")):
        self.cache_file = cache_file
        self.cache = {}
        self.thoughtful_mode = False
        self.load_cache()
    
    def load_cache(self):
        """Load response cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"⚡ Response Cache: Loaded {len(self.cache)} cached responses")
                self.scrub_dynamic_cache()
        except Exception as e:
            print(f"⚠️ Cache load error: {e}")
    
    def save_cache(self):
        """Save response cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Cache save error: {e}")
    
    def get_cache_key(self, user_input: str) -> str:
        """Generate cache key from user input"""
        # Normalize and hash input
        normalized = user_input.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get_cached_response(self, user_input: str) -> Optional[str]:
        """Get cached response if available"""
        # SKIP if dynamic
        if self.is_dynamic(user_input):
            return None
            
        cache_key = self.get_cache_key(user_input)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            cached['hits'] = cached.get('hits', 0) + 1
            # Don't save immediately - batch saves for performance
            print(f"⚡ Cache HIT: Instant response (hits: {cached['hits']})")
            return cached['response']
        return None
    
    def is_dynamic(self, user_input: str) -> bool:
        """Check if the query is dynamic and should NOT be cached"""
        dynamic_keywords = ['time', 'date', 'weather', 'clock', 'news', 'today', 'now', 'temperature']
        query = user_input.lower()
        return any(keyword in query for keyword in dynamic_keywords)

    def scrub_dynamic_cache(self):
        """Remove dynamic queries from the cache file"""
        dynamic_keywords = ['time', 'date', 'weather', 'clock', 'news', 'today', 'now', 'temperature']
        to_remove = []
        for key, entry in self.cache.items():
            if any(keyword in entry['input'].lower() for keyword in dynamic_keywords):
                to_remove.append(key)
        
        if to_remove:
            print(f" Scrubbing {len(to_remove)} dynamic entries from cache...")
            for key in to_remove:
                del self.cache[key]
            self.save_cache()

    def cache_response(self, user_input: str, response: str, save_immediately: bool = False):
        """Cache a response for future use"""
        # SKIP caching if input is dynamic (time, date, etc.)
        if self.is_dynamic(user_input):
            return

        cache_key = self.get_cache_key(user_input)
        self.cache[cache_key] = {
            'input': user_input,
            'response': response,
            'hits': 0,
            'cached_at': time.time()
        }
        
        # Limit cache size
        if len(self.cache) > 100:
            # Remove least used entries
            sorted_cache = sorted(self.cache.items(), 
                                key=lambda x: x[1].get('hits', 0))
            self.cache = dict(sorted_cache[-100:])
        
        # Only save if explicitly requested (for shutdown/critical moments)
        if save_immediately:
            self.save_cache()
    
    def enable_thoughtful_mode(self, enabled: bool = True):
        """Enable/disable thoughtful reasoning mode"""
        self.thoughtful_mode = enabled
        mode = "THOUGHTFUL" if enabled else "FAST"
        print(f" Response Mode: {mode}")
    
    def add_thinking_delay(self, complexity: str = "medium"):
        """Add artificial delay for thoughtful responses"""
        if not self.thoughtful_mode:
            return
        
        delays = {
            "simple": 0.5,
            "medium": 1.0,
            "complex": 2.0
        }
        
        delay = delays.get(complexity, 1.0)
        # print(f" Thinking deeply... ({delay}s)")
        # time.sleep(delay) - REMOVED for speed as requested
    
    def preprocess_input(self, user_input: str) -> str:
        """Voice-aware preprocessing: strips STT artifacts, fillers, and echo duplicates."""
        if not user_input:
            return ""

        processed = user_input

        # 1. Convert spoken punctuation to actual punctuation
        spoken_punctuation = {
            ' comma ': ', ', ' period ': '. ', ' full stop ': '. ',
            ' question mark ': '? ', ' exclamation mark ': '! ',
            ' colon ': ': ', ' semicolon ': '; ',
            ' new line ': '\n', ' newline ': '\n',
        }
        proc_lower = processed.lower()
        for spoken, actual in spoken_punctuation.items():
            if spoken in proc_lower:
                # Case-insensitive replace
                import re as _re
                processed = _re.sub(_re.escape(spoken), actual, processed, flags=_re.IGNORECASE)

        # 2. Remove filler words (voice artifacts from STT)
        filler_words = [
            'um', 'uh', 'uhh', 'umm', 'hmm', 'hm', 'er', 'ah',
            'like', 'you know', 'basically', 'literally', 'actually',
            'so like', 'i mean', 'kind of', 'sort of',
            'okay so', 'alright so', 'well',
        ]
        for filler in filler_words:
            # Only remove when it's a standalone filler, not part of a real word
            import re as _re
            pattern = r'\b' + _re.escape(filler) + r'\b'
            processed = _re.sub(pattern, '', processed, flags=_re.IGNORECASE)

        # 3. Remove duplicate adjacent words (echo/stutter from STT)
        # e.g., "play play music" → "play music"
        words = processed.split()
        deduped = [words[0]] if words else []
        for i in range(1, len(words)):
            if words[i].lower() != words[i-1].lower():
                deduped.append(words[i])
        processed = ' '.join(deduped)

        # 4. Clean up extra whitespace
        processed = ' '.join(processed.split())

        return processed.strip()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_hits = sum(entry.get('hits', 0) for entry in self.cache.values())
        return {
            'cached_responses': len(self.cache),
            'total_hits': total_hits,
            'mode': 'thoughtful' if self.thoughtful_mode else 'fast'
        }
