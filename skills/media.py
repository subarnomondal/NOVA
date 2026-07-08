"""
Media Skill for Nova
Handles music playback (YouTube, Spotify, YT Music) and media controls with persona.
Consolidates logic from previous media and automation skills.
"""
import os
import webbrowser
import random
import requests
import re
import pyautogui
import time
from ytmusicapi import YTMusic

def get_yt_client():
    """Helper to get YTMusic client (authenticated if possible)"""
    try:
        if os.path.exists("oauth.json"):
            return YTMusic("oauth.json")
        return YTMusic()
    except Exception:
        return None

def get_music_mood(query):
    """Simple mood classifier for music queries"""
    q = query.lower()
    
    moods = {
        'energetic': ['gym', 'workout', 'power', 'aggressive', 'hard', 'rock', 'metal', 'hype', 'energetic'],
        'happy': ['happy', 'upbeat', 'party', 'dance', 'fun', 'joy', 'celebrate'],
        'sad': ['sad', 'lonely', 'breakup', 'crying', 'depressing', 'melancholy', 'heartbreak'],
        'chill': ['chill', 'relax', 'study', 'lofi', 'calm', 'soft', 'peaceful', 'sleep'],
        'romantic': ['romantic', 'love', 'date', 'sweet', 'soft', 'couple']
    }
    
    for mood, keywords in moods.items():
        if any(k in q for k in keywords):
            return mood
    return None

def get_emotional_reaction(mood):
    """Returns a narrative action and response style based on mood"""
    reactions = {
        'happy': ("*smiles brightly*", "Yay! I love upbeat songs. Let's play this! ✨"),
        'sad': ("*looks sympathetic*", "Aww, are you feeling a bit down? Here's some music to help you through it. "),
        'chill': ("*relaxes*", "That sounds like a great idea. Let's chill for a bit. "),
        'energetic': ("*gets pumped*", "Let's get energized! This is going to be awesome! ⚡"),
        'romantic': ("*smiles warmly*", "A romantic choice. Let me put it on for you. ")
    }
    return reactions.get(mood, ("*smiles*", "Sure thing! Let me play that for you! ✨"))

def find_local_music(query):
    """Search for music files in standard Windows music directories"""
    music_dirs = [
        os.path.join(os.path.expanduser("~"), "Music"),
        os.path.join(os.path.expanduser("~"), "Downloads")
    ]
    
    clean_query = query.lower().strip()
    found_files = []
    
    extensions = ('.mp3', '.m4a', '.wav', '.flac')
    
    for d in music_dirs:
        if not os.path.exists(d): continue
        for root, dirs, files in os.walk(d):
            # Limit depth for performance
            if root.count(os.sep) - d.count(os.sep) > 2: dirs[:] = []
            
            for file in files:
                if file.lower().endswith(extensions):
                    if clean_query in file.lower():
                        found_files.append(os.path.join(root, file))
    
    return found_files

def get_nova_taste(query):
    """Nova's personal music preferences"""
    q = query.lower()
    
    # Check for Bengali music
    if any(word in q for word in ["bengali", "bangla", "rabindra", "arijit"]):
        return ("*smiles warmly*", "Bengali music? Excellent choice! Local vibes are the best. ✨")
    
    if any(word in q for word in ["miku", "yoasobi"]):
        return ("*smiles*", "J-Pop! Great choice. Let's listen! ")

    return None

