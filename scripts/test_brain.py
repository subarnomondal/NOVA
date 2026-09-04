import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("Loading PersonalBrain...")
    from core.personal_brain import personal_brain
    
    print("\n--- Initial Profile State ---")
    print(f"Name: {personal_brain.get_name()}")
    
    # Let's temporarily disable strict_privacy for the test so we can see the output
    print("\n--- Forcing strict_privacy to False for test ---")
    personal_brain._profile.setdefault("preferences", {})["strict_privacy"] = False
    
    print("\n--- Simulating Conversation 1: Setting a goal ---")
    user_input = "I want to start going to the gym every morning"
    print(f"User: {user_input}")
    personal_brain.learn_from_exchange(user_input, "That's a great goal! I'll remind you.")
    
    print("\n--- Simulating Conversation 2: Logging a mood ---")
    user_input = "I am feeling super stressed about exams"
    print(f"User: {user_input}")
    personal_brain.learn_from_exchange(user_input, "Take a deep breath, you'll be fine.")
    
    print("\n--- Generating Rich Context for LLM ---")
    ctx = personal_brain.get_rich_context()
    print("=========================================")
    print(ctx)
    print("=========================================")
    
    print("\n--- Checking brain.json directly ---")
    with open("userdata/brain.json", "r") as f:
        data = json.load(f)
        print("Goals:", [g['title'] for g in data.get('goals', [])])
        print("Mood log:", [m['mood'] for m in data.get('mood_log', [])])
        print("Life events count:", len(data.get('life_events', [])))
        
    print("\n✅ Test Completed Successfully!")
except Exception as e:
    print(f"❌ Error during test: {e}")
