"""
Online Training Skill for NOVA
Enables importing conversation datasets from online sources (specifically ChatterBot corpus)
"""

import requests
import yaml
import time
from core.conversation_trainer import ConversationTrainer

# Initialize trainer
trainer = ConversationTrainer()

# Base URL for ChatterBot corpus
CORPUS_BASE_URL = "https://raw.githubusercontent.com/gunthercox/chatterbot-corpus/master/chatterbot_corpus/data/english/"

AVAILABLE_TOPICS = [
    "ai", "botprofile", "computers", "conversations", "emotion", 
    "food", "gossip", "greetings", "health", "history", "humor", 
    "literature", "money", "movies", "politics", "psychology", 
    "science", "sports", "trivia"
]

def cmd_list_datasets(args):
    """List available online datasets"""
    topics_list = ", ".join(AVAILABLE_TOPICS)
    return f"""📚 **Available Training Topics**

You can import knowledge on these topics:
{topics_list}

**Usage:** `import dataset [topic]` or `import dataset all`"""

def fetch_and_train_topic(topic):
    """Fetch a specific topic and train Nova"""
    url = f"{CORPUS_BASE_URL}{topic}.yml"
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = yaml.safe_load(response.text)
        conversations = data.get('conversations', [])
        
        count = 0
        for conv in conversations:
            if len(conv) >= 2:
                # Handle standard [trigger, response] pairs
                trigger = conv[0]
                response = conv[1]
                
                # Teach the main pair
                trainer.teach_response(trigger, response, category=topic, mood="neutral")
                count += 1
                
                # If there are more items, they are likely alternating conversation flow
                # For simplicity, we just take the first pair, or chain them if we had advanced flow training
                # But conversation_trainer mainly supports single turn pairs for now roughly
        
        return count, None
    except Exception as e:
        return 0, str(e)

def cmd_import_dataset(args):
    """
    Import a dataset from online
    Usage: import dataset [topic]
    """
    args = args.lower().replace("import dataset", "").strip()
    
    if not args:
        return cmd_list_datasets(args)
    
    topics_to_import = []
    
    if args == "all":
        topics_to_import = AVAILABLE_TOPICS
        return "⚠️ Importing ALL datasets might take a while and flood your database. Are you sure? Say 'import dataset all confirm' to proceed."
    elif args == "all confirm":
        topics_to_import = AVAILABLE_TOPICS
    elif args == "social":
        # Import social-media style topics
        topics_to_import = ["gossip", "conversations", "humor", "movies", "sports", "emotion"]
        # Note: We proceed to loop below
    elif args in AVAILABLE_TOPICS:
        topics_to_import = [args]
    else:
        return f"❌ Unknown topic: '{args}'. Available topics: {', '.join(AVAILABLE_TOPICS)}\n\n💡 Tip: Try 'import dataset social' for a social media pack!"
    
    total_learned = 0
    results = []
    
    msg = f"⬇️ Starting import for: {', '.join(topics_to_import)}...\n"
    
    for topic in topics_to_import:
        count, error = fetch_and_train_topic(topic)
        if error:
            results.append(f"❌ {topic}: Failed ({error})")
        else:
            results.append(f"✅ {topic}: Learned {count} patterns")
            total_learned += count
        
        # Rate limiting slightly
        time.sleep(0.1)
    
    summary = "\n".join(results)
    return f"{msg}\n{summary}\n\n🎉 Total new patterns learned: {total_learned}"

def register(dispatcher):
    """Register online training commands"""
    dispatcher.register("import dataset", cmd_import_dataset)
    dispatcher.register("list datasets", cmd_list_datasets)