def cmd_play(args):
    """Usage: play <query> or play music <query>"""
    try:
        # Extract query
        query_raw = args.lower()
        query = query_raw
        for prefix in ["play music", "play song", "play video", "play"]:
            if query_raw.startswith(prefix):
                query = query_raw[len(prefix):].strip()
                break
        
        # --- NEW: User Taste Discovery via LTM ---
        if query in ["my taste", "something i like", "my favorites", "some music i like", "my favorite music"]:
            try:
                from core.ltm_manager import LTMManager
                ltm = LTMManager()
                # Gather possible music interests
                taste_clues = []
                for cat in ["artist", "band", "genre", "singer"]:
                    fact = ltm.get_fact(cat)
                    if fact: taste_clues.append(fact)
                for item in ltm.facts.get("interest", []):
                    if "music" in item["value"].lower():
                        taste_clues.append(item["value"])
                
                if taste_clues:
                    query = random.choice(taste_clues)
                    print(f" LTM Taste selected: {query}")
                else:
                    # Fallback if no taste exists in LTM yet
                    query = "lofi chill beats"
            except Exception as e:
                print(f"LTM fetch error: {e}")
                query = "lofi chill beats"

        if not query:
            # AGI Context Support: Check if a previous step gave us a query
            from core.agi_context import agi_context
            query = agi_context.get_query()
            
            if not query:
                if query_raw in ["play", "pause", "resume"]:
                    # Media toggle fallback
                    print("⏯️ Toggling media playback...")
                    try:
                        import pyautogui
                        pyautogui.press("playpause")
                    except Exception:
                        pass
                    return "Toggled media playback. ⏯️"
                else:
                    # e.g., user just said "play music" or "play song"
                    query = "lofi chill beats"            
        # --- NEW: LOCAL FILE SEARCH ---
        if "local" in query_raw or "pc" in query_raw or "computer" in query_raw:
            clean_query = query.replace("local", "").replace("pc", "").replace("on", "").strip()
            print(f" Searching local files for: {clean_query}")
            local_files = find_local_music(clean_query)
            if local_files:
                target = local_files[0]
                print(f" Playing local file: {target}")
                os.startfile(target)
                return f"*smiles* Found it on your PC! Playing '{os.path.basename(target)}' for you. "

        # Persona & Mood Check
        special_reaction = get_nova_taste(query)
        if special_reaction:
            action, intro = special_reaction
        else:
            mood = get_music_mood(query)
            action, intro = get_emotional_reaction(mood)
            
        # Platform Routing
        if "spotify" in query:
            clean_query = query.replace("on spotify", "").replace("spotify", "").strip()
            print(f" Opening Spotify: {clean_query}")
            os.system(f"start spotify:search:{clean_query}")
        
            return f"{action} {intro}\nOpening Spotify for '{clean_query}'! "
            
        # YT Music Search & Play
        client = get_yt_client()
        clean_query = query.replace("on youtube music", "").replace("youtube music", "").replace("yt music", "").replace("on yt music", "").strip()
        
        print(f" Searching YT Music for: {clean_query}")
        
        search_results = []
        if client:
            try:
                # Search for songs
                yt_results = client.search(clean_query, filter="songs", limit=5)
                if yt_results:
                    for res in yt_results:
                        search_results.append({
                            "title": res.get("title"),
                            "artist": ", ".join([a.get("name") for a in res.get("artists", [])]),
                            "album": res.get("album", {}).get("name") if res.get("album") else "Unknown",
                            "videoId": res.get("videoId"),
                            "thumbnail": res.get("thumbnails", [{}])[-1].get("url")
                        })
                    
                    # If it's a direct play request and we have a strong match, just play it
                    best_match = search_results[0]
                    best_url = f"https://music.youtube.com/watch?v={best_match['videoId']}"
                    
                    print(f" Best YT Music Match: {best_match['title']} by {best_match['artist']}")
                    
                    # Stop currently playing media before opening a new song
                    try:
                        time.sleep(0.3)  # Brief pause to let the old track stop
                    except Exception:
                        pass
                    
                    from skills.browser_agent import agent
                    agent.open_url(best_url)
                    
                    # Return rich data for the UI to render cards if it supports it
                    return {
                        "response": f"{action} {intro}\nPlaying **{best_match['title']}** by {best_match['artist']}! ",
                        "data": {
                            "type": "music_results",
                            "results": search_results,
                            "playing": best_match
                        }
                    }
            except Exception as yt_err:
                print(f"⚠️ YT Music API error: {yt_err}")

        # Fallback to DDGS if YTMusic fails or client not available
        print(f" Fallback to DDGS Search: {clean_query}")
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.videos(f"{clean_query} song youtube", max_results=3))
                if results:
                    best_url = results[0].get('content') or results[0].get('embed_url') or results[0].get('url')
                    if best_url:
                        # Stop current media before playing new
                        try:
                            time.sleep(0.3)
                        except Exception:
                            pass
                        from skills.browser_agent import agent
                        agent.open_url(best_url)
                        return f"{action} {intro}\nFinding '{clean_query}' for you on YouTube! "
        except Exception as search_err:
            print(f"⚠️ Search fallback snag: {search_err}")

        # Final Fallback — stop current media first
        try:
            time.sleep(0.3)
        except Exception:
            pass
        from skills.browser_agent import agent
        agent.open_url(f"https://music.youtube.com/search?q={clean_query}")
        return f"{action} {intro}\nOpening search results for '{clean_query}'! "

    except Exception as e:
        return f"Oops, I couldn't play that. Error: {e}"

def cmd_my_music(args):
    """Usage: my music <playlist name> or play playlist <name>"""
    try:
        # Check for ytmusicapi client
        client = get_yt_client()

        if not client:
            return "I can't access your library yet! Please run `python setup_ytmusic.py` to sync your account first. "
            
        query = args.replace("my music", "").replace("playlist", "").replace("play", "").strip()
        if not query:
            return "Which playlist should I play, Darling? "
            
        results = client.search(query, filter="playlists")
        if results:
            target = results[0]
            playlist_id = target['browseId']
            title = target['title']
            from skills.browser_agent import agent
            agent.open_url(f"https://music.youtube.com/playlist?list={playlist_id}")
        
            return f"Found '{title}' in your library! Playing it now. "
        else:
        
            return f"I couldn't find a playlist called '{query}' in your account. "
            
    except Exception as e:
        return f"Error accessing your music: {e}"

def register(dispatcher):
    """Register all media commands"""
    # Core play commands
    dispatcher.register("play", cmd_play)
    dispatcher.register("play music", cmd_play)
    dispatcher.register("play song", cmd_play)
    dispatcher.register("play video", cmd_play)
    
    # Specific Platforms
    dispatcher.register("ytmusic", cmd_play)
    dispatcher.register("youtube music", cmd_play)
    dispatcher.register("spotify", cmd_play)
    
    # Library
    dispatcher.register("my music", cmd_my_music)
    dispatcher.register("my playlist", cmd_my_music)
    dispatcher.register("play playlist", cmd_my_music)
