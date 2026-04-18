"""
HITL (Human-In-The-Loop) System for NOVA
Allows NOVA to learn from user corrections and feedback
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional

class HITLSystem:
    def __init__(self, feedback_file=os.path.join("userdata", "hitl_feedback.json")):
        self.feedback_file = feedback_file
        self.feedback_data = []
        self.corrections = {}
        self.load_feedback()
    
    def load_feedback(self):
        """Load previous feedback and corrections"""
        try:
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.feedback_data = data.get('feedback', [])
                    self.corrections = data.get('corrections', {})
                print(f"🔄 HITL: Loaded {len(self.feedback_data)} feedback entries")
        except Exception as e:
            print(f"⚠️ HITL load error: {e}")
    
    def save_feedback(self):
        """Save feedback and corrections"""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'feedback': self.feedback_data,
                    'corrections': self.corrections
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ HITL save error: {e}")
    
    def record_interaction(self, user_input: str, nova_response: str, 
                          intent: str, confidence: float):
        """Record an interaction for potential feedback"""
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'nova_response': nova_response,
            'intent': intent,
            'confidence': confidence,
            'feedback': None,
            'correction': None
        }
        self.feedback_data.append(interaction)
        
        # Keep only last 100 interactions
        if len(self.feedback_data) > 100:
            self.feedback_data = self.feedback_data[-100:]
        
        self.save_feedback()
        return len(self.feedback_data) - 1  # Return index
    
    def add_user_correction(self, interaction_id: int, correction: str):
        """User provides correction for a response"""
        if 0 <= interaction_id < len(self.feedback_data):
            self.feedback_data[interaction_id]['correction'] = correction
            self.feedback_data[interaction_id]['feedback'] = 'corrected'
            
            # Store correction pattern
            original = self.feedback_data[interaction_id]['user_input']
            self.corrections[original.lower()] = correction
            
            self.save_feedback()
            print(f"✅ HITL: Correction recorded")
            return True
        return False
    
    def add_feedback(self, interaction_id: int, feedback_type: str):
        """User provides feedback (positive/negative)"""
        if 0 <= interaction_id < len(self.feedback_data):
            self.feedback_data[interaction_id]['feedback'] = feedback_type
            self.save_feedback()
            print(f"✅ HITL: Feedback '{feedback_type}' recorded")
            return True
        return False
    
    def get_learned_correction(self, user_input: str) -> Optional[str]:
        """Check if we have a learned correction for this input"""
        return self.corrections.get(user_input.lower())
    
    def get_feedback_stats(self) -> Dict:
        """Get statistics about feedback"""
        positive = sum(1 for f in self.feedback_data if f.get('feedback') == 'positive')
        negative = sum(1 for f in self.feedback_data if f.get('feedback') == 'negative')
        corrected = sum(1 for f in self.feedback_data if f.get('feedback') == 'corrected')
        
        return {
            'total_interactions': len(self.feedback_data),
            'positive_feedback': positive,
            'negative_feedback': negative,
            'corrections': corrected,
            'learned_patterns': len(self.corrections)
        }
    
    def suggest_improvements(self) -> list:
        """Suggest improvements based on feedback"""
        suggestions = []
        
        # Find patterns in negative feedback
        negative_intents = {}
        for entry in self.feedback_data:
            if entry.get('feedback') == 'negative':
                intent = entry.get('intent')
                if intent:
                    negative_intents[intent] = negative_intents.get(intent, 0) + 1
        
        # Suggest retraining for intents with high negative feedback
        for intent, count in negative_intents.items():
            if count > 3:
                suggestions.append({
                    'type': 'intent_improvement',
                    'intent': intent,
                    'issue': f'High negative feedback ({count} times)',
                    'suggestion': f'Review and improve {intent} intent recognition'
                })
        
        return suggestions
