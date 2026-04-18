
"""
Emotion Detector for Nova
Rule-based emotion detection inspired by GoEmotions dataset (27 emotions)
"""

import re
from typing import List, Dict, Tuple

class EmotionDetector:
    def __init__(self):
        # GoEmotions-inspired emotion categories with keyword patterns
        self.emotion_keywords = {
            # Positive emotions
            "joy": ["happy", "joyful", "glad", "cheerful", "delighted", "pleased", "yay", "woohoo"],
            "love": ["love", "adore", "cherish", "affection", "caring", "fond"],
            "admiration": ["admire", "respect", "impressed", "amazing", "wonderful", "brilliant"],
            "amusement": ["funny", "hilarious", "lol", "haha", "lmao", "rofl", "joke"],
            "excitement": ["excited", "thrilled", "pumped", "hyped", "can't wait"],
            "gratitude": ["thank", "thanks", "grateful", "appreciate", "thankful"],
            "optimism": ["hope", "hopeful", "optimistic", "positive", "bright future"],
            "pride": ["proud", "accomplished", "achievement", "success"],
            "relief": ["relief", "relieved", "phew", "finally", "glad it's over"],
            
            # Negative emotions
            "sadness": ["sad", "depressed", "down", "unhappy", "miserable", "crying", "tears"],
            "anger": ["furious", "rage", "pissed", "irritated", "outraged"],
            "fear": ["scared", "afraid", "terrified", "frightened", "worried", "anxious", "nervous"],
            "disgust": ["disgusting", "gross", "eww", "yuck", "nasty", "revolting"],
            "grief": ["grief", "mourning", "loss", "heartbroken", "devastated"],
            "disappointment": ["disappointed", "let down", "failed", "didn't work out"],
            "annoyance": ["annoying", "bothered", "irritating", "ugh", "frustrated"],
            "embarrassment": ["embarrassed", "ashamed", "awkward", "humiliated"],
            "nervousness": ["nervous", "jittery", "anxious", "uneasy", "tense"],
            "remorse": ["sorry", "regret", "guilt", "my fault", "shouldn't have"],
            
            # Ambiguous emotions
            "surprise": ["surprised", "shocked", "wow", "omg", "unexpected", "didn't expect"],
            "confusion": ["confused", "don't understand", "what", "huh", "puzzled"],
            "curiosity": ["curious", "wonder", "interested", "want to know"],
            "realization": ["realize", "understand now", "oh", "aha", "i see"],
            
            # Other
            "caring": ["care about", "concerned", "worried about you", "are you okay"],
            "desire": ["want", "wish", "desire", "crave", "need"],
            "approval": ["agree", "yes", "correct", "right", "exactly"],
            "disapproval": ["disagree", "no", "wrong", "incorrect", "don't think so"]
        }
        
        # Emotion intensity modifiers
        self.intensifiers = ["very", "really", "so", "extremely", "super", "incredibly"]
        self.diminishers = ["a bit", "slightly", "somewhat", "kind of", "sort of"]
        
    def detect_emotion(self, text: str, top_k: int = 3) -> List[Dict[str, any]]:
        """
        Detect emotions in text using keyword matching.
        
        Returns:
            List of dicts with 'emotion' and 'confidence' keys, sorted by confidence
        """
        text_lower = text.lower()
        
        # Score each emotion
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
                    
                    # Boost score if intensifier nearby
                    for intensifier in self.intensifiers:
                        if intensifier in text_lower and keyword in text_lower:
                            score += 0.5
            
            if score > 0:
                # Normalize score to confidence (0-1)
                confidence = min(score / 3.0, 1.0)  # Cap at 1.0
                emotion_scores[emotion] = {
                    "emotion": emotion,
                    "confidence": confidence,
                    "matched_keywords": matched_keywords
                }
        
        # Sort by confidence
        sorted_emotions = sorted(
            emotion_scores.values(),
            key=lambda x: x['confidence'],
            reverse=True
        )
        
        return sorted_emotions[:top_k] if sorted_emotions else [{"emotion": "neutral", "confidence": 1.0, "matched_keywords": []}]
    
    def get_primary_emotion(self, text: str) -> str:
        """Get the single most likely emotion."""
        emotions = self.detect_emotion(text, top_k=1)
        return emotions[0]['emotion'] if emotions else "neutral"
    
    def is_emotional(self, text: str, threshold: float = 0.3) -> bool:
        """Check if text contains significant emotional content."""
        emotions = self.detect_emotion(text, top_k=1)
        if not emotions or emotions[0]['emotion'] == 'neutral':
            return False
        return emotions[0]['confidence'] >= threshold
    
    def get_emotion_category(self, emotion: str) -> str:
        """Categorize emotion into positive/negative/ambiguous."""
        positive = ["joy", "love", "admiration", "amusement", "excitement", "gratitude", "optimism", "pride", "relief", "approval"]
        negative = ["sadness", "anger", "fear", "disgust", "grief", "disappointment", "annoyance", "embarrassment", "nervousness", "remorse", "disapproval"]
        ambiguous = ["surprise", "confusion", "curiosity", "realization", "caring", "desire"]
        
        if emotion in positive:
            return "positive"
        elif emotion in negative:
            return "negative"
        elif emotion in ambiguous:
            return "ambiguous"
        else:
            return "neutral"

# Global singleton
emotion_detector = EmotionDetector()

if __name__ == "__main__":
    # Test
    detector = EmotionDetector()
    
    test_cases = [
        "I'm so happy today!",
        "I'm really sad and depressed...",
        "This makes me so angry!",
        "I'm scared and worried about the exam",
        "Wow, that's surprising!",
        "Thank you so much, I really appreciate it!"
    ]
    
    print("🧪 Testing Emotion Detection:\n")
    for text in test_cases:
        emotions = detector.detect_emotion(text, top_k=2)
        primary = emotions[0]
        category = detector.get_emotion_category(primary['emotion'])
        
        print(f"Text: \"{text}\"")
        print(f"  Primary: {primary['emotion']} ({primary['confidence']:.2f}) [{category}]")
        if len(emotions) > 1:
            print(f"  Secondary: {emotions[1]['emotion']} ({emotions[1]['confidence']:.2f})")
        print()
