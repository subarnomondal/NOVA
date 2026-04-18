"""
User Profile System for NOVA
Stores and manages user preferences, habits, and personalization data
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class UserProfile:
    def __init__(self, profile_file=os.path.join("userdata", "user_profile.json")):
        self.profile_file = profile_file
        self.profile = {}
        self.load_profile()
        self.initialize_default_profile()
    
    def load_profile(self):
        """Load user profile from file"""
        try:
            if os.path.exists(self.profile_file):
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    self.profile = json.load(f)
                print(f"👤 User Profile: Loaded profile for {self.profile.get('name', 'User')}")
        except Exception as e:
            print(f"⚠️ Profile load error: {e}")
    
    def save_profile(self):
        """Save user profile to file"""
        try:
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Profile save error: {e}")
    
    def initialize_default_profile(self):
        """Initialize with default profile structure"""
        if not self.profile:
            self.profile = {
                "name": "User",
                "role": "user", # Default role
                "preferences": {
                    "language": "en",
                    "voice": "en-IE-EmilyNeural",  # Super cute native English! 💕
                    "timezone": "Asia/Kolkata"
                },
                "habits": {
                    "common_commands": {},
                    "frequent_contacts": [],
                    "favorite_topics": []
                },
                "personal_info": {
                    "location": "",
                    "occupation": "",
                    "interests": []
                },
                "routine": {
                    "wake_up": 8.0,  # 8:00 AM
                    "sleep": 22.0,   # 10:00 PM
                    "midday_break": 13.0, # 1:00 PM
                    "evening_start": 18.0  # 6:00 PM
                },
                "interaction_stats": {
                    "total_interactions": 0,
                    "first_interaction": datetime.now().isoformat(),
                    "last_interaction": datetime.now().isoformat()
                }
            }
            self.save_profile()

    def is_admin(self) -> bool:
        """Check if current user has admin privileges"""
        # Hardcoded superuser override for safety
        if self.get_name().upper() == "RIVU":
            if self.profile.get('role') != 'admin':
                self.profile['role'] = 'admin'
                self.save_profile()
            return True
        return self.profile.get('role') == 'admin'

    
    def update_name(self, name: str):
        """Update user's name"""
        self.profile['name'] = name
        self.save_profile()
        print(f"✅ Updated name to: {name}")
    
    def update_preference(self, key: str, value: str):
        """Update a user preference"""
        self.profile['preferences'][key] = value
        self.save_profile()
        print(f"✅ Updated preference: {key} = {value}")
    
    def add_personal_info(self, key: str, value: str):
        """Add personal information"""
        self.profile['personal_info'][key] = value
        self.save_profile()
        print(f"✅ Added personal info: {key}")

    def update_personal_info(self, key: str, value: str):
        """Update personal information (Alias for add_personal_info)"""
        self.add_personal_info(key, value)
    
    def track_command_usage(self, command: str):
        """Track frequently used commands"""
        habits = self.profile['habits']
        if command not in habits['common_commands']:
            habits['common_commands'][command] = 0
        habits['common_commands'][command] += 1
        self.save_profile()
    
    def add_frequent_contact(self, contact: str):
        """Add a frequently contacted person"""
        if contact not in self.profile['habits']['frequent_contacts']:
            self.profile['habits']['frequent_contacts'].append(contact)
            self.save_profile()
    
    def add_interest(self, topic: str):
        """Add user interest/topic"""
        if topic not in self.profile['personal_info']['interests']:
            self.profile['personal_info']['interests'].append(topic)
            self.save_profile()
    
    def update_interaction_stats(self):
        """Update interaction statistics"""
        stats = self.profile['interaction_stats']
        stats['total_interactions'] += 1
        stats['last_interaction'] = datetime.now().isoformat()
        self.save_profile()
    
    def get_name(self) -> str:
        """Get user's name"""
        return self.profile.get('name', 'User')
    
    def get_preference(self, key: str, default=None):
        """Get a user preference"""
        return self.profile['preferences'].get(key, default)
    
    def get_common_commands(self) -> Dict:
        """Get most common commands"""
        commands = self.profile['habits']['common_commands']
        # Sort by frequency
        return dict(sorted(commands.items(), key=lambda x: x[1], reverse=True))
    
    def get_interests(self) -> List[str]:
        """Get user interests"""
        return self.profile['personal_info'].get('interests', [])
    
    def get_profile_summary(self) -> str:
        """Get a summary of the user profile"""
        name = self.get_name()
        interactions = self.profile['interaction_stats']['total_interactions']
        interests = ', '.join(self.get_interests()[:3]) if self.get_interests() else 'None yet'
        
        return f"User: {name}, Interactions: {interactions}, Interests: {interests}"
    
    def get_personalization_context(self) -> str:
        """Get context string for personalizing responses"""
        context_parts = []
        
        name = self.get_name()
        if name != "User":
            context_parts.append(f"User's name is {name}")
        
        interests = self.get_interests()
        if interests:
            context_parts.append(f"Interested in: {', '.join(interests[:3])}")
        
        location = self.profile['personal_info'].get('location')
        if location:
            context_parts.append(f"Location: {location}")

        gender = self.profile['personal_info'].get('gender')
        if gender:
            context_parts.append(f"Gender: {gender}")
        
        if context_parts:
            return "User context: " + ". ".join(context_parts)
        return ""

    def set_gender(self, gender: str):
        """Set user's gender"""
        self.profile['personal_info']['gender'] = gender
        self.save_profile()
        print(f"✅ User gender set to: {gender}")

    def get_profile_data(self) -> Dict:
        """Get the entire profile dictionary"""
        return self.profile or {}
