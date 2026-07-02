"""
NLU (Natural Language Understanding) Processor for NOVA
Modern LLM-first architecture: The LLM handles intent recognition, 
entity extraction, and semantic understanding. Rule-based logic is 
only used as a lightweight fallback for system-critical commands.
"""

import re
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime


class NLUProcessor:
    def __init__(self):
        # Dialogue state tracking
        self.dialogue_state = {
            'last_intent': None,
            'last_entities': {},
            'context_stack': [],
            'conversation_topic': None,
            'user_sentiment': 'neutral'
        }

        # --- LIGHTWEIGHT SYSTEM COMMAND MAP ---
        # Only hardcode intents that MUST execute instantly without LLM latency.
        # Everything else goes through the LLM reasoning loop in assistant.py.
        self.system_commands = {
            'time':     ['what time', 'current time', 'tell me the time'],
            'date':     ['what date', "what's the date", 'what day'],
            'stop':     ['stop', 'pause', 'shut up', 'silence', 'quiet'],
            'shutdown': ['shutdown', 'turn off', 'power off'],
            'restart':  ['restart', 'reboot'],
            'lock':     ['lock screen', 'lock pc'],
            'sleep':    ['sleep mode', 'go to sleep'],
            'abort':    ['abort', 'cancel', "don't shutdown", 'stop shutdown'],
        }

        # Command mappings for dispatcher (system commands only)
        self.intent_to_command = {
            'time': 'time',
            'date': 'date',
            'stop': 'stop',
            'shutdown': 'shutdown',
            'restart': 'restart',
            'lock': 'lock',
            'sleep': 'sleep',
            'abort': 'abort',
        }

        # Social intents (detected locally for fast-path routing in assistant.py)
        self.social_patterns = {
            'greeting':   ['hello', 'hi', 'hey', 'sup', 'yo', 'howdy', "what's up", 'namaste'],
            'thanks':     ['thank', 'thanks', 'thx', 'appreciate'],
            'how_are_you':['how are you', 'hru', 'hows it going', 'you good'],
            'bored':      ['bored', 'nothing to do', 'entertain me'],
            'affection':  ['love you', 'like you', 'i love u'],
            'identity':   ['who are you', 'your name', 'what are you'],
            'compliment':  ['you are great', 'you are amazing', 'good job'],
            'miss_you':   ['missed you', 'long time no see', 'where have you been'],
        }

    def normalize_text(self, text: str, language: str = "en") -> str:
        """
        Minimal text normalization. Unlike the old system, we do NOT
        translate slang or rewrite the user's words. The LLM understands
        slang, Hinglish, Gen-Z speak, and typos natively.
        """
        if not text:
            return ""

        # Remove extra whitespace
        normalized = ' '.join(text.split())

        # Capitalize first letter
        if normalized:
            normalized = normalized[0].upper() + normalized[1:]

        return normalized.strip()

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract structured entities from text (phone numbers, URLs, etc.)"""
        entities: Dict[str, Any] = {}

        # Extract phone numbers
        phone_pattern = r'\+?\d[\d\s-]{7,15}'
        phones = re.findall(phone_pattern, text)
        if phones:
            entities['phone_numbers'] = phones

        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        if urls:
            entities['urls'] = urls

        # Extract numbers
        number_pattern = r'\b\d+\b'
        numbers = re.findall(number_pattern, text)
        if numbers:
            entities['numbers'] = [int(n) for n in numbers]

        # Extract time expressions
        time_pattern = r'\b\d{1,2}:\d{2}\b|\b\d{1,2}\s*(am|pm)\b'
        times = re.findall(time_pattern, text.lower())
        if times:
            entities['times'] = times

        # Extract quoted text (for messages, etc.)
        quoted_pattern = r'["\'](.+?)["\']'
        quoted = re.findall(quoted_pattern, text)
        if quoted:
            entities['quoted_text'] = quoted

        # Extract message content after "saying" or "message" (unquoted)
        if not quoted:
            msg_match = re.search(r'(?:saying|message|say|tell him|tell her|tell them) (.+)', text, re.IGNORECASE)
            if msg_match:
                entities['message_content'] = msg_match.group(1).strip()

        # Extract potential contact names
        contact_match = re.search(r'(?:message|whatsapp|to) ([\w\s]+?)(?: saying| say|$)', text, re.IGNORECASE)
        if contact_match:
            entities['contact_name'] = contact_match.group(1).strip()

        return entities

    def recognize_intent(self, text: str) -> Tuple[Optional[str], float]:
        """
        Lightweight intent recognition for system-critical commands only.
        Everything else returns (None, 0.0) and gets handled by the LLM.
        """
        text_lower = text.lower().strip()

        # 1. Check system commands (must be instant, no LLM latency)
        for intent, keywords in self.system_commands.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    score = 0.95 if text_lower.startswith(keyword) else 0.85
                    return intent, score

        # 2. Check social patterns (for fast-path routing, not for skill dispatch)
        for intent, keywords in self.social_patterns.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    return intent, 0.8

        # 3. Everything else → Let the LLM handle it
        return None, 0.0

    def fuzzy_match_command(self, text: str, commands: List[str], threshold: float = 0.6) -> Optional[str]:
        """Find best matching command using fuzzy matching"""
        from difflib import SequenceMatcher
        text_lower = text.lower()
        best_match = None
        best_ratio = 0.0

        for command in commands:
            ratio = SequenceMatcher(None, text_lower, command.lower()).ratio()
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = command

        return best_match

    def process(self, text: str) -> Dict:
        """Process natural language input and return structured data"""
        entities = self.extract_entities(text)
        intent, confidence = self.recognize_intent(text)

        command = None
        if intent and intent in self.intent_to_command:
            command = self.intent_to_command[intent]

        return {
            'original_text': text,
            'intent': intent,
            'confidence': confidence,
            'command': command,
            'entities': entities,
            'processed': True
        }

    def enhance_command(self, text: str, nlp_result: Dict) -> str:
        """Pass through — the LLM handles enhancement"""
        return text

    def get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            'time': 'Checking the time',
            'date': 'Checking the date',
            'stop': 'Stopping current action',
            'shutdown': 'Shutting down system',
            'restart': 'Restarting system',
            'lock': 'Locking screen',
            'sleep': 'Entering sleep mode',
            'abort': 'Aborting action',
            'greeting': 'Greeting',
            'thanks': 'Expressing gratitude',
            'identity': 'Asking about identity',
        }
        return descriptions.get(intent, 'General conversation')

    # ===== NLU-Specific Features =====

    def analyze_sentiment(self, text: str) -> str:
        """Quick sentiment check for UI emotion triggers"""
        text_lower = text.lower()

        positive_words = ['happy', 'great', 'awesome', 'love', 'thanks', 'perfect',
                         'excellent', 'good', 'nice', 'wonderful', 'amazing', 'yay']
        negative_words = ['sad', 'angry', 'hate', 'terrible', 'bad', 'awful',
                         'horrible', 'annoyed', 'frustrated', 'upset', 'disappointed']

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        return 'neutral'

    def update_dialogue_state(self, nlp_result: Dict):
        """Update dialogue state with new information"""
        self.dialogue_state['last_intent'] = nlp_result.get('intent')
        self.dialogue_state['last_entities'] = nlp_result.get('entities', {})
        self.dialogue_state['user_sentiment'] = nlp_result.get('sentiment', 'neutral')

        # Update context stack (keep last 5 turns)
        self.dialogue_state['context_stack'].append({
            'timestamp': datetime.now().isoformat(),
            'intent': nlp_result.get('intent'),
            'entities': nlp_result.get('entities', {})
        })
        if len(self.dialogue_state['context_stack']) > 5:
            self.dialogue_state['context_stack'].pop(0)

        # Update conversation topic
        if nlp_result.get('intent') not in ['greeting', 'thanks', 'goodbye']:
            self.dialogue_state['conversation_topic'] = nlp_result.get('intent')

    def segment_intents(self, text: str) -> List[str]:
        """Split complex input into multiple sub-utterances"""
        segments = re.split(r'\b(?:and then|then)\b|[;]', text, flags=re.IGNORECASE)
        return [s.strip() for s in segments if len(s.strip()) > 3]

    def process_with_nlu(self, text: str, min_confidence: float = 0.5) -> List[Dict]:
        """
        Modern NLU pipeline. Only classifies system-critical and social intents locally.
        Everything else is delegated to the LLM reasoning loop.
        """
        # 1. Capture sentiment for UI emotion triggers
        global_sentiment = self.analyze_sentiment(text)
        
        try:
            from core.agi_context import agi_context
            agi_context.current_mood = global_sentiment
        except Exception:
            pass

        # 2. Segment multi-part commands
        raw_segments = self.segment_intents(text)
        if len(raw_segments) <= 1:
            raw_segments = [text]

        results = []
        for segment in raw_segments:
            entities = self.extract_entities(segment)
            intent, confidence = self.recognize_intent(segment)

            command = self.intent_to_command.get(intent) if intent else None

            res = {
                'original_text': segment,
                'intent': intent,
                'confidence': confidence,
                'command': command,
                'entities': entities,
                'sentiment': self.analyze_sentiment(segment),
                'processed': True,
                'timestamp': datetime.now().isoformat()
            }

            self.update_dialogue_state(res)
            results.append(res)

        return results
