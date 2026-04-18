import sys
import os

# Add project root to path for core imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
from core.nlp_processor import NLUProcessor

# Configuration
SKILLS_DIR = "skills"
OUTPUT_FILE = os.path.join("userdata", "datasets", "nova_skills_dataset.jsonl")

def generate_dataset():
    nlu = NLUProcessor()
    dataset = []
    
    print(f"🔍 Scanning {SKILLS_DIR} for commands...")
    
    # 1. Map intents to triggers
    command_examples = {
        "play": ["play some music", "can you play a song", "drop a beat", "start the music"],
        "time": ["what time is it", "current time", "what's the clock", "time please"],
        "weather": ["how is the weather", "current temperature", "will it rain", "weather update"],
        "correct this": ["correct this text", "fix my grammar", "spellcheck this", "improve my sentence"],
        "calculate": ["calculate 5 plus 5", "solve 2x + 5 = 10", "square root of 144", "compute math"]
    }
    
    # 2. Synthesize commands from register() calls in skills
    skill_commands = []
    for filename in os.listdir(SKILLS_DIR):
        if filename.endswith(".py"):
            path = os.path.join(SKILLS_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                # Find dispatcher.register("cmd", ...)
                matches = re.findall(r'dispatcher\.register\(["\'](.+?)["\']', content)
                skill_commands.extend(matches)
    
    print(f"✅ Found {len(skill_commands)} unique command triggers.")
    
    # 3. Create training pairs
    for cmd in skill_commands:
        # Example 1: Direct Command
        dataset.append({
            "messages": [
                {"role": "user", "content": f"{cmd} please"},
                {"role": "assistant", "content": f"[SKILL] {cmd} [/SKILL]"}
            ]
        })
        
        # Example 2: Conversation Style
        dataset.append({
            "messages": [
                {"role": "user", "content": f"Hey Nova, can you {cmd}?"},
                {"role": "assistant", "content": f"Of course! [SKILL] {cmd} [/SKILL]"}
            ]
        })

    # 4. Add Automation Examples (Python/Shell)
    dataset.append({
        "messages": [
            {"role": "user", "content": "Write a python script to print hello world"},
            {"role": "assistant", "content": "[SCRIPT]\nprint('Hello World')\n[/SCRIPT]"}
        ]
    })
    
    dataset.append({
        "messages": [
            {"role": "user", "content": "List all files in current directory"},
            {"role": "assistant", "content": "[CMD] dir [/CMD]"}
        ]
    })

    # Ensure datasets directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in dataset:
            f.write(json.dumps(entry) + "\n")
            
    print(f"✨ Dataset generated: {OUTPUT_FILE} ({len(dataset)} examples)")

if __name__ == "__main__":
    generate_dataset()
