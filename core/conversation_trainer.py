"""
Conversation Trainer for NOVA
Advanced system for teaching Nova new conversational patterns, responses, and behaviors
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

class ConversationTrainer:
    def __init__(self, training_file="conversation_training.json"):
        self.training_file = training_file
        self.trained_patterns = {}
        self.conversation_examples = []
        self.response_templates = {}
        self.contextual_responses = {}
        self.load_training_data()
    
    def load_training_data(self):
        """Load previously trained patterns and examples"""
        try:
            if os.path.exists(self.training_file):
                with open(self.training_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.trained_patterns = data.get('patterns', {})
                    self.conversation_examples = data.get('examples', [])
                    self.response_templates = data.get('templates', {})
                    self.contextual_responses = data.get('contextual', {})
                print(f"🎓 Conversation Trainer: Loaded {len(self.trained_patterns)} patterns, {len(self.conversation_examples)} examples")
        except Exception as e:
            print(f"⚠️ Training data load error: {e}")
    
    def save_training_data(self):
        """Save training data to file"""
        try:
            with open(self.training_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'patterns': self.trained_patterns,
                    'examples': self.conversation_examples,
                    'templates': self.response_templates,
                    'contextual': self.contextual_responses,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            print("💾 Training data saved successfully")
        except Exception as e:
            print(f"⚠️ Training data save error: {e}")
    
    def teach_response(self, trigger: str, response: str, category: str = "general", mood: str = "neutral") -> bool:
        """
        Teach Nova a new response pattern
        
        Args:
            trigger: The user input that should trigger this response
            response: Nova's response
            category: Category of the response (greeting, fact, emotion, etc.)
            mood: The mood associated with this response
        """
        trigger_normalized = trigger.lower().strip()
        
        if category not in self.trained_patterns:
            self.trained_patterns[category] = {}
        
        self.trained_patterns[category][trigger_normalized] = {
            'response': response,
            'mood': mood,
            'trained_at': datetime.now().isoformat(),
            'usage_count': 0,
            'variations': []
        }
        
        self.save_training_data()
        print(f"✅ Taught new response: '{trigger}' → '{response[:50]}...' (Mood: {mood})")
        return True
    
    def teach_conversation_flow(self, user_input: str, nova_response: str, 
                                context: Optional[str] = None) -> bool:
        """
        Teach Nova a complete conversation example with context
        
        Args:
            user_input: What the user said
            nova_response: How Nova should respond
            context: Optional context (previous conversation, mood, etc.)
        """
        example = {
            'user_input': user_input,
            'nova_response': nova_response,
            'context': context,
            'trained_at': datetime.now().isoformat(),
            'quality_score': None
        }
        
        self.conversation_examples.append(example)
        
        # Keep only last 200 examples to avoid bloat
        if len(self.conversation_examples) > 200:
            self.conversation_examples = self.conversation_examples[-200:]
        
        self.save_training_data()
        print(f"✅ Learned conversation pattern")
        return True
    
    def add_response_variation(self, trigger: str, variation: str, category: str = "general") -> bool:
        """Add a variation to an existing response pattern"""
        trigger_normalized = trigger.lower().strip()
        
        if category in self.trained_patterns and trigger_normalized in self.trained_patterns[category]:
            if 'variations' not in self.trained_patterns[category][trigger_normalized]:
                self.trained_patterns[category][trigger_normalized]['variations'] = []
            
            self.trained_patterns[category][trigger_normalized]['variations'].append(variation)
            self.save_training_data()
            print(f"✅ Added variation to '{trigger}'")
            return True
        
        return False
    
    def get_trained_response(self, user_input: str, context: Optional[Dict] = None) -> Optional[str]:
        """
        Get a trained response for user input
        
        Args:
            user_input: The user's message
            context: Optional context (recent conversation, mood, etc.)
        
        Returns:
            Trained response if found, None otherwise
        """
        user_input_normalized = user_input.lower().strip()
        
        # 1. Check exact matches first
        for category, patterns in self.trained_patterns.items():
            if user_input_normalized in patterns:
                pattern_data = patterns[user_input_normalized]
                pattern_data['usage_count'] = pattern_data.get('usage_count', 0) + 1
                
                # Return variation if available, otherwise main response
                if pattern_data.get('variations'):
                    import random
                    return random.choice([pattern_data['response']] + pattern_data['variations'])
                
                return pattern_data['response']
        
        # 2. Check fuzzy matches (similar inputs)
        best_match = None
        best_score = 0.0
        
        for category, patterns in self.trained_patterns.items():
            for trigger, data in patterns.items():
                similarity = self._calculate_similarity(user_input_normalized, trigger)
                if similarity > 0.85 and similarity > best_score:  # 85% similarity threshold
                    best_score = similarity
                    best_match = data
        
        if best_match:
            best_match['usage_count'] = best_match.get('usage_count', 0) + 1
            if best_match.get('variations'):
                import random
                return random.choice([best_match['response']] + best_match['variations'])
            return best_match['response']
        
        # 3. Check contextual responses
        if context:
            contextual_response = self._get_contextual_response(user_input_normalized, context)
            if contextual_response:
                return contextual_response
        
        return None
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _get_contextual_response(self, user_input: str, context: Dict) -> Optional[str]:
        """Get response based on context (mood, recent topics, etc.)"""
        # Check if we have contextual patterns
        for ctx_key, responses in self.contextual_responses.items():
            if ctx_key in str(context):
                for trigger, response in responses.items():
                    if trigger in user_input:
                        return response
        return None
    
    def teach_template(self, template_name: str, template: str, variables: List[str]) -> bool:
        """
        Teach Nova a response template with variables
        
        Args:
            template_name: Name of the template
            template: Template string with {variable} placeholders
            variables: List of variable names used in template
        
        Example:
            teach_template("weather_response", 
                          "The weather is {weather}. {advice}", 
                          ["weather", "advice"])
        """
        self.response_templates[template_name] = {
            'template': template,
            'variables': variables,
            'created_at': datetime.now().isoformat()
        }
        
        self.save_training_data()
        print(f"✅ Taught template: {template_name}")
        return True
    
    def use_template(self, template_name: str, **kwargs) -> Optional[str]:
        """Use a template to generate a response"""
        if template_name not in self.response_templates:
            return None
        
        template_data = self.response_templates[template_name]
        template = template_data['template']
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"⚠️ Missing variable for template: {e}")
            return None
    
    def analyze_conversation_quality(self, user_input: str, nova_response: str) -> Dict:
        """
        Analyze the quality of a conversation turn
        
        Returns metrics like:
        - Response length appropriateness
        - Emotional engagement
        - Personality consistency
        - Natural language flow
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'nova_response': nova_response,
            'metrics': {}
        }
        
        # 1. Length appropriateness
        user_len = len(user_input.split())
        nova_len = len(nova_response.split())
        
        if user_len < 5:  # Short query
            ideal_len = (10, 30)
        else:  # Longer query
            ideal_len = (20, 60)
        
        length_score = 1.0 if ideal_len[0] <= nova_len <= ideal_len[1] else 0.5
        analysis['metrics']['length_score'] = length_score
        
        # 2. Emotional engagement (check for actions, emojis, personality markers)
        emotion_markers = ['*', '(', ')', '!', '?', '...', '~', '♡', '✨', '💖']
        has_emotion = any(marker in nova_response for marker in emotion_markers)
        analysis['metrics']['emotional_engagement'] = 1.0 if has_emotion else 0.3
        
        # 3. Personality consistency (check for Nova-specific traits)
        nova_markers = [
            '<thought>', 'actually', 'honestly', 'let me think', 
            'right', 'look', 'hey', 'anyway', 'to be honest'
        ]
        has_personality = any(marker.lower() in nova_response.lower() for marker in nova_markers)
        analysis['metrics']['personality_consistency'] = 1.0 if has_personality else 0.5
        
        # 4. Natural flow (avoid robotic phrases)
        robotic_phrases = [
            'as an ai', 'i am an ai', 'i cannot', 'i am not able',
            'my purpose is', 'i was created', 'i do not have feelings'
        ]
        is_natural = not any(phrase in nova_response.lower() for phrase in robotic_phrases)
        analysis['metrics']['natural_flow'] = 1.0 if is_natural else 0.0
        
        # Overall quality score
        metrics = analysis['metrics']
        overall = (
            metrics['length_score'] * 0.2 +
            metrics['emotional_engagement'] * 0.3 +
            metrics['personality_consistency'] * 0.3 +
            metrics['natural_flow'] * 0.2
        )
        analysis['overall_quality'] = {
            'score': overall
        }
        
        return analysis
    
    def get_training_suggestions(self, recent_conversations: List[Dict]) -> List[str]:
        """
        Analyze recent conversations and suggest training improvements
        
        Args:
            recent_conversations: List of recent conversation turns
        
        Returns:
            List of training suggestions
        """
        suggestions = []
        
        if not recent_conversations:
            return ["No recent conversations to analyze"]
        
        # Analyze quality of recent responses
        low_quality_count = 0
        missing_emotion_count = 0
        missing_personality_count = 0
        
        for conv in recent_conversations[-10:]:  # Last 10 conversations
            if 'user' in conv and 'nova' in conv:
                quality = self.analyze_conversation_quality(conv['user'], conv['nova'])
                
                overall_score = quality['overall_quality']['score'] if isinstance(quality['overall_quality'], dict) else quality['overall_quality']
                if overall_score < 0.6:
                    low_quality_count += 1
                
                if quality['metrics']['emotional_engagement'] < 0.5:
                    missing_emotion_count += 1
                
                if quality['metrics']['personality_consistency'] < 0.5:
                    missing_personality_count += 1
        
        # Generate suggestions
        if low_quality_count > 3:
            suggestions.append("⚠️ Multiple low-quality responses detected. Consider training more natural conversation patterns.")
        
        if missing_emotion_count > 5:
            suggestions.append("💭 Responses lack emotional engagement. Train more expressive responses with actions and emotions.")
        
        if missing_personality_count > 5:
            suggestions.append("🎭 Personality consistency is low. Reinforce Nova's character traits (smart, witty, direct) in responses.")
        
        # Check for repetitive responses
        response_texts = [conv.get('nova', '') for conv in recent_conversations[-10:]]
        unique_responses = len(set(response_texts))
        if unique_responses < len(response_texts) * 0.7:
            suggestions.append("🔄 Detected repetitive responses. Add more response variations.")
        
        if not suggestions:
            suggestions.append("✅ Conversation quality looks good! Keep up the great work!")
        
        return suggestions
    
    def get_total_examples(self) -> int:
        """Get total number of conversation examples"""
        return len(self.conversation_examples)

    def export_training_summary(self) -> Dict:
        """Export a summary of all training data"""
        return {
            'total_patterns': sum(len(patterns) for patterns in self.trained_patterns.values()),
            'total_examples': len(self.conversation_examples),
            'total_templates': len(self.response_templates),
            'categories': list(self.trained_patterns.keys()),
            'most_used_patterns': self._get_most_used_patterns(5),
            'training_file': self.training_file
        }
    
    def _get_most_used_patterns(self, limit: int = 5) -> List[Dict]:
        """Get the most frequently used trained patterns"""
        all_patterns = []
        
        for category, patterns in self.trained_patterns.items():
            for trigger, data in patterns.items():
                all_patterns.append({
                    'trigger': trigger,
                    'category': category,
                    'usage_count': data.get('usage_count', 0),
                    'response': data['response'][:50] + '...' if len(data['response']) > 50 else data['response']
                })
        
        # Sort by usage count
        all_patterns.sort(key=lambda x: x['usage_count'], reverse=True)
        return all_patterns[:limit]
    
    def clear_training_data(self, category: Optional[str] = None) -> bool:
        """Clear training data (optionally for a specific category)"""
        if category:
            if category in self.trained_patterns:
                del self.trained_patterns[category]
                self.save_training_data()
                print(f"🗑️ Cleared training data for category: {category}")
                return True
            return False
        else:
            self.trained_patterns = {}
            self.conversation_examples = []
            self.response_templates = {}
            self.contextual_responses = {}
            self.save_training_data()
            print("🗑️ Cleared all training data")
            return True
