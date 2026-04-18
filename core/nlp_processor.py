"""
NLU (Natural Language Understanding) Processor for NOVA
Handles natural language understanding, intent recognition, entity extraction,
semantic understanding, sentiment analysis, and dialogue management
"""

import re
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
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
        # Intent patterns with keywords
        self.intent_patterns = {
            # Priority Info intents
            'time': ['time', 'clock', 'hour', 'current time', 'tell me the time', 'what is the time', 'watch'],
            'date': ['date', 'day', 'today', 'current date', "what's the date", 'what day is it', 'calendar'],
            'weather': ['weather', 'temperature', 'forecast', 'rain', 'hot', 'cold', 'sunny', 'climate', 'outside'],
            'news': ['news', 'headlines', 'latest', 'updates', 'current events', 'happenings', 'report'],
            'natural_events': ['natural events', 'what\'s happening on earth', 'satellite gossip', 'news satellites', 'nasa news', 'eonet', 'earth events', 'wildfires', 'storms', 'volcanoes'],
            'earthquakes': ['earthquake', 'earthquakes', 'seismic', 'tremor', 'quakes', 'earth quuick', 'earth queck', 'earthquake alerts'],
            'vision': ['look at my screen', 'what am i doing', 'look screen', 'describe my screen', 'see screen', 'vision test'],
            'ocr': ['read my screen', 'ocr screen', 'text on screen', 'analyze screen text', 'read the screen', 'scan my screen'],


            
            # Action intents
            'call': ['call', 'dial', 'phone', 'ring', 'reach out', 'contact'],
            'message': ['message', 'text', 'send', 'whatsapp', 'dm', 'ping', 'msg'],
            'play': ['play', 'listen', 'music', 'song', 'video', 'jam', 'drop the beat', 'spin', 'tune', 'start', 'resume', 'queue', 'ytmusic', 'youtube music', 'yt music', 'spotify'],
            # Math Query moved up for priority
            'math_query': ['calculate', 'solve', 'math', 'compute', 'square root', 'sqrt', 'equation', 'plus', 'minus', 'times', 'divided by', 'sine', 'cosine', 'tangent', 'sin', 'cos', 'tan', 'log', 'factorial', 'pi', 'root', 'square', 'cube', 'power'],
            'search': ['search', 'find', 'look up', 'google', 'lookup', 'info', 'check', 'details', 'define', 'kind of', 'types of', 'list of', 'examples of', 'tell me about', 'sort of'],
            
            # Social intents
            'greeting': ['hello', 'hi', 'hey', 'sup', 'yo', 'greetings', 'hiya', 'howdy', 'what\'s up', 'namaste', 'pranam', 'nomoshkar', 'salaam', 'kaise ho', 'kemon acho', 'kemon achen'],
            'goodbye': ['bye', 'goodbye', 'see you', 'later', 'peace', 'ciao', 'leaving', 'exit', 'quit', 'night', 'alvida', 'khuda hafiz'],
            'thanks': ['thank', 'thanks', 'thx', 'appreciate', 'cool', 'awesome', 'great', 'nice', 'shukriya', 'dhanyawad', 'dhonyobad'],
            'identity': ['who are you', 'your name', 'what are you', 'nova', 'hey nova', 'are you nova', 'yourself'],
            
            # System intents
            'help': ['help', 'assist', 'support', 'guide', 'commands', 'what can you do'],
            'status': ['status', 'battery', 'usage', 'health', 'condition', 'system status'],
            'stop': ['stop', 'pause', 'halt', 'end', 'finish', 'quiet', 'shush', 'shut up', 'silence', 'kill', 'terminate'],
            'joke': ['joke', 'funny', 'laugh', 'humor', 'tell me a joke', 'make me laugh', 'comedy', 'jocks'],
            'affection': ['love you', 'like you', 'favorite person', 'best person', 'i love u', 'fav person', 'feb person'],
            'apology': ['sorry', 'apologize', 'my mistake', 'my bad', 'pardon me', 'forgive me', 'maaf', 'maafi', 'khoma'],
            'jealousy': ['siri', 'alexa', 'google', 'gemini', 'claude', 'chatgpt', 'bixby', 'cortana', 'maya', 'sarah', 'emily', 'sakura', 'miku', 'rem', 'emilia'],
            'gaming': ['pubg', 'bgmi', 'minecraft', 'clash of clans', 'coc', 'free fire', 'ff', 'gaming', 'video games', 'play games'],
            
            # Power Intents
            'shutdown': ['shutdown', 'turn off', 'power off', 'system shutdown'],
            'restart': ['restart', 'reboot'],
            'lock': ['lock screen', 'lock pc', 'lock'],
            'sleep': ['sleep mode', 'go to sleep', 'put pc to sleep', 'sleep'],
            'abort': ['abort', 'cancel', 'stop shutdown', 'don\'t shutdown'],
            'voice_status': ['voice registered', 'is my voice registered', 'register my voice', 'voice profile', 'voice recognition status', 'setup voice', 'voice setup'],
            'debug_parameters': ['debug parameters', 'show parameters', 'what are your parameters', 'tell me your parameters', 'her parameter', 'your settings', 'personality settings', 'current configuration'],
            
            'automation': ['automate', 'run script', 'python script', 'system command', 'execute script', 'run python'],
            'minimize': ['minimize', 'hide window', 'show desktop'],
            'maximize': ['maximize', 'fullscreen', 'make bigger'],
            'switch': ['switch window', 'alt tab', 'next window'],
            'scroll': ['scroll', 'go down', 'go up', 'page down', 'page up'],
            'type': ['type', 'typing', 'write'],
            'press': ['press', 'hit key', 'keyboard'],
            'click': ['click', 'mouse click', 'right click', 'double click'],
            'copy': ['copy'],
            'paste': ['paste'],
            'create': ['create folder', 'make folder', 'new folder'],
            'save': ['save'],
            'text_correction': ['correct', 'fix', 'spellcheck', 'grammar', 'typo', 'professional', 'improve'],
            'explain_emotions': ['explain', 'emotion', 'feelings', 'define', 'understand'],
            'troll': ['troll', 'roast', 'mean', 'insult', 'savage'],
            'how_are_you': ['how are you', 'how do you do', 'hru', 'hows it going', 'how have you been', 'you good', 'doing well'],
            'bored': ['bored', 'nothing to do', 'entertain me', 'so bored', 'what should i do'],
            'what_doing': ['what are you doing', 'what you up to', 'whatcha doing', 'what\'s happening', 'busy'],
            'miss_you': ['missed you', 'long time no see', 'where have you been', 'i missed you'],
            'celebration': ['yay', 'i passed', 'i won', 'i did it', 'success', 'hooray', 'awesome'],
            'encouragement': ['wish me luck', 'fingers crossed', 'i can do this', 'nervous', 'hope it goes well'],
            'plans': ['any plans', 'what are your plans', 'what you doing later', 'got plans'],
            'weather_small_talk': ['nice weather', 'it\'s hot', 'it\'s raining', 'beautiful day', 'it\'s cold'],
            'food_talk': ['i\'m hungry', 'hungry', 'food', 'what should i eat', 'craving']
        }
        
        # Command mappings for dispatcher
        self.intent_to_command = {
            'call': 'call',
            'message': 'send message',
            'play': 'play',
            'search': 'search',
            'open': 'open',
            'download': 'download',
            'remind': 'remind',
            'volume': 'volume',
            'screenshot': 'screenshot',
            'time': 'time',
            'news': 'news',
            'help': 'help',
            'status': 'usage',
            'stop': 'stop',
            'joke': 'joke',
            'affection': 'affection',
            'apology': 'apology',
            'jealousy': 'jealousy',
            'gaming': 'gaming',
            'shutdown': 'shutdown',
            'restart': 'restart',
            'lock': 'lock',
            'sleep': 'sleep',
            'voice_status': 'voice_status',
            'debug_parameters': 'debug_parameters',
            'abort': 'abort',
            'cancel': 'cancel',
            'automation': 'automate',
            'minimize': 'minimize',
            'maximize': 'maximize',
            'switch': 'switch window',
            'scroll': 'scroll down', # Default
            'type': 'type',
            'press': 'press',
            'click': 'click',
            'copy': 'copy',
            'paste': 'paste',
            'create': 'create folder',
            'save': 'save',
            'text_correction': 'correct this',
            'explain_emotions': 'explain emotions',
            'troll': 'troll',
            'math_query': 'calculate',
            'weather': 'weather',
            'date': 'date',
            'how_are_you': 'how are you',
            'bored': 'bored',
            'what_doing': 'what are you doing',
            'miss_you': 'missed you',
            'celebration': 'celebrated',
            'encouragement': 'encouragement',
            'plans': 'plans',
            'weather_small_talk': 'weather small talk',
            'food_talk': 'food talk',
            'when': 'time',
            'natural_events': 'natural events',
            'earthquakes': 'earthquakes',
            'vision': 'look at my screen',
            'ocr': 'read my screen',
            'tides': 'tides',
        }

    
    def normalize_text(self, text: str, language: str = "en") -> str:
        """
        Normalize and clean transcribed text with dialect and slang recognition.
        Only applies English corrections if language is 'en' or not specified.
        """
        """Normalize and clean transcribed text with dialect and slang recognition"""
        if not text:
            return ""
        
        # Remove extra whitespace
        normalized = ' '.join(text.split())
        
        # ASR Error Corrections (Common misrecognitions)
        asr_corrections = {
            "we're": "weather",
            "we are": "weather",
            "whether": "weather",
            "where": "weather",
            "new": "news",
            "knew": "news",
            "use": "news",
            "remind me": "remind",
            "remember": "remind",
            "call me": "call",
            "time now": "time",
            "what time": "time",
            "sloop": "sleep",
            "slap": "sleep",
            "asleep": "sleep",
        }
        
        # Apply ASR corrections (case-insensitive, word-boundary aware)
        normalized_lower = normalized.lower()
        for error, correction in asr_corrections.items():
            if error in normalized_lower:
                # Replace only if it's a standalone phrase or at word boundaries
                import re
                pattern = r'\b' + re.escape(error) + r'\b'
                normalized = re.sub(pattern, correction, normalized, flags=re.IGNORECASE)
        
        # Indian English dialect and slang recognition
        dialect_slang_map = {
            # Common Indian English slang
            'yaar': 'friend',
            'bhai': 'brother',
            'dude': 'friend',
            'bro': 'brother',
            'sis/': 'sister',
            'didi': 'sister',
            
            # Hinglish (Hindi-English mix)
            'kya': 'what',
            'kaise': 'how',
            'kahan': 'where',
            'kab': 'when',
            'kyun': 'why',
            'achha': 'okay',
            'theek hai': 'okay',
            'haan': 'yes',
            'nahi': 'no',
            'bas': 'just',
            'abhi': 'now',
            'kal': 'tomorrow',
            'aaj': 'today',
            
            # Common abbreviations
            'plz': 'please',
            'pls': 'please',
            'thx': 'thanks',
            'thnx': 'thanks',
            'ty': 'thank you',
            'tysm': 'thank you so much',
            'tyvm': 'thank you very much',
            'np': 'no problem',
            'btw': 'by the way',
            'idk': "I don't know",
            'omg': 'oh my god',
            'lol': 'laughing',
            'asap': 'as soon as possible',
            
            # Gen Z / Internet Slang (Expanded)
            'tysm': 'thank you so much',
            'fr': 'for real',
            'ngl': 'not gonna lie',
            'ik': 'I know',
            'wru': 'where are you',
            'hru': 'how are you',
            'gtg': 'got to go',
            'lmao': 'laughing my ass off',
            'rofl': 'rolling on the floor laughing',
            'imho': 'in my humble opinion',
            'ily': 'I love you',
            'lmk': 'let me know',
            'rn': 'right now',
            'sus': 'suspicious',
            'cap': 'lie',
            'no cap': 'no lie',
            'bet': 'okay',
            'slay': 'great job',
            'fire': 'amazing',
            'lit': 'amazing',
            'ghosted': 'ignored',
            'lowkey': 'secretly',
            'highkey': 'obviously',
            'vibe': 'feeling',
            'vibing': 'chilling',
            
            # Indian English variations
            'prepone': 'reschedule earlier',
            'do the needful': 'do what is necessary',
            'revert back': 'reply',
            'out of station': 'out of town',
            'timepass': 'leisure activity',
            'updation': 'update',
            'doubt': 'question',
            'expire': 'end',

            # Internet/Gaming Slang (New additions)
            'gg': 'good game',
            'wb': 'welcome back',
            'brb': 'be right back',
            'afk': 'away from keyboard',
            'nvm': 'nevermind',
            'irl': 'in real life',
            'imo': 'in my opinion',
            'glhf': 'good luck have fun',
            
            # Additional Indian text-speak/Casual
            'arrey': 'hey',
            'pakka': 'sure',
            'chal': 'come (let\'s go)',
            'chalo': 'let\'s go',
            'haanji': 'yes sir/ma\'am',
            'mast': 'great',
            'badiya': 'good',
            'pagal': 'crazy',
            'scene': 'situation',
            'scene on': 'plan confirmed',
            
            # Common misspellings/variations
            'gonna': 'going to',
            'wanna': 'want to',
            'gotta': 'got to',
            'lemme': 'let me',
            'gimme': 'give me',
            'dunno': "don't know",
            'kinda': 'kind of',
            'sorta': 'sort of',
            'yeah': 'yes',
            'nope': 'no',
            'yep': 'yes',
            'nah': 'no',
            
            # Fix common transcription errors
            'nova': 'Nova',
            'NOVA': 'Nova',
            'ok google': 'okay',
            'hey siri': 'hey',
            'alexa': 'Nova',
            
            # Fix spacing around punctuation
            ' .': '.',
            ' ,': ',',
            ' ?': '?',
            ' !': '!',
            ' :': ':',
            ' ;': ';',
        }
        
        # Apply dialect and slang replacements (case-insensitive)
        # ONLY if the language is English
        normalized_lower = normalized.lower()
        if language and language.startswith('en'):
            for slang, standard in dialect_slang_map.items():
                # Use word boundaries to avoid partial matches
                import re
                pattern = r'\b' + re.escape(slang) + r'\b'
                normalized = re.sub(pattern, standard, normalized, flags=re.IGNORECASE)
        
        # Capitalize first letter
        if normalized:
            normalized = normalized[0].upper() + normalized[1:]
        
        # Ensure proper sentence ending
        if normalized and normalized[-1] not in '.!?':
            # Don't add period if it's a command-like sentence
            if not any(normalized.lower().startswith(cmd) for cmd in ['call', 'play', 'search', 'open', 'send']):
                normalized += '.'
        
        return normalized.strip()
    
    def extract_entities(self, text: str) -> Dict[str, any]:
        """Extract entities from text"""
        entities = {}
        
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
        quoted_pattern = r'["\'](.*?)["\']'
        quoted = re.findall(quoted_pattern, text)
        if quoted:
            entities['quoted_text'] = quoted
        
        # Extract message content after "saying" or "message" (unquoted)
        if not quoted:
            msg_match = re.search(r'(?:saying|message|say|tell him|tell her|tell them) (.+)', text, re.IGNORECASE)
            if msg_match:
                entities['message_content'] = msg_match.group(1).strip()
        
        # Extract potential contact names (everything between 'message' and 'saying')
        contact_match = re.search(r'(?:message|whatsapp|to) ([\w\s]+?)(?: saying| say|$)', text, re.IGNORECASE)
        if contact_match:
            entities['contact_name'] = contact_match.group(1).strip()
        
        return entities
    
    def recognize_intent(self, text: str) -> Tuple[Optional[str], float]:
        """Recognize intent from text using keyword matching"""
        text_lower = text.lower()
        best_intent = None
        best_score = 0.0
        
    def recognize_intent(self, text: str) -> Tuple[Optional[str], float]:
        """Recognize intent from text using keyword matching"""
        text_lower = text.lower()
        best_intent = None
        best_score = 0.0
        
        for intent, keywords in self.intent_patterns.items():
            for keyword in keywords:
                # Use word boundary to avoid partial matches (e.g. "call" in "recall")
                pattern = r'\b' + re.escape(keyword) + r'\b'
                match = re.search(pattern, text_lower)
                if match:
                    # Base score for finding a keyword
                    score = 0.8
                    
                    # Boost score if keyword is a significant part of the sentence
                    if len(keyword) / len(text_lower) > 0.5:
                        score = 0.9
                    if keyword == text_lower:  # Exact match
                        score = 1.0
                    
                    # Boost if keyword is at the start (Command priority)
                    if text_lower.startswith(keyword):
                        score += 0.15

                    if score > best_score:
                        best_score = score
                        best_intent = intent
        
        return best_intent, best_score    
    def fuzzy_match_command(self, text: str, commands: List[str], threshold: float = 0.6) -> Optional[str]:
        """Find best matching command using fuzzy matching"""
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
        # Extract entities
        entities = self.extract_entities(text)
        
        # Recognize intent
        intent, confidence = self.recognize_intent(text)
        
        # Get command mapping
        command = None
        if intent and intent in self.intent_to_command:
            command = self.intent_to_command[intent]
        
        result = {
            'original_text': text,
            'intent': intent,
            'confidence': confidence,
            'command': command,
            'entities': entities,
            'processed': True
        }
        
        return result
    
    def enhance_command(self, text: str, nlp_result: Dict) -> str:
        """Enhance command with NLP understanding"""
        # If we have a clear command mapping, use it
        if nlp_result['command']:
            # Keep the original text for context
            return text
        
        # Otherwise, return original
        return text
    
    def get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            'call': 'Making a phone call',
            'message': 'Sending a message',
            'play': 'Playing media',
            'search': 'Searching for information',
            'open': 'Opening an application',
            'download': 'Downloading a file',
            'remind': 'Setting a reminder',
            'greeting': 'Greeting',
            'thanks': 'Expressing gratitude',
            'identity': 'Asking about identity',
        }
        return descriptions.get(intent, 'Unknown intent')
    
    # ===== NLU-Specific Features =====
    
    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of user input"""
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = ['happy', 'great', 'awesome', 'love', 'thanks', 'perfect', 
                         'excellent', 'good', 'nice', 'wonderful', 'amazing']
        # Negative indicators
        negative_words = ['sad', 'angry', 'hate', 'terrible', 'bad', 'awful', 
                         'horrible', 'annoyed', 'frustrated', 'upset', 'disappointed']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def extract_semantic_meaning(self, text: str, intent: str) -> Dict:
        """Extract semantic meaning based on intent"""
        semantic = {
            'action': None,
            'target': None,
            'modifier': None,
            'temporal': None
        }
        
        # Extract action verbs
        action_verbs = ['call', 'send', 'play', 'search', 'open', 'download', 
                       'remind', 'set', 'get', 'find', 'show']
        for verb in action_verbs:
            if verb in text.lower():
                semantic['action'] = verb
                break
        
        # Extract temporal expressions
        temporal_words = ['now', 'later', 'tomorrow', 'today', 'tonight', 
                         'morning', 'afternoon', 'evening']
        for temp in temporal_words:
            if temp in text.lower():
                semantic['temporal'] = temp
                break
        
        # Extract modifiers (urgency, politeness)
        if any(word in text.lower() for word in ['please', 'kindly', 'could you']):
            semantic['modifier'] = 'polite'
        if any(word in text.lower() for word in ['urgent', 'asap', 'quickly', 'now']):
            semantic['modifier'] = 'urgent'
        
        return semantic
    
    def resolve_context(self, text: str, dialogue_state: Dict) -> Dict:
        """Resolve pronouns and references using dialogue context"""
        resolved = {
            'original': text,
            'resolved': text,
            'references': []
        }
        
        # Pronoun resolution
        pronouns = {
            'it': dialogue_state.get('last_entities', {}).get('target'),
            'that': dialogue_state.get('last_intent'),
            'this': dialogue_state.get('conversation_topic')
        }
        
        for pronoun, reference in pronouns.items():
            if pronoun in text.lower() and reference:
                resolved['references'].append({
                    'pronoun': pronoun,
                    'refers_to': reference
                })
        
        return resolved
    
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
        # Split by conjunctions and common step-markers
        segments = re.split(r'\b(?:and|then|also|plus|as well as)\b|[,;]', text, flags=re.IGNORECASE)
        # Clean segments
        return [s.strip() for s in segments if len(s.strip()) > 3]

    def process_with_nlu(self, text: str, min_confidence: float = 0.5) -> List[Dict]:
        """
        AGI-ready NLU. Returns a LIST of results for sequential execution.
        """
        from core.agi_context import agi_context
        
        # 1. Capture Global Chain Context (Mood)
        global_sentiment = self.analyze_sentiment(text)
        agi_context.current_mood = global_sentiment
        print(f"🧠 AGI Brain: Global Sentiment detected as '{global_sentiment}'")

        raw_segments = self.segment_intents(text)
        if len(raw_segments) <= 1:
            raw_segments = [text]

        results = []
        for segment in raw_segments:
            entities = self.extract_entities(segment)
            intent, confidence = self.recognize_intent(segment)
            
            # Contextual Recovery
            if confidence < min_confidence:
                 last_intent = self.dialogue_state.get('last_intent')
                 if last_intent and re.search(r'\d+', segment):
                      intent = last_intent
                      confidence = 0.9

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
