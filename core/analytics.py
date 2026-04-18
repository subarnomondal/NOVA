"""
Analytics Engine for NOVA
Aggregates data from user profile, history, and system stats for the dashboard.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

class AnalyticsEngine:
    def __init__(self, profile_file=os.path.join("userdata", "user_profile.json"), history_file=os.path.join("userdata", "conversation_history.json")):
        self.profile_file = profile_file
        self.history_file = history_file
    
    def _load_json(self, filepath) -> dict:
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
        return {}

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get aggregated data for the dashboard"""
        profile = self._load_json(self.profile_file)
        history = self._load_json(self.history_file)
        
        return {
            "overview": self._get_overview_stats(profile),
            "command_usage": self._get_command_usage(profile),
            "sentiment_trend": self._get_sentiment_trend(history),
            "daily_activity": self._get_daily_activity(history)
        }
    
    def _get_overview_stats(self, profile: dict) -> dict:
        stats = profile.get('interaction_stats', {})
        return {
            "total_interactions": stats.get('total_interactions', 0),
            "user_name": profile.get('name', 'User'),
            "voice_model": profile.get('preferences', {}).get('voice', 'Standard')
        }
    
    def _get_command_usage(self, profile: dict) -> dict:
        """Return top 5 used commands"""
        commands = profile.get('habits', {}).get('common_commands', {})
        # Sort by count desc
        sorted_cmds = sorted(commands.items(), key=lambda x: x[1], reverse=True)[:5]
        return dict(sorted_cmds)
    
    def _get_sentiment_trend(self, history: dict) -> dict:
        """Analyze sentiment over the last 10 conversations (simulated for now)"""
        # In a real scenario, we'd store sentiment per conversation. 
        # For now, we will return mock data structure for the UI to consume 
        # based on conversation timestamps if available, or just generic trend.
        
        # Real implementation would require parsing history items
        return {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "data": [0.2, 0.4, 0.5, 0.3, 0.8] # 0.0 to 1.0 scale
        }

    def _get_daily_activity(self, history: dict) -> dict:
        """Count interactions per day"""
        # Simplified for MVP
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "today": 12, # Placeholder, would calculate from history timestamps
            "average": 15
        }
