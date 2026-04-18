
import os
import time
from core.vision_manager import vision_manager
from core.llm_manager import llm_manager
from core.personality_manager import PersonalityManager

def cmd_ocr_screen(args):
    """Usage: read my screen / ocr screen"""
    try:
        print("🔍 Vision Skill: OCR Mode - Scanning screen for text...")
        filepath = vision_manager.capture_screen()
        if not filepath:
            return "❌ I'm trying to look, but your screen is a bit shy right now. Can you check if my visibility is blocked? 🔄"

        # Active Window for context
        import pygetwindow as gw
        window_title = "Unknown Window"
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                window_title = active_window.title
        except: pass

        # Persona-aware prompt for OCR & Understanding
        pm = PersonalityManager()
        active_persona = pm.get_active_personality()
        
        prompt = (
            f"CONTEXT: You are looking at the user's screen. The active window is '{window_title}'.\n"
            "TASK: Read all the important text, code, or messages you see on this screen.\n"
            "- If it's a chat, tell me who is talking and what they are saying.\n"
            "- If it's code, explain what it does or find any obvious errors.\n"
            "- If it's a website or document, summarize the main points.\n"
            "- Be very specific. Quote text if necessary.\n"
            "Nova:"
        )

        # Send to multimodal LLM
        response = llm_manager.generate(
            user_input=f"What is on my screen in '{window_title}'?",
            image_path=filepath,
            system_prompt=prompt,
            max_tokens=600,
            temperature=0.3 # Lower temperature for better OCR accuracy
        )
        
        # Cleanup
        if os.path.exists(filepath):
            os.remove(filepath)
            
        return response if response else "I scanned the screen, but I couldn't make out any clear text! Is it too blurry? 🧐"

    except Exception as e:
        print(f"❌ OCR Skill Error: {e}")
        return f"Oops! My logic circuits got a bit tangled while reading your screen. Error: {str(e)}"

def register(dispatcher):
    # Map both old and new triggers to the improved multimodal OCR function
    dispatcher.register("look at my screen", cmd_ocr_screen)
    dispatcher.register("what am I doing", cmd_ocr_screen)
    dispatcher.register("describe screen", cmd_ocr_screen)
    dispatcher.register("vision test", cmd_ocr_screen)
    
    # Dedicated OCR Triggers
    dispatcher.register("read my screen", cmd_ocr_screen)
    dispatcher.register("ocr screen", cmd_ocr_screen)
    dispatcher.register("text on screen", cmd_ocr_screen)
    dispatcher.register("analyze screen text", cmd_ocr_screen)
    dispatcher.register("read the screen", cmd_ocr_screen)
    dispatcher.register("scan my screen", cmd_ocr_screen)
