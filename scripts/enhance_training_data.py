import json
import os

def enhance_dataset(input_file, output_file):
    new_examples = [
        # Multi-Intent Examples
        {"messages": [{"role": "user", "content": "Play some music and then lock the computer"}, 
                      {"role": "assistant", "content": "<thought>The user wants to play music and lock the PC. I will trigger the music play skill first, then the system lock skill.</thought>[SKILL] play music [/SKILL] [SKILL] lock computer [/SKILL]"}]},
        {"messages": [{"role": "user", "content": "What's the weather like and summarize my recent emails"}, 
                      {"role": "assistant", "content": "<thought>I need to check the weather and then summarize emails. I'll use the weather skill and then the email list/summary skill.</thought>[SKILL] weather [/SKILL] [SKILL] list emails [/SKILL]"}]},
        {"messages": [{"role": "user", "content": "Set a reminder for my meeting at 5 and tell me a joke"}, 
                      {"role": "assistant", "content": "<thought>Setting a reminder and then telling a joke to lighten the mood.</thought>[SKILL] remind meeting at 5 [/SKILL] [SKILL] joke [/SKILL]"}]},
        
        # Contextual Reasoning Examples
        {"messages": [{"role": "user", "content": "What should I wear today?"}, 
                      {"role": "assistant", "content": "<thought>To answer this, I need the current weather. I'll also check if the user has any preferred styles in their profile.</thought>[SKILL] weather [/SKILL] [SKILL] user profile [/SKILL]"}]},
        {"messages": [{"role": "user", "content": "Remind me to buy eggs when I'm near the store"}, 
                      {"role": "assistant", "content": "<thought>This requires location awareness. I'll set a geofenced reminder if supported, otherwise a standard one with a location note.</thought>[SKILL] remind buy eggs at store [/SKILL]"}]},
        
        # Proactive Engagement Examples
        {"messages": [{"role": "user", "content": "I'm feeling a bit lonely today"}, 
                      {"role": "assistant", "content": "<thought>The user is feeling low. I should respond with empathy and suggest an activity like listening to music or a walk.</thought>I'm sorry to hear that. *hugs* I'm here for you. Would you like me to play some of your favorite music or maybe we can just chat? [SKILL] suggest music [/SKILL]"}]},
        {"messages": [{"role": "user", "content": "It's raining outside"}, 
                      {"role": "assistant", "content": "<thought>Rain detected. I should proactively suggest checking for a scheduled outdoor task or offer to play rainy-day music.</thought>It sounds cozy! Do you have any plans for today that might be affected, or should I play some relaxing rainy-day music? [SKILL] check schedule [/SKILL]"}]},
        
        # Complex Automation Examples
        {"messages": [{"role": "user", "content": "If it rains tomorrow, remind me to take an umbrella"}, 
                      {"role": "assistant", "content": "<thought>This is a conditional automation. I need to check the forecast and then set a reminder.</thought>[SKILL] forecast [/SKILL] [SKILL] remind take umbrella if rain [/SKILL]"}]},
    ]

    # Load existing if exists
    existing_data = []
    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    existing_data.append(json.loads(line))
    
    # Avoid duplicates (simple check)
    existing_outputs = {json.dumps(ex['messages'][-1]['content']) for ex in existing_data}
    
    count = 0
    with open(output_file, 'a', encoding='utf-8') as f:
        for ex in new_examples:
            if json.dumps(ex['messages'][-1]['content']) not in existing_outputs:
                f.write(json.dumps(ex) + '\n')
                count += 1
                
    print(f"✅ Successfully added {count} new complex reasoning examples to {output_file}")

if __name__ == "__main__":
    dataset_path = os.path.join("userdata", "datasets", "nova_skills_dataset.jsonl")
    enhance_dataset(dataset_path, dataset_path)
