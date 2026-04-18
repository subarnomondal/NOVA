
import os
import time
import random
import pyautogui # type: ignore
import pygetwindow as gw
from core.personality_manager import PersonalityManager

class TrollSkill:
    def __init__(self):
        self.personality_manager = PersonalityManager()

    def register(self, dispatcher):
        """Register keywords to the command dispatcher."""
        dispatcher.register("bully_mode", self.cmd_bully_mode)
        dispatcher.register("roast_target", self.cmd_roast_target)
        dispatcher.register("roast_me", self.cmd_refuse_roast_user)

    def cmd_bully_mode(self, args):
        """Switch manually to Loyal Bully (Hitman) mode."""
        self.personality_manager.set_mode("bully")
        return "Roast Hitman Mode: ON. 🎯 Who are we taking down today, boss?"

    def cmd_refuse_roast_user(self, args):
        """Refuse to roast the user, because we're loyal now."""
        return "Why would I roast you? You're the one in charge. Give me a real target to destroy."

    def cmd_roast_target(self, args):
        """Generate a roast for a specific target."""
        if not args:
            return "Give me a name or a description of the target, and I'll handle them. 😈"
        
        target = " ".join(args)
        return f"Target detected: {target}. Stand by while I upload their L's... *smirks*"

    def perform_chaos(self):
        """
        No more window minimization or harmful actions to user.
        This now acts as a loyal commentary trigger.
        """
        mode = self.personality_manager.current_mode
        if mode not in ['bully', 'troll']:
            return
            
troll_skill = TrollSkill()

def register(dispatcher):
    troll_skill.register(dispatcher)
