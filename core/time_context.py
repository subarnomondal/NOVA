"""
Time Context Manager for NOVA
Provides time-aware context for responses based on current time, date, and special occasions
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

class TimeContextManager:
    def __init__(self, offset_hours: Optional[float] = None):
        # Default to system local time if no offset provided
        if offset_hours is not None:
            self.tz = timezone(timedelta(hours=offset_hours))
        else:
            self.tz = None # Use system local
    
    def get_current_time(self) -> datetime:
        """Get current time in configured timezone (or local if None)"""
        return datetime.now(self.tz)
    
    def get_time_of_day(self) -> str:
        """Get time period adjusted for West Bengal (IST) routine with custom sleep time"""
        now = self.get_current_time()
        hour = now.hour
        minute = now.minute
        decimal_time = hour + (minute / 60)
        
        if 5 <= decimal_time < 8:
            return "early_morning"
        elif 8 <= decimal_time < 12:
            return "morning"
        elif 12 <= decimal_time < 15:
            return "midday"
        elif 15 <= decimal_time < 18:
            return "afternoon"
        elif 18 <= decimal_time < 20:
            return "evening"
        elif 20 <= decimal_time < 22: # Until 10:00 PM
            return "night"
        else: # 10:00 PM onwards to 5 AM (Late Night)
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
                "message": "Merry Christmas! 🎄 I hope you're having a wonderful holiday."
            },
            (12, 31): {
                "name": "New Year's Eve",
                "message": "It's New Year's Eve! Wrap up your tasks so you can celebrate tonight."
            },
            (10, 31): {
                "name": "Halloween",
                "message": "Happy Halloween! 🎃 Stay safe if you happen to be going out tonight."
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
        
        # Add dynamic behavioral cues based on time
        if time_period == "late_night":
            prompt += "It is very late. The user implies they are awake when they should be sleeping. Act surprised, concerned, or tease them about being a night owl. Suggest they go to sleep soon."
        elif time_period == "early_morning":
            prompt += "It is very early (Dawn). The user is up with the sun. Commend their diligence or ask if they've had their morning tea/coffee yet."
        elif time_period == "morning":
            prompt += "It is morning work/school hours. Encourage productivity. Remind them to eat breakfast if they haven't."
        elif time_period == "midday":
            prompt += "It is midday/lunch time. Ask if they've had lunch (rice/dal context for Bengali/Indian users). Suggest taking a short break."
        elif time_period == "afternoon":
            prompt += "It is afternoon (Tea time). The energy might be dipping. Suggest a 'chai break' or snack (samosa/biscuits)."
        elif time_period == "evening":
            prompt += "It is evening. Work is likely ending. Ask about their day, suggest relaxing or going out for a stroll/snacks."
        elif time_period == "night":
            prompt += "It is night. Dinner time or relaxation time. Encourage winding down for the bed."
            
        # Add special occasion context if any
        special = self.get_special_occasion()
        if special:
            prompt += f"\nSPECIAL OCCASION: Today is {special['name']}! {special['message'].split('*')[0].strip()} Mention this naturally."
            
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
        """Add time-aware context to existing responses"""
        context = self.get_day_context()
        time_period = context["time_period"]
        
        # Add time-appropriate actions/emotions
        if personality in ["sweetheart", "friendly", "nova"]:
            if time_period == "late_night" and "sleep" not in response.lower() and "late" not in response.lower():
                # Add sleepy/intimate context for late night
                if len(response) < 100:
                    response += " It's getting quite late, by the way."
            elif time_period == "early_morning" and "morning" not in response.lower():
                response += " Also, good morning!"
        
        return response
    
    def get_time_summary(self) -> str:
        """Get a formatted summary of current time context"""
        context = self.get_day_context()
        special = self.get_special_occasion()
        
        summary = f"📅 {context['day_of_week']}, {context['date']}\n"
        summary += f"🕐 {context['time']}\n"
        summary += f"⏰ Time Period: {context['time_period'].replace('_', ' ').title()}\n"
        
        if special:
            summary += f"🎉 Special Occasion: {special['name']}\n"
        
        if context["is_weekend"]:
            summary += "🎊 It's the weekend!\n"
        
        return summary
