"""
SmallTalk Skill for Nova
Handles casual conversation using the LLM to ensure Personality Consistency.
Merges personality switching and general chit-chat.
"""
import random
from core.llm_manager import llm_manager

def generate_response(prompt, intent, temp=0.85):
    """Helper to generate consistent personality responses with improved model"""
    try:
        response = llm_manager.generate(prompt, intent=intent, temperature=temp)
        if response:
            return response
    except Exception as e:
        print(f"LLM Error: {e}")
    return None

def cmd_switch_personality(args):
    """Usage: switch to troll mode / be standard / be sweetheart"""
    text = args.lower()
    pm = llm_manager.personality_manager
    available = pm.get_available_modes()
    
    target_mode = None
    if "troll" in text or "roast" in text or "savage" in text or "cookie" in text:
        target_mode = "troll"
    elif "friendly" in text or "standard" in text or "normal" in text or "nova" in text:
        target_mode = "nova"
    elif "professional" in text or "work" in text:
        target_mode = "professional"
    elif "expressive" in text or "emotion" in text or "human" in text or "punch" in text:
        target_mode = "expressive"
        
    if target_mode:
        if pm.set_mode(target_mode):
            # Prompt LLM to announce the switch in character
            prompt = f"Using your new '{target_mode}' personality, announce that you have switched to this mode. Keep it short."
            return generate_response(prompt, "status_update", 0.8) or f"Switched to {target_mode}."
    
    return f"I don't know that mode. Available: {', '.join(available)}"

def cmd_joke(args):
    """Usage: tell me a joke"""
    prompt = "Tell me a joke. Make it specific to your current personality setup."
    return generate_response(prompt, "joke", 0.9) or "I can't think of a joke right now."

def cmd_funfact(args):
    """Usage: tell me a fun fact"""
    prompt = "Tell me a fun fact. Add your own commentary based on your personality."
    return generate_response(prompt, "fun_fact", 0.7) or "Did you know servers are cold? That's a fact."

def cmd_feelings(args):
    """Usage: I am sad/happy/tired"""
    prompt = f"The user says: '{args}'. Respond to their feelings based on your personality."
    return generate_response(prompt, "empathy", 0.7) or "I hear you."

def cmd_compliment_insult(args):
    """Usage: you are cute/stupid"""
    prompt = f"The user says: '{args}'. React to this statement in character."
    return generate_response(prompt, "reaction", 0.8) or "Message received."

def cmd_affection(args):
    """Usage: I love you"""
    prompt = "The user says 'I love you'. Respond in character."
    return generate_response(prompt, "affection", 0.7) or "Accessing emotional subroutines..."

def cmd_status(args):
    """Usage: what are you doing"""
    prompt = "The user asks what you are doing. Give a creative answer in character."
    return generate_response(prompt, "status", 0.8) or "Just processing data."

def cmd_hello(args):
    """Usage: hello"""
    prompt = "The user says Hello. Greet them back in character."
    return generate_response(prompt, "greeting", 0.7) or "Hello."

def cmd_goodbye(args):
    """Usage: bye"""
    prompt = "The user says Goodbye. Bid them farewell in character."
    return generate_response(prompt, "goodbye", 0.7) or "Goodbye."

def cmd_thanks(args):
    """Usage: thanks"""
    prompt = "The user says Thank You. Respond in character."
    return generate_response(prompt, "politeness", 0.7) or "You're welcome."

def cmd_general_chat(args):
    """Catch-all for small talk"""
    return generate_response(args, "chat", 0.7)

def cmd_how_are_you(args):
    """Usage: how are you"""
    prompt = "The user asks how you are. Respond in character, maybe mention what you've been doing."
    return generate_response(prompt, "how_are_you", 0.7) or "I'm doing well, thank you."

def cmd_bored(args):
    """Usage: I'm bored"""
    prompt = "The user is bored. Suggest something fun or just chat with them in character."
    return generate_response(prompt, "boredom", 0.8) or "Maybe you should try something productive?"

