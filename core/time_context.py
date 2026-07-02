"""
Time Context Manager for NOVA
Provides time-aware context for responses based on current time, date, and special occasions
"""

from datetime import datetime, timedelta, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for Python < 3.9
    from datetime import timezone as ZoneInfo
from typing import Dict, Optional

class TimeContextManager:
    def __init__(self, offset_hours: Optional[float] = None, routine: Optional[Dict] = None, timezone_str: Optional[str] = "Asia/Kolkata"):
        self.tz = None
        # 1. Prioritize Geographical Timezone String
        if timezone_str:
            try:
                self.tz = ZoneInfo(timezone_str) # type: ignore
            except:
                self.tz = None
                
        # 2. Fallback to Numerical Offset
        if self.tz is None and offset_hours is not None:
            self.tz = timezone(timedelta(hours=offset_hours))
            
        # Personalized Routine (Defaults to standard IST routine if not provided)
        self.routine = routine or {
            "wake_up": 8.0,
            "sleep": 22.0,
            "midday_break": 13.0,
            "evening_start": 18.0
        }
    
    def get_current_time(self) -> datetime:
        """Get current time in configured timezone (or local if None)"""
        return datetime.now(self.tz)
    
    def get_time_of_day(self) -> str:
        """Get time period adjusted for User's personalized routine"""
        now = self.get_current_time()
        hour = now.hour
        minute = now.minute
        decimal_time = hour + (minute / 60)
        
        wake = self.routine.get("wake_up", 8.0)
        sleep = self.routine.get("sleep", 22.0)
        midday = self.routine.get("midday_break", 13.0)
        evening = self.routine.get("evening_start", 18.0)
        
        # Early Morning: Before Wake up (but after 5 AM)
        if 5.0 <= decimal_time < wake:
            return "early_morning"
        # Morning: Wake up to Midday
        elif wake <= decimal_time < midday:
            return "morning"
        # Midday: Midday to Afternoon (Midday + 3h)
        elif midday <= decimal_time < (midday + 2):
            return "midday"
        # Afternoon: Midday+2 to Evening
        elif (midday + 2) <= decimal_time < evening:
            return "afternoon"
        # Evening: Evening to Sleep
        elif evening <= decimal_time < sleep:
            return "evening"
        # Night: Sleep to 1h after sleep
        elif sleep <= decimal_time < (sleep + 1.5):
            return "night"
        # Late Night: Sleep+1.5 to 5 AM
        else:
            return "late_night"
    
    def get_greeting(self, personality: str = "nova") -> str:
        """Get time-appropriate greeting based on personality"""
        time_period = self.get_time_of_day()
        now = self.get_current_time()
        
        # Standard Nova greetings
        if personality in ["sweetheart", "friendly", "nova", "savage", "cookie"]:
            greetings = {
                "late_night": [
                    "You're still working? It's quite late. Make sure you get some rest soon.",
                    "It's past 10 PM. I'm here if you need anything, but don't forget to sleep.",
                    "Still up? Let's finish this quickly so you can head to bed."
                ],
                "early_morning": [
                    "Good morning! It's quite early. Have you had your coffee or tea yet?",
                    "Morning. You're up early today. Let's make it a productive one!",
                    "Good morning. The sun is just coming up. Ready to start the day?"
                ],
                "morning": [
                    "Good morning! I hope you're having a great start to your day.",
                    "Good morning. Let me know what's on the agenda for today.",
                    "Morning! Ready to get to work?"
                ],
                "midday": [
                    "It's midday. Have you taken a break for lunch yet?",
                    "Hello! It's the middle of the day. Remember to stay hydrated.",
                    "Good midday. Let's keep the momentum going!"
                ],
                "afternoon": [
                    "Good afternoon! Might be time for a quick tea or coffee break.",
                    "Afternoon! We're past the halfway mark of the day. How's it going?",
                    "Good afternoon. Let me know if you need help wrapping things up."
                ],
                "evening": [
                    "Good evening! I hope you had a productive day.",
                    "Evening! Winding down for the day, or still working?",
                    "Good evening. It's getting dark out. Time to relax soon."
                ],
                "night": [
                    "Good night. Time to relax and have some dinner.",
                    "Good night! I hope you can unwind after today.",
                    "It's getting late. Make sure you take it easy tonight."
                ]
            }
            
            import random
            return random.choice(greetings.get(time_period, greetings["morning"]))
        
        # Bengali mode greetings (Even more localized)
        elif personality == "bengali":
            greetings = {
                "late_night": "Arey! 10-ta বেজে গেছে, akhono ghumao ni? Ektu rest koro Dada, ratri onek holo!",
                "early_morning": "Shuvo sokal! *smiles* Tea and biscuits hoyeche? Sunrise is beautiful today!",
                "morning": "Good morning! Sokal sokal luchi-torkari khele na ki? Work hard, kaje mon dao!",
                "midday": "Nomoshkar! Midday hoye gelo. Bhaat-daal-mach hole toh jome jabe! Hehe~",
                "afternoon": "Good afternoon! Cha-er sathe samosa ba chops hoye jak? It's snack time!",
                "evening": "Sondha belar shubhechha! Adda bondhu-der sathe? Phuchka khete vulo na kintu!",
                "night": "Good night! Dinner hoyeche? Dinner light rakha-i bhalo kintu. Relax koro ebar!",
            }
            return greetings.get(time_period, "Namaste! Kemon acho?")
        
        # Professional mode
        elif personality == "professional":
            greetings = {
                "late_night": "Working late. Noted. Status update?",
                "early_morning": "Early start. Commendable. Today's priorities?",
                "morning": "Good morning. Ready to execute.",
                "afternoon": "Afternoon. Progress check?",
                "evening": "Evening. Day summary?",
                "night": "End of day. Rest recommended."
            }
            return greetings.get(time_period, "Status?")
        
        # Default
        return "Hello!"
    
    def get_special_occasion(self, user_birthday: Optional[str] = None, user_name: str = "User") -> Optional[Dict]:
        """Check if today is a special occasion"""
        now = self.get_current_time()
        month = now.month
        day = now.day
        
        # Check user birthday first (priority)
        if user_birthday:
            try:
                # Format: "MM-DD"
                b_month, b_day = map(int, user_birthday.split("-"))
                if b_month == month and b_day == day:
                    return {
                        "name": "User Birthday",
                        "message": f"Happy Birthday, {user_name}! ✨ I hope you have a fantastic day today."
                    }
            except:
                pass

        occasions = {
            (1, 1): {
                "name": "New Year's Day",
                "message": "Happy New Year! ✨ Here's to a great year ahead for both of us."
            },
            (2, 14): {
                "name": "Valentine's Day",
                "message": "Happy Valentine's Day! I hope you spend it with people you care about."
            },
            (12, 25): {
                "name": "Christmas",
                "message": "Merry Christmas!  I hope you're having a wonderful holiday."
            },
            (12, 31): {
                "name": "New Year's Eve",
                "message": "It's New Year's Eve! Wrap up your tasks so you can celebrate tonight."
            },
            (10, 31): {
                "name": "Halloween",
                "message": "Happy Halloween!  Stay safe if you happen to be going out tonight."
            }
        }
        
        return occasions.get((month, day))
    
    def get_day_context(self) -> Dict:
        """Get context about the current day"""
        now = self.get_current_time()
        
        return {
            "day_of_week": now.strftime("%A"),
            "is_weekend": now.weekday() >= 5,
            "is_monday": now.weekday() == 0,
            "is_friday": now.weekday() == 4,
            "date": now.strftime("%B %d, %Y"),
            "time": now.strftime("%I:%M %p"),
            "hour": now.hour,
            "time_period": self.get_time_of_day()
        }
    
    
    def get_time_prompt(self) -> str:
        """Get LLM instructions based on current time context (Dynamic Awareness)"""
        context = self.get_day_context()
        time_period = context["time_period"]
        time_str = context["time"]
        
        prompt = f"Current Time: {time_str} ({time_period.replace('_', ' ').title()}). "
        
        # Add dynamic behavioral cues based on time (Background Context only)
        if time_period == "late_night":
            prompt += "It is late night. Respond with a calm, slightly lower energy tone."
        elif time_period == "early_morning":
            prompt += "It is early morning."
        elif time_period == "morning":
            prompt += "It is morning."
        elif time_period == "midday":
            prompt += "It is midday."
        elif time_period == "afternoon":
            prompt += "It is afternoon."
        elif time_period == "evening":
            prompt += "It is evening."
        elif time_period == "night":
            prompt += "It is night time."
            
        # Add special occasion context if any
        special = self.get_special_occasion()
        if special:
            prompt += f"\nNote: Today is {special['name']}."
            
        return prompt

    def get_contextual_response(self, query: str, personality: str = "nova") -> Optional[str]:
        """Get time-aware contextual response"""
        # ... logic mostly moved to LLM via get_time_prompt, but keeping specific triggers ...
        query_lower = query.lower()
        context = self.get_day_context()
        time_period = context["time_period"]
        
        # Greeting responses - ONLY for very explicit greetings, not general conversation
        # Changed to be more selective - only "hello", "hi", "hey" alone, not in sentences
        if query_lower.strip() in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "good night"]:
            return self.get_greeting(personality)
        
        return None
    
    def enhance_response_with_time_context(self, response: str, personality: str = "nova") -> str:
        """Disabled to prevent repetitive time-shaming."""
        return response
    
    def get_time_summary(self) -> str:
        """Get a formatted summary of current time context"""
        context = self.get_day_context()
        special = self.get_special_occasion()
        
        summary = f" {context['day_of_week']}, {context['date']}\n"
        summary += f" {context['time']}\n"
        summary += f"⏰ Time Period: {context['time_period'].replace('_', ' ').title()}\n"
        
        if special:
            summary += f" Special Occasion: {special['name']}\n"
        
        if context["is_weekend"]:
            summary += " It's the weekend!\n"
        
        return summary
