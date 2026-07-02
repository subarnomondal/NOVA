"""
Calendar Skill for Nova
Provides access to Google Calendar (Web) and Windows Calendar
"""

import webbrowser
import os
import platform

def cmd_calendar(args):
    """Usage: open calendar / check schedule"""
    try:
        # Default to Google Calendar (Web) as it's most common for cross-platform users
        # But allow specific "windows calendar" request
        
        args = args.lower()
        
        if "windows" in args or "app" in args:
            # Open Windows Calendar
            print(" Opening Windows Calendar...")
            return "Proping open the Windows Calendar! Oki doki! "
            
        else:
            # Open Google Calendar
            print(" Opening Google Calendar...")
            webbrowser.open("https://calendar.google.com")
            
            import random
            responses = [
                "Opening your Google Calendar! Let's see what's up! ",
                "Checking your schedule... Hehe~ ️",
                "Here is your Google Calendar! All organized! (◕‿◕✿) ✨"
            ]
            return random.choice(responses)
            
    except Exception as e:
        print(f"Calendar Error: {e}")
        return f"Oops, I couldn't open the calendar. Error: {e}"

def register(dispatcher):
    dispatcher.register("calendar", cmd_calendar)
    dispatcher.register("open calendar", cmd_calendar)
    dispatcher.register("check schedule", cmd_calendar)
    dispatcher.register("show calendar", cmd_calendar)
    dispatcher.register("schedule", cmd_calendar) # Overlap with reminds, but dispatcher handles explicit matches first usually
