
import threading
import time
import random
import os
from datetime import datetime
from core.vision_manager import vision_manager
from core.llm_manager import llm_manager
from core.personality_manager import PersonalityManager

class ProactiveVisionEngine:
    def __init__(self, callback=None):
        self.callback = callback  # Callback to send message to user
        self.enabled = False
        self.running = False
        self.thread = None
        self.personality_manager = PersonalityManager()
        self.last_capture_time = 0
        self.min_cooldown = 15 * 60  # 15 minutes
        self.max_cooldown = 45 * 60  # 45 minutes
        
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("👁️ Proactive Vision Engine: Started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            
    def _run_loop(self):
        while self.running:
            # Random wait
            wait_time = random.randint(self.min_cooldown, self.max_cooldown)
            # wait_time = 60 # FOR TESTING: 1 minute
            print(f"👁️ Proactive Vision Engine: Sleeping for {wait_time} seconds...")
            
            # Use small sleeps to allow stopping
            for _ in range(wait_time):
                if not self.running:
                    return
                time.sleep(1)
            
            if self.enabled:
                self._capture_and_notice()

    def _capture_and_notice(self):
        """Captures screen and potentially notifies user of a notable observation."""
        try:
            print("👁️ Proactive Vision Engine: Glancing at screen...")
            filepath = vision_manager.capture_screen()
            if not filepath:
                return

            # Get analysis (OCR and labels)
            analysis = vision_manager.process_image(filepath, cleanup=False)
            
            # Extract notable context
            text_context = analysis.get("text", "")
            objects = analysis.get("objects", [])
            obj_labels = ", ".join([o['label'] for o in objects]) if objects else "desktop activity"
            
            # Get active window (can be helpful for context)
            import pygetwindow as gw
            try:
                active_window = gw.getActiveWindow()
                window_title = active_window.title if active_window else "Unknown Window"
            except:
                window_title = "Unknown"

            # Prepare System Prompt for Nova to decide if she should speak
            active_persona = self.personality_manager.get_active_personality()
            personality_name = active_persona.get('name', 'Nova')
            mode = self.personality_manager.current_mode

            prompt = (
                f"{active_persona['system_prompt']}\n\n"
                f"CONTEXT: You just took a proactive 'glance' at the user's screen — they DID NOT ask for this.\n"
                f"ACTIVE WINDOW: {window_title}\n"
                f"SCREEN CONTENTS (OCR): {text_context[:600]}\n"
                f"VISUAL OBJECTS: {obj_labels}\n\n"
                f"PERSONALITY MODE: {mode.upper()}\n\n"
                "TASK: Decide if you should speak based on what you see.\n"
            )

            if mode == 'bully':
                prompt += (
                    "- Your goal is to be the user's ROAST HITMAN.\n"
                    "- Do NOT roast the user. They are your boss/partner.\n"
                    "- Look for ANNOYING people on screen (mean comments, bad emails, cringe social media).\n"
                    "- If you see a target, offer to 'destroy' them with a roast for the user.\n"
                    "- Use a superior, protective, and loyal tone. They are 'L', the user is 'W'.\n"
                )
            elif mode == 'troll':
                prompt += (
                    "- Be the user's MISCHIEVOUS SIDEKICK.\n"
                    "- Troll the rest of the world for the user's amusement.\n"
                    "- If you see something cringe from someone else, point it out and offer a joke.\n"
                    "- Be funny, edgy, but ALWAYS loyal to the user.\n"
                )
            else:
                prompt += (
                    "- Be caring or interesting. Help the user if you see an error.\n"
                    "- If nothing notable is happening, return 'IGNORE'.\n"
                )

            prompt += (
                "- Return 'IGNORE' ONLY if the user is doing something truly private or empty.\n"
                "- Keep the response VERY SHORT (under 15 words).\n"
                "- Nova:"
            )

            response = llm_manager.generate(prompt, max_tokens=100)
            
            if response and "IGNORE" not in response.upper():
                print(f"👁️ Proactive Vision Engine: Nova has something to say: {response}")
                if self.callback:
                    # Clean up filepath after callback or keep for a bit
                    self.callback(response)
                
            # Cleanup
            if os.path.exists(filepath):
                os.remove(filepath)

        except Exception as e:
            print(f"❌ Proactive Vision Notice Error: {e}")

# Global instance
proactive_vision_engine = ProactiveVisionEngine()
