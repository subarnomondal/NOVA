"""
NLU (Natural Language Understanding) Processor for NOVA
Modern LLM-first architecture: The LLM handles intent recognition, 
entity extraction, and semantic understanding. Rule-based logic is 
only used as a lightweight fallback for system-critical commands.

Enhanced with voice-aware fuzzy matching and STT error correction.
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

        # --- VOICE MISRECOGNITION MAP ---
        # Common Whisper/STT mistakes → intended words
        # These are applied BEFORE intent matching for better accuracy
        self.voice_corrections = {
            # Nova-specific
            'no va': 'nova', 'no bar': 'nova', 'nover': 'nova',
            'no vah': 'nova', 'novar': 'nova',
            # System commands
            'look screen': 'lock screen', 'look my pc': 'lock pc',
            'log screen': 'lock screen', 'log my pc': 'lock pc',
            'shut down': 'shutdown', 'shot down': 'shutdown',
            'turned off': 'turn off', 'tone off': 'turn off',
            'power of': 'power off', 'powered off': 'power off',
            'restarted': 'restart', 'restart it': 'restart',
            're boot': 'reboot', 'reboot it': 'reboot',
            'asleep': 'sleep mode', 'go sleep': 'go to sleep',
            'top it': 'stop', 'pause it': 'pause',
            # Time/Date
            'what\'s the time': 'what time', 'what time is': 'what time',
            'what\'s the date': 'what date', 'what day is': 'what day',
            # Media/Music
            'play some music': 'play music', 'play a song': 'play music',
            'played music': 'play music', 'play me a song': 'play music',
            # Search
            'search for': 'search', 'look up': 'search',
            'looked up': 'search', 'find me': 'search',
            # Weather
            'whether': 'weather', 'whether today': 'weather',
            'whether report': 'weather',
            # WhatsApp
            'what\'s app': 'whatsapp', 'what app': 'whatsapp',
            'watts app': 'whatsapp', 'watsapp': 'whatsapp',
            # Volume
            'volume of': 'volume up', 'volume off': 'mute',
            'turn it up': 'volume up', 'turn it down': 'volume down',
            # Screenshot
            'screen shot': 'screenshot', 'screen short': 'screenshot',
            'take screen': 'screenshot', 'take a screen shot': 'screenshot',
        }

        # --- LIGHTWEIGHT SYSTEM COMMAND MAP ---
        # Only hardcode intents that MUST execute instantly without LLM latency.
        # Everything else goes through the LLM reasoning loop in assistant.py.
        self.system_commands = {
            'time':     ['what time', 'current time', 'tell me the time', 'time please',
                         'what is the time', 'time right now', 'clock'],
            'date':     ['what date', "what's the date", 'what day', 'today date',
                         'what is the date', 'what day is it', 'current date'],
            'stop':     ['stop', 'pause', 'shut up', 'silence', 'quiet',
                         'be quiet', 'stop talking', 'enough', 'stop it', 'hush'],
            'shutdown': ['shutdown', 'turn off', 'power off', 'shut down',
                         'switch off', 'turn off the computer', 'power down'],
            'restart':  ['restart', 'reboot', 'restart the computer',
                         'restart my pc', 'reboot system'],
            'lock':     ['lock screen', 'lock pc', 'lock my pc', 'lock computer',
                         'lock the screen', 'lock my computer', 'lock my screen'],
            'sleep':    ['sleep mode', 'go to sleep', 'put to sleep',
                         'hibernate', 'enter sleep', 'sleep my pc'],
            'abort':    ['abort', 'cancel', "don't shutdown", 'stop shutdown',
                         'cancel shutdown', 'abort shutdown', 'never mind',
                         "don't restart", 'cancel restart'],
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
            'greeting': 'hello',
            'thanks': 'thanks',
            'how_are_you': 'how are you',
            'bored': 'bored',
            'affection': 'love you',
            'identity': 'introduce yourself',
            'compliment': 'you are',
            'miss_you': 'missed you',
        }

        # Social intents (detected locally for fast-path routing in assistant.py)
        self.social_patterns = {
            'greeting':   ['hello', 'hi', 'hey', 'sup', 'yo', 'howdy', "what's up",
                           'namaste', 'hlo', 'heya', 'hiya', 'greetings', 'good morning',
                           'good afternoon', 'good evening', 'morning', 'evening'],
            'thanks':     ['thank', 'thanks', 'thx', 'appreciate', 'thank you',
                           'thankyou', 'ty', 'thanks a lot', 'much appreciated'],
            'how_are_you':['how are you', 'hru', 'hows it going', 'you good',
                           'how you doing', 'how do you do', 'wassup', 'you okay',
                           'how is it going', "how's everything"],
            'bored':      ['bored', 'nothing to do', 'entertain me', "i'm bored",
                           'so bored', 'boring', 'tell me something fun'],
            'affection':  ['love you', 'like you', 'i love u', 'luv you', 'ily',
                           'i adore you', 'you are the best', 'love u'],
            'identity':   ['who are you', 'your name', 'what are you', 'introduce yourself',
                           'tell me about yourself', "what's your name", 'who is this',
                           'who am i talking to'],
            'compliment':  ['you are great', 'you are amazing', 'good job', 'well done',
                            'nice work', 'you rock', 'brilliant', 'you are smart',
                            'awesome job', 'impressive'],
            'miss_you':   ['missed you', 'long time no see', 'where have you been',
                           'i missed you', 'miss you', 'where were you'],
        }

        # Build flattened keyword lists for fuzzy matching
        self._all_system_keywords = []
        for intent, keywords in self.system_commands.items():
            for kw in keywords:
                self._all_system_keywords.append(kw)

    def _apply_voice_corrections(self, text: str) -> str:
        """Apply voice misrecognition corrections before intent matching."""
        text_lower = text.lower()
        for wrong, correct in self.voice_corrections.items():
            # Use word-boundary matching to avoid partial replacements
            pattern = r'\b' + re.escape(wrong) + r'\b'
            text_lower = re.sub(pattern, correct, text_lower)
        return text_lower

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
        Enhanced intent recognition with voice-aware fuzzy matching.
        1. Apply voice misrecognition corrections
        2. Exact keyword matching for system commands
        3. Fuzzy matching fallback for near-misses from STT errors
        4. Social pattern matching
        """
        # Step 0: Apply voice corrections to fix common STT errors
        text_corrected = self._apply_voice_corrections(text)
        text_lower = text_corrected.strip()

        # 1. Check system commands (exact match — must be instant, no LLM latency)
        for intent, keywords in self.system_commands.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    score = 0.95 if text_lower.startswith(keyword) else 0.85
                    return intent, score

        # 2. Fuzzy matching fallback for STT errors (only for system commands)
        best_fuzzy_intent = None
        best_fuzzy_score = 0.0
        for intent, keywords in self.system_commands.items():
            match = self.fuzzy_match_command(text_lower, keywords, threshold=0.7)
            if match:
                from difflib import SequenceMatcher
                ratio = SequenceMatcher(None, text_lower, match.lower()).ratio()
                if ratio > best_fuzzy_score:
                    best_fuzzy_score = ratio
                    best_fuzzy_intent = intent

        if best_fuzzy_intent and best_fuzzy_score >= 0.7:
            return best_fuzzy_intent, round(best_fuzzy_score * 0.85, 2)  # Slightly lower confidence than exact

        # 3. Check social patterns (for fast-path routing, not for skill dispatch)
        for intent, keywords in self.social_patterns.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    return intent, 0.8

        # 4. Everything else → Let the LLM handle it
        return None, 0.0

    def fuzzy_match_command(self, text: str, commands: List[str], threshold: float = 0.6) -> Optional[str]:
        """Find best matching command using fuzzy matching"""
        from difflib import SequenceMatcher
        text_lower = text.lower()
        best_match = None
        best_ratio = 0.0

        for command in commands:
            # Check both full-text and substring matching
            ratio = SequenceMatcher(None, text_lower, command.lower()).ratio()
            
            # Also check if command appears as a substring with minor edits
            if len(command) > 3 and command.lower() in text_lower:
                ratio = max(ratio, 0.9)  # High confidence for substring match
            
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
        """Enhanced sentiment check with broader vocabulary including Hinglish/slang"""
        text_lower = text.lower()

        positive_words = [
            'happy', 'great', 'awesome', 'love', 'thanks', 'perfect',
            'excellent', 'good', 'nice', 'wonderful', 'amazing', 'yay',
            'fantastic', 'brilliant', 'superb', 'cool', 'lit', 'fire',
            'dope', 'sick', 'epic', 'beautiful', 'lovely', 'excited',
            'proud', 'grateful', 'blessed', 'wow', 'incredible',
            # Hinglish
            'mast', 'zabardast', 'badhiya', 'shandar', 'kamaal',
            'sahi', 'accha', 'bohot accha', 'maja', 'khushi'
        ]
        negative_words = [
            'sad', 'angry', 'hate', 'terrible', 'bad', 'awful',
            'horrible', 'annoyed', 'frustrated', 'upset', 'disappointed',
            'worst', 'pathetic', 'useless', 'boring', 'disgusting',
            'painful', 'miserable', 'depressed', 'anxious', 'stressed',
            'tired', 'exhausted', 'irritated', 'furious', 'rubbish',
            # Hinglish
            'bakwas', 'bekar', 'ganda', 'bura', 'dukhi',
            'gussa', 'pareshan', 'thak gaya', 'bore'
        ]

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