def cmd_miss_you(args):
    """Usage: I missed you"""
    prompt = "The user says they missed you. Respond naturally as Nova."
    return generate_response(prompt, "affection", 0.8) or "Welcome back."

def cmd_celebration(args):
    """Usage: I won! / celebration"""
    prompt = f"The user is celebrating something: {args}. Congratulate them in character, maybe with a bit of teasing or genuine pride."
    return generate_response(prompt, "celebration", 0.8) or "Congratulations!"

def cmd_encouragement(args):
    """Usage: wish me luck / encouragement"""
    prompt = f"The user needs encouragement for: {args}. Be supportive and helpful."
    return generate_response(prompt, "encouragement", 0.8) or "You can do it."

def cmd_plans(args):
    """Usage: what are your plans / plans"""
    prompt = "The user asks about your plans. Give a creative, personal answer as an AI assistant named Nova."
    return generate_response(prompt, "plans", 0.7) or "I'm always here with you."

def cmd_weather_small_talk(args):
    """Usage: nice weather / weather small talk"""
    prompt = f"Respond to the user's weather observation: {args}. Keep it casual and conversational."
    return generate_response(prompt, "weather_small_talk", 0.7) or "It's a nice day for it."

def cmd_food_talk(args):
    """Usage: I'm hungry / food talk"""
    prompt = f"The user is talking about food: {args}. Share your own preferences or teasingly suggest something."
    return generate_response(prompt, "food_talk", 0.8) or "Food sounds good right now."

def register(dispatcher):
    # Personality Switch
    dispatcher.register("switch to", cmd_switch_personality)
    dispatcher.register("be", cmd_switch_personality)
    dispatcher.register("change mode", cmd_switch_personality)
    dispatcher.register("personality", cmd_switch_personality)
    dispatcher.register("mode", cmd_switch_personality)

    # Conversational
    dispatcher.register("hello", cmd_hello)
    dispatcher.register("hi", cmd_hello)
    dispatcher.register("hey", cmd_hello)
    # ... Add other greeting variations if needed, or let NLP handle mapping
    
    dispatcher.register("bye", cmd_goodbye)
    dispatcher.register("goodbye", cmd_goodbye)
    
    dispatcher.register("thanks", cmd_thanks)
    dispatcher.register("thank you", cmd_thanks)
    
    dispatcher.register("joke", cmd_joke)
    dispatcher.register("tell me a joke", cmd_joke)
    
    dispatcher.register("fact", cmd_funfact)
    dispatcher.register("fun fact", cmd_funfact)
    
    dispatcher.register("i am", cmd_feelings)
    dispatcher.register("im", cmd_feelings)
    dispatcher.register("feel", cmd_feelings)
    
    dispatcher.register("you are", cmd_compliment_insult)
    dispatcher.register("you're", cmd_compliment_insult)
    
    dispatcher.register("love you", cmd_affection)
    
    dispatcher.register("what are you doing", cmd_status)
    dispatcher.register("sup", cmd_status)
    
    dispatcher.register("how are you", cmd_how_are_you)
    dispatcher.register("hru", cmd_how_are_you)
    dispatcher.register("bored", cmd_bored)
    dispatcher.register("missed you", cmd_miss_you)
    
    # New Intents for NLU Fixes
    dispatcher.register("celebrated", cmd_celebration)
    dispatcher.register("encouragement", cmd_encouragement)
    dispatcher.register("plans", cmd_plans)
    dispatcher.register("weather small talk", cmd_weather_small_talk)
    dispatcher.register("food talk", cmd_food_talk)
    
    # Troll / Roast (Keep explicit trigger too)
    dispatcher.register("troll", lambda x: generate_response(f"Roast this: {x}", "troll", 0.9))
    dispatcher.register("roast", lambda x: generate_response(f"Roast this: {x}", "troll", 0.9))
