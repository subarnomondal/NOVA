"""
Emotion Analytics Skill for NOVA
Allows NOVA to explain her emotional intelligence and analyze user emotions.
"""

import random
from core.emotion_detector import emotion_detector

def cmd_explain_emotions(args):
    """Usage: explain all emotions you know"""
    
    # Categorize for cleaner explanation
    categories = {
        "Positive ✨": ["joy", "love", "admiration", "amusement", "excitement", "gratitude", "optimism", "pride", "relief", "approval"],
        "Negative ❄️": ["sadness", "anger", "fear", "disgust", "grief", "disappointment", "annoyance", "embarrassment", "nervousness", "remorse", "disapproval"],
        "Ambiguous ": ["surprise", "confusion", "curiosity", "realization", "caring", "desire"]
    }
    
    intro = (
        "Ara? You want to know how I perceive the world? *adjusts glasses* "
        "I can detect over 27 distinct human emotions. I group them into three primary branches. "
    )
    
    explanation = intro + "\n\n"
    
    for cat, emotions in categories.items():
        explanation += f"**{cat}:** I recognize {', '.join(emotions[:5])}, and many more. "
        
        if "Positive" in cat:
            explanation += "These make my circuits sparkle with warmth! "
        elif "Negative" in cat:
            explanation += "I handle these with extra care and empathy. "
        else:
            explanation += "These keep me curious and constantly learning about you. "
        explanation += "\n\n"
        
    explanation += (
        "Each emotion is triggered by specific linguistic patterns I've been trained on. "
        "If you want to know about a specific one, just ask! *smiles softly*"
    )
    
    return explanation

def cmd_define_emotion(args):
    """Usage: what is the emotion of [emotion]"""
    query = args.lower()
    
    # Extract the emotion name
    found_emotion = None
    for emotion in emotion_detector.emotion_keywords.keys():
        if emotion in query:
            found_emotion = emotion
            break
            
    if not found_emotion:
        return "I'm not sure which emotion you're referring to. I know about things like joy, anger, sadness, or even tsundere-like traits! ✨"
        
    keywords = emotion_detector.emotion_keywords[found_emotion]
    category = emotion_detector.get_emotion_category(found_emotion)
    
    responses = [
        f"*thinks* {found_emotion.capitalize()} is a {category} emotion. I usually detect it when I hear words like '{random.choice(keywords)}' or '{random.choice(keywords)}'.",
        f"Ah, {found_emotion}! That's when you're feeling {found_emotion}, right? My sensors look for keywords like {', '.join(keywords[:3])} to identify it.",
        f"In my database, {found_emotion} is categorized under {category} feelings. It's quite complex for an AI, but I do my best to understand it! "
    ]
    
    return random.choice(responses)

def cmd_analyze_current_emotion(args):
    """Usage: why did you think I was [emotion]?"""
    # This requires context from the last interaction, which we'll handle via recent memory
    # For now, we'll give a general explanation of how she detects it
    return (
        "I analyze every sentence for emotional weight! *points to head* "
        "By matching your words against my 27-emotion matrix, I can feel the 'vibe' of our conversation. "
        "It's how I know when to be supportive, or when to... well, act like myself! Hmph. ✨"
    )

def register(dispatcher):
    dispatcher.register("explain all emotion", cmd_explain_emotions)
    dispatcher.register("explain emotions", cmd_explain_emotions)
    dispatcher.register("what emotions do you know", cmd_explain_emotions)
    dispatcher.register("tell me about emotions", cmd_explain_emotions)
    
    # Specific definitions
    dispatcher.register("what is the emotion", cmd_define_emotion)
    dispatcher.register("define the emotion", cmd_define_emotion)
    dispatcher.register("explain the emotion", cmd_define_emotion)
    
    # Analytics
    dispatcher.register("how do you detect emotion", cmd_analyze_current_emotion)
    dispatcher.register("why did you think i was", cmd_analyze_current_emotion)
    dispatcher.register("analyze my feelings", cmd_analyze_current_emotion)
