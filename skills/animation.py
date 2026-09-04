import random

VALID_EMOTIONS = ['happy', 'joy', 'angry', 'sorrow', 'sad', 'relaxed', 'thinking', 'surprised', 'sleep', 'neutral', 'success', 'error', 'dance', 'wave', 'shy', 'proud']

def cmd_animate(args):
    """
    Usage: be happy / act angry / get surprised
    Triggers a specific VTuber animation directly.
    """
    args = args.lower().strip()
    
    # Try to find which emotion the user requested
    target_emotion = "neutral"
    for em in VALID_EMOTIONS:
        if em in args:
            target_emotion = em
            break
            
    if target_emotion == "neutral" and args:
        # If they just said the raw word without standard sentence
        if args in VALID_EMOTIONS:
            target_emotion = args
            
    responses = [
        f"Okay! I'm showing {target_emotion} now.",
        f"Executing {target_emotion} protocol.",
        f"How does this look?",
        f"Right away! Switching to {target_emotion}."
    ]
    
    return {
        "response": random.choice(responses),
        "emotion": target_emotion
    }

def register(dispatcher):
    # Register the direct triggers
    dispatcher.register("act", cmd_animate)
    dispatcher.register("be", cmd_animate)
    dispatcher.register("get", cmd_animate)
    dispatcher.register("show emotion", cmd_animate)
    dispatcher.register("do a pose", cmd_animate)
    
    # Register direct emotion keywords as a fallback
    for em in VALID_EMOTIONS:
        dispatcher.register(f"be {em}", cmd_animate)
        dispatcher.register(f"act {em}", cmd_animate)
        dispatcher.register(f"look {em}", cmd_animate)
