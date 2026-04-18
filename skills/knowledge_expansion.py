"""
Knowledge Expansion Skill
Enables Nova to learn new facts from the web (Wiki/DDG)
"""

import json
from duckduckgo_search import DDGS
from core.domain_knowledge import DomainKnowledge

# Local instance to write to file
knowledge_db = DomainKnowledge()

def fetch_summary(topic):
    """Fetch a short summary of a topic using DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            # Search for "what is [topic]" or just topic
            query = f"what is {topic} wikipedia"
            results = list(ddgs.text(query, max_results=2))
            
            if results:
                # Get the first good result/snippet
                for res in results:
                    body = res.get('body', '')
                    if body and len(body) > 50:
                        return body
    except Exception as e:
        print(f"Search error: {e}")
    return None

def cmd_learn_topic(args):
    """
    Learn about a specific topic from the web
    Usage: learn about [topic]
    Example: learn about Quantum Physics
    """
    # Parse topic
    import re
    match = re.search(r'learn\s+(?:about\s+)?(.+)', args, re.IGNORECASE)
    if not match:
        return "⚠️ What should I learn about? Usage: 'learn about [topic]'"
    
    topic = match.group(1).strip()
    
    # 1. Check if we already know it
    existing = knowledge_db.get_knowledge(topic)
    if existing:
        return f"🧠 I already know about {topic}: {existing[:100]}..."
        
    # 2. Search Web
    summary = fetch_summary(topic)
    
    if not summary:
        return f"❌ I couldn't find good information on '{topic}' right now."
        
    # 3. Add to Knowledge Base
    # Determine domain (simple heuristic)
    domain = "general"
    if any(w in summary.lower() for w in ['computer', 'software', 'technology', 'robot']):
        domain = "technology"
    elif any(w in summary.lower() for w in ['science', 'physics', 'biology', 'chemistry']):
        domain = "science"
    elif any(w in summary.lower() for w in ['history', 'war', 'year', 'century']):
        domain = "history"
        
    knowledge_db.add_knowledge(domain, topic, summary)
    
    return f"📚 Learned new fact about **{topic}**!\n\"{summary}\"\n_(Restart me to use this in conversation!)_"

def register(dispatcher):
    dispatcher.register("learn about", cmd_learn_topic)
    dispatcher.register("research", cmd_learn_topic)
