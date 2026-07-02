"""
Web Search Skill for Nova
Allows Nova to search the web and provide answers
"""

from duckduckgo_search import DDGS
import logging

# Initialize knowledge base for learning
from core.domain_knowledge import DomainKnowledge

# Initialize knowledge base for learning
knowledge = DomainKnowledge()

def cmd_learn(args):
    """Usage: learn that <fact> or remember that <fact>"""
    try:
        # Expected format: "learn that [topic] is [info]" or "remember that [topic] is [info]"
        text = args.lower()
        
        # Remove trigger words
        for trigger in ["learn that", "remember that", "know that", "save that"]:
            if trigger in text:
                text = text.split(trigger, 1)[1].strip()
                break
        
        if " is " not in text:
            return "I need to know *what* to learn! Try saying 'Learn that the WiFi password is 1234'. 🧠"
            
        parts = text.split(" is ", 1)
        topic = parts[0].strip()
        info = parts[1].strip()
        
        if not topic or not info:
             return "I didn't catch that. Try 'Learn that [Topic] is [Value]'. 🧠"
             
        # Save to knowledge base
        knowledge.add_knowledge("user_taught", topic, info)
        
        import random
        responses = [
            f"Got it! I've learned that {topic} is {info}. 🧠",
            f"Noted! {topic} = {info}. Saved to memory! 💾",
            f"Okay, I'll remember that {topic} is {info}. ✨"
        ]
        return random.choice(responses)
        
    except Exception as e:
        return f"Oops, I couldn't learn that. Error: {e}"

def cmd_advanced_search(args):
    """
    Advanced search for the AI agent loop.
    Returns structured data for reasoning.
    """
    query = args.replace("advanced search", "").replace("search", "").strip()
    if not query: return "ERROR: No search query provided."
    
    print(f"🌐 Performing Advanced Web Search: {query}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='us-en', max_results=8))
            
        if not results:
            return "OBSERVATION: No results found for this query."
            
        # Format as useful structured text for the LLM
        obs = f"FOUND {len(results)} RELEVANT SNIPPETS:\n\n"
        for i, r in enumerate(results, 1):
            obs += f"SOURCE {i}: {r.get('title')}\nURL: {r.get('href')}\nSNIPPET: {r.get('body')}\n\n"
            
        return obs
    except Exception as e:
        return f"ERROR [SEARCH_FAILURE]: {e}"

def get_favicon(url):
    """Helper to generate a favicon URL from a domain/URL"""
    from urllib.parse import urlparse
    try:
        domain = urlparse(url).netloc
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
    except:
        return None

def cmd_search(args):
    """Usage: search <query> or google <query>"""
    try:
        query = args.lower().replace("search", "").replace("google", "").replace("find", "").strip()
        
        if not query:
            return "What would you like me to look up for you? I'm ready to search! 🔍"
            
        kb_result = knowledge.search_knowledge(query)
        if kb_result and kb_result['confidence'] > 0.7:
            return kb_result['facts'][0]['information']
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='us-en', max_results=5))
        
        if not results:
            return f"Hmm, I couldn't find much about '{query}'."
        
        # Prepare structured data for the frontend
        search_data = []
        for r in results[:3]:
            href = r.get('href', '#')
            search_data.append({
                "title": r.get('title', 'No title'),
                "url": href,
                "snippet": r.get('body', ''),
                "favicon": get_favicon(href)
            })
            
        response = f"I found several relevant pieces of information for '{query}':\n\n"
        for i, r in enumerate(search_data, 1):
             snippet = r['snippet'] if r['snippet'] else ""
             response += f"{i}. **{r['title']}**\n   {snippet[:200]}...\n\n"

        return {
            "response": response,
            "data": {
                "type": "search_results",
                "query": query,
                "results": search_data
            }
        }
        
    except Exception as e:
        return f"Oops, I ran into a little hiccup while searching: {e}"

def cmd_news(args):
    """Usage: news or news about <topic>"""
    try:
        query = args.lower().replace("news", "").replace("latest", "").replace("about", "").replace("on", "").strip()
        if not query: query = "World News"
        
        with DDGS() as ddgs:
            results = list(ddgs.news(query, region='wt-wt', max_results=6))
                
        if not results:
            return f"I couldn't find any recent news headlines about '{query}'. 📰"
        
        news_data = []
        for item in results:
            url = item.get('url', '#')
            news_data.append({
                "title": item.get('title'),
                "source": item.get('source', 'Top Source'),
                "url": url,
                "favicon": get_favicon(url)
            })
            
        response = f"📰 **Latest News Report: {query.title()}**\n\n"
        for i, r in enumerate(news_data[:3], 1):
            response += f"{i}. **{r['title']}**\n   ◈ {r['source']}\n\n"

        return {
            "response": response,
            "data": {
                "type": "news_results",
                "query": query,
                "results": news_data
            }
        }
        
    except Exception as e:
        print(f"News Skill Error: {e}")
        return f"I encountered a glitch while fetching the news. 🗞️ Let me know if you want me to try again!"

def register(dispatcher):
    dispatcher.register("search", cmd_search)
    dispatcher.register("advanced search", cmd_advanced_search)
    dispatcher.register("google", cmd_search)
    dispatcher.register("find", cmd_search)
    dispatcher.register("look up", cmd_search)
    dispatcher.register("define", cmd_search)
    dispatcher.register("what is", cmd_search)
    dispatcher.register("who is", cmd_search)
    dispatcher.register("news", cmd_news)
    dispatcher.register("latest news", cmd_news)
    dispatcher.register("headlines", cmd_news)
    
    # Learning commands
    dispatcher.register("learn that", cmd_learn)
    dispatcher.register("remember that", cmd_learn)
    dispatcher.register("know that", cmd_learn)
    dispatcher.register("save that", cmd_learn)
