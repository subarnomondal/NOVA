"""
Text Correction Skill for NOVA
Allows users to ask NOVA to fix their spelling and grammar.
"""

import random

# Global reference to text corrector, set during registration
text_corrector = None

def cmd_correct_text(args):
    """Usage: correct this <text> or fix my grammar <text>"""
    if not text_corrector:
        return "I'm sorry, my text correction engine isn't initialized yet. 🛠️"
        
    # Extract the text to be corrected
    text = args.lower()
    
    triggers = [
        "correct this", "fix my grammar", "spellcheck", "fix typos in", 
        "make it professional", "correct my text", "fix this"
    ]
    
    target_text = args
    for trigger in triggers:
        if trigger in text:
            # Case insensitive split to keep original casing in the target text
            import re
            parts = re.split(re.escape(trigger), args, flags=re.IGNORECASE, maxsplit=1)
            if len(parts) > 1:
                target_text = parts[1].strip()
            break
            
    if not target_text or target_text == args:
        # If no clear text follows the trigger, use the whole thing but strip common intro words
        target_text = args.strip()
    
    if not target_text:
        return "What would you like me to correct? Just say 'correct this' followed by your text! ✍️"

    # Determine mode based on user's query
    mode = "balanced"
    if "professional" in text or "formal" in text:
        mode = "professional"
    elif "spelling" in text or "typo" in text:
        mode = "spelling"
    elif "grammar" in text:
        mode = "grammar"
        
    print(f"✍️ Correcting text (mode: {mode}): {target_text[:50]}...")
    
    result = text_corrector.correct(target_text, mode=mode)
    
    if not result.get("is_changed"):
        return random.choice([
            "Your text looks perfect already! I didn't find any errors. ✨",
            "I couldn't find anything to fix. It looks great as it is! 👍",
            "Everything seems correct in that sentence! Good job. 😊"
        ])
        
    corrected = result.get("corrected")
    
    intros = [
        "Here is the corrected version of your text:",
        "I've polished it up for you:",
        "Here it is, fixed and ready:",
        "I've made some improvements to your text:"
    ]
    
    return f"{random.choice(intros)}\n\n> {corrected}\n\nHope that helps! ✨"

def register(dispatcher, corrector_instance=None):
    global text_corrector
    text_corrector = corrector_instance
    
    dispatcher.register("correct this", cmd_correct_text)
    dispatcher.register("fix my grammar", cmd_correct_text)
    dispatcher.register("spellcheck", cmd_correct_text)
    dispatcher.register("fix typos", cmd_correct_text)
    dispatcher.register("make it professional", cmd_correct_text)
    dispatcher.register("fix this", cmd_correct_text)
    
    # Register dictionary commands
    dispatcher.register("add word", cmd_add_word)
    dispatcher.register("remember spelling", cmd_add_word)

def cmd_add_word(args):
    """Usage: add word <word>"""
    if not text_corrector:
        return "System not ready."
        
    word = args.replace("add word", "").replace("remember spelling", "").strip()
    # Remove "to dictionary" if present
    word = word.replace("to dictionary", "").strip()
    
    if not word:
        return "Which word should I remember?"
        
    if text_corrector.add_word(word):
        return f"Got it! I'll remember the spelling for '{word}'. 📝"
    else:
        return f"I already know '{word}'! ✨"
