import json
import os
import time
from typing import Dict, List, Optional

class LTMManager:
    """
    Long-Term Memory (LTM) Manager with Fact Decay
    Handles persistent storage of user-related facts and preferences.
    Facts fade over time unless reinforced through conversation.
    """
    def __init__(self, memory_file=os.path.join("userdata", "user_facts.json"), decay_threshold_days=60):
        self.memory_file = memory_file
        self.decay_threshold_days = decay_threshold_days
        self.enabled = True # Added to fix desktop.py attribute error
        # Structure: { "category": { "value": "x", "last_seen": ts, "reinforcement": 5 } }
        self.facts = self._migrate_and_prune(self._load_memory())

    def _load_memory(self) -> Dict:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _migrate_and_prune(self, raw_data: Dict) -> Dict:
        """Prunes stale facts and converts old string-only data to metadata-backed data."""
        now = time.time()
        migrated = {}
        stale_threshold = self.decay_threshold_days * 86400
        
        for cat, data in raw_data.items():
            if isinstance(data, list):
                valid_items = []
                for item in data:
                    if isinstance(item, str):
                        item = {"value": item, "last_seen": now, "reinforcement": 1}
                    if (now - item.get("last_seen", 0)) < stale_threshold:
                        valid_items.append(item)
                if valid_items: migrated[cat] = valid_items
            else:
                if isinstance(data, str):
                    data = {"value": data, "last_seen": now, "reinforcement": 1}
                if (now - data.get("last_seen", 0)) < stale_threshold:
                    migrated[cat] = data
        return migrated

    def save_memory(self):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.facts, f, indent=2)

    def learn_fact(self, category: str, value: str):
        """Stores or reinforces a specific fact about the user."""
        category = category.lower().strip()
        value = value.strip()
        now = time.time()
        
        list_categories = ['interest', 'favorite', 'like', 'hobby', 'dislike']
        
        if category in list_categories:
            if category not in self.facts:
                self.facts[category] = []
            
            # Find existing or add new
            found = False
            for item in self.facts[category]:
                if item["value"].lower() == value.lower():
                    item["last_seen"] = now
                    item["reinforcement"] = item.get("reinforcement", 0) + 1
                    found = True
                    break
            
            if not found:
                self.facts[category].append({"value": value, "last_seen": now, "reinforcement": 1})
                print(f"✨ LTM: Added new {category}: {value}")
        else:
            # Single value update or reinforcement
            if category in self.facts and self.facts[category]["value"].lower() == value.lower():
                self.facts[category]["last_seen"] = now
                self.facts[category]["reinforcement"] = self.facts[category].get("reinforcement", 0) + 1
            else:
                self.facts[category] = {"value": value, "last_seen": now, "reinforcement": 1}
                print(f"✨ LTM: Learned that user's {category} is {value}")
            
        self.save_memory()

    def forget_fact(self, category: str):
        if category.lower() in self.facts:
            del self.facts[category.lower()]
            self.save_memory()

    def get_fact(self, category: str) -> Optional[str]:
        data = self.facts.get(category.lower())
        if not data: return None
        return data["value"] if isinstance(data, dict) else None

    def get_summary_for_prompt(self) -> str:
        """Returns a string summary of facts, prioritized by recency/reinforcement."""
        if not self.facts:
            return ""
        
        summary = "\nPERSISTENT USER FACTS & CORRECTIONS:\n"
        # Sort facts: Keep corrections at the top, followed by recent facts
        all_metadata = []
        corrections = []
        
        for cat, val in self.facts.items():
            if cat == "correction":
                if isinstance(val, list):
                    corrections.extend([(cat, item) for item in val])
                else:
                    corrections.append((cat, val))
            else:
                if isinstance(val, list):
                    for item in val:
                        all_metadata.append((cat, item))
                else:
                    all_metadata.append((cat, val))
        
        # Sort standard facts by last_seen desc
        all_metadata.sort(key=lambda x: x[1].get('last_seen', 0), reverse=True)
        
        # Always include latest 5 corrections if they exist
        corrections.sort(key=lambda x: x[1].get('last_seen', 0), reverse=True)
        final_list = corrections[:5] + all_metadata[:10]
        
        for cat, item in final_list:
            val = item['value']
            label = "CORRECTED FACT" if cat == "correction" else cat.capitalize()
            summary += f"- {label}: {val}\n"
        return summary

    def auto_extract_facts(self, user_input: str):
        """
        Extract facts from user input using regex patterns.
        """
        user_input = user_input.lower().strip()
        import re
        
        # Pattern 1: 'My [category] is [value]'
        match1 = re.search(r"my ([\w\s]+) is ([\w\s]+)", user_input)
        if match1:
            category, value = match1.groups()
            self._save_valid_fact(category, value)

        # Pattern 2: 'I (love|like|enjoy) [value]' -> category: 'interest'
        # Improved to catch multi-word values
        match2 = re.search(r"i (love|like|enjoy|am interested in) ([\w\s,]+)", user_input)
        if match2:
            interest = match2.group(2).strip()
            # Split by 'and' or commas if present
            interests = re.split(r",| and ", interest)
            for i in interests:
                if i.strip():
                    self.learn_fact("interest", i.strip())

        # Pattern 3: 'I (live|reside) in [value]' -> category: 'location'
        match3 = re.search(r"i (live|reside) in ([\w\s]+)", user_input)
        if match3:
            self.learn_fact("location", match3.group(2).strip())

        # Pattern 4: 'I (am|work as) a ([\w\s]+)' -> category: 'occupation'
        match4 = re.search(r"i (am|work as) a ([\w\s]+)", user_input)
        if match4:
             self.learn_fact("occupation", match4.group(2).strip())

        # Pattern 5: 'Call me [name]' -> category: 'nickname'
        match5 = re.search(r"call me ([\w\s]+)", user_input)
        if match5:
            self.learn_fact("nickname", match5.group(1).strip())
            
        # Pattern 6: 'I hate [value]' -> category: 'dislike'
        match6 = re.search(r"i (hate|dislike|don't like) ([\w\s]+)", user_input)
        if match6:
            self.learn_fact("dislike", match6.group(2).strip())

    def _save_valid_fact(self, category, value):
        """Filters and saves facts to avoid noise"""
        category = category.strip().lower()
        value = value.strip()
        
        # Blacklist common non-fact categories
        blacklist = ['name', 'command', 'problem', 'this', 'that', 'it', 'there', 'you']
        if category not in blacklist and len(value) > 1:
            self.learn_fact(category, value)
