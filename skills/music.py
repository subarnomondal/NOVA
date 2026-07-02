"""
Music & Song Intelligence Skill for Nova
Handles song identification, lyrics, artist info, and trending Indian music.
"""

from duckduckgo_search import DDGS
import random
import re
import warnings
import subprocess
import os

# Suppress the ddgs rename warning specifically
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*renamed to ddgs.*")

def _fetch_itunes_metadata(query, entity="song"):
    """Helper to fetch structured metadata from iTunes Search API."""
    import requests
    try:
        url = f"https://itunes.apple.com/search?term={query}&media=music&entity={entity}&limit=1"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                return data['results'][0]
    except Exception as e:
        print(f"iTunes API Error: {e}")
    return None

def cmd_music_info(args):
    """Usage: music info <song/artist> or tell me about the song <name>"""
    query = args.lower().replace("music info", "").replace("tell me about the song", "").replace("who sang", "").replace("details of", "").strip()
    
    if not query:
        return "Which song or artist should I look up for you? I'm ready to dive into the music world! "

    print(f" Music Search (iTunes API): {query}")
    metadata = _fetch_itunes_metadata(query)

    if metadata:
        artist = metadata.get('artistName', 'Unknown Artist')
        track = metadata.get('trackName', query.title())
        album = metadata.get('collectionName', 'Unknown Album')
        genre = metadata.get('primaryGenreName', 'Music')
        release_date = metadata.get('releaseDate', '')
        year = release_date[:4] if release_date else 'N/A'
        view_url = metadata.get('trackViewUrl', '#')

        response = f"###  Nova Music Report: **{track}**\n\n"
        response += f"| Category | Details |\n"
        response += f"| :--- | :--- |\n"
        response += f"| **Artist** | {artist} |\n"
        response += f"| **Album** | {album} |\n"
        response += f"| **Release Year** | {year} |\n"
        response += f"| **Genre** | {genre} |\n\n"
        response += f"*smiles* This track is a masterclass in {genre.lower()}! Should I play it for you? "
        
        return {
            "response": response,
            "data": {"query": f"{track} {artist}"},
            "suggested_next": "play" 
        }

    # Fallback to DDGS if iTunes fails
    print(f" iTunes Fallback -> DDGS: {query}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} song details facts", region='in-en', max_results=3))
        
        if not results:
            return f"I couldn't find detailed info about '{query}'. Maybe it's a hidden gem? "

        response = f"*adjusts glasses* I've gathered some insights on '{query}':\n\n"
        for res in results:
            response += f"• {res['body'][:200]}...\n"
        
        response += "\n*smiles* Music history is fascinating! Want to hear it?"
        
        return {
            "response": response,
            "data": {"query": query},
            "suggested_next": "play"
        }
    except Exception as e:
        print(f"Music Info Fallback Error: {e}")
        return "I hit a snag while researching that song. My apologies. "

def cmd_lyrics(args):
    """Usage: lyrics <song name>"""
    query = args.lower().replace("lyrics of", "").replace("lyrics", "").strip()
    
    if not query:
        return "Which song's lyrics are you looking for? "

    print(f" Fetching Full Lyrics for: {query}")
    import requests
    
    try:
        # Using a reliable public API for lyrics
        url = f"https://some-random-api.com/lyrics?title={query}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', query.title())
            artist = data.get('author', 'Unknown Artist')
            lyrics = data.get('lyrics', '')
            
            if lyrics:
                # Truncate if insanely long, but usually fine
                if len(lyrics) > 3000:
                    lyrics = lyrics[:3000] + "\n\n... (Lyrics truncated)"
                    
                response_text = f"###  Lyrics: **{title}** by {artist}\n\n"
                response_text += f"{lyrics}\n\n"
                response_text += f"*starts singing along* I love this part! Hope you enjoy singing it too! "
                return response_text

        # Fallback to DDGS snippet if API fails
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} song lyrics full", region='in-en', max_results=3))
        
        if not results:
            return f"I couldn't find the lyrics for '{query}'. Perhaps you could hum a few lines for me? "

        response_text = f"Here is a snippet of lyrics for '{query}':\n\n"
        for res in results[:2]:
            response_text += f"• {res['body'][:200]}...\n"
        response_text += f"\nFull lyrics here: {results[0]['href']}\n\n*blushes* I hope this helps!"
        return response_text

    except Exception as e:
        print(f"Lyrics Error: {e}")
        return "I couldn't fetch the lyrics right now. Try again later? "

def cmd_trending_indian(args):
    """Usage: trending songs or popular indian music"""
    print(" Fetching Authentic Indian Charts...")
    
    try:
        from ytmusicapi import YTMusic
        yt = YTMusic()
        explore = yt.get_charts(country='IN')
        
        songs = explore.get('songs', {}).get('items', [])
        if not songs:
            raise Exception("No chart data from YTMusic")
            
        response = "###  Top Trending Songs in India (YT Music)\n\n"
        for i, song in enumerate(songs[:7], 1):
            title = song.get('title', 'Unknown')
            artists = ", ".join([a.get('name', '') for a in song.get('artists', [])])
            response += f"**{i}. {title}** by {artists}\n"

        response += "\n*hums a popular tune* Should I play one of these for you? Just say the name! "
        return response

    except Exception as e:
        print(f"Trending Error (YTMusic failed, falling back): {e}")
        # Fallback to DDGS
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text("top trending songs in India 2026 popular bollywood hits", region='in-en', max_results=5))
            
            response_text = "*smiles brightly* Here's what's currently topping the charts in India:\n\n"
            for i, res in enumerate(results[:5], 1):
                response_text += f"{i}. {res['title']}\n"
            response_text += "\nShould I play any of these?"
            return response_text
        except Exception:
            return "Chart data is a bit messy right now. Let's try later! "

def cmd_artist_briefing(args):
    """Usage: artist info <name> or tell me about <artist>"""
    artist = args.lower().replace("artist info", "").replace("tell me about", "").replace("who is", "").replace("details of", "").strip()
    
    if not artist:
        return "Which artist should I research for you? "

    print(f" Artist Research (iTunes API): {artist}")
    metadata = _fetch_itunes_metadata(artist, entity="musicArtist")

    if metadata:
        name = metadata.get('artistName', artist.title())
        genre = metadata.get('primaryGenreName', 'Music')
        view_url = metadata.get('artistLinkUrl', '#')

        briefing = f"###  Artist Briefing: **{name}**\n\n"
        briefing += f"**Primary Genre:** {genre}\n\n"
        briefing += "*smiles* They are such a legendary figure in the music world! Should I play some of their top hits for you? "
        
        return {
            "response": briefing,
            "data": {"artist": name},
            "suggested_next": "play"
        }

    # Fallback to DDGS
    print(f" Artist Fallback -> DDGS: {artist}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{artist} artist biography career facts", region='in-en', max_results=3))
        
        if not results:
            return f"I couldn't find detailed info about '{artist}'. Perhaps they're an underground talent? "

        briefing = f"###  Artist Briefing: **{artist.title()}**\n\n"
        briefing += "| Category | Details |\n"
        briefing += "| :--- | :--- |\n"
        briefing += f"| **Highlights** | {results[0]['body'][:200]}... |\n\n"
        briefing += "*smiles* Their journey is inspiring! Want to hear their music? "
        
        return {
            "response": briefing,
            "data": {"artist": artist},
            "suggested_next": "play"
        }
    except Exception as e:
        print(f"Artist Briefing Error: {e}")
        return f"Aww, I had trouble looking up {artist}. Mind trying again? "

def cmd_global_charts(args):
    """Usage: worldwide charts, billboard, global trends"""
    print(" Fetching Global Music Trends...")
    
    try:
        from ytmusicapi import YTMusic
        yt = YTMusic()
        explore = yt.get_charts(country='US') # Represents global/billboard
        
        songs = explore.get('songs', {}).get('items', [])
        if not songs:
            raise Exception("No chart data from YTMusic")
            
        response = "###  Universal Music Trends (Global Top 5)\n\n"
        for i, song in enumerate(songs[:5], 1):
            title = song.get('title', 'Unknown')
            artists = ", ".join([a.get('name', '') for a in song.get('artists', [])])
            response += f"**{i}. {title}** by {artists}\n"

        response += "\n*hums a tune* Quite the variety today! Would you like to hear any of these? (◕‿◕✿) "
        return response

    except Exception as e:
        print(f"Global Charts Error: {e}")
        return "I couldn't synch with the global charts right now. I'll try again later! "


def cmd_download_song(args):
    """Usage: download song <name>"""
    query = args.lower().replace("download song", "").replace("download music", "").replace("download", "").strip()
    
    if not query:
        return "Which song would you like me to download to your PC? "
        
    try:
        import platform
        import threading
        
        music_dir = os.path.join(os.path.expanduser("~"), "Music", "Nova Downloads")
        if not os.path.exists(music_dir):
            os.makedirs(music_dir)
            
        def download_thread():
            try:
                print(f" Starting download: {query}")
                out_template = os.path.join(music_dir, "%(title)s.%(ext)s")
                
                # Fetch top result and download as mp3
                dl_cmd = [
                    "yt-dlp", 
                    f"ytsearch1:{query} audio", 
                    "-x", 
                    "--audio-format", "mp3", 
                    "--audio-quality", "0", 
                    "-o", out_template
                ]
                
                # Hidden terminal execution
                subprocess.run(dl_cmd, creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0)
                print(f"✅ Download complete: {query}")
                
            except Exception as e:
                print(f"Download thread error: {e}")

        # Start download in background so Nova doesn't freeze
        threading.Thread(target=download_thread, daemon=True).start()
        
        return f"On it! I'm downloading '{query}' as an MP3. It will be saved to your `Music/Nova Downloads` folder shortly! ✨"
        
    except Exception as e:
        return f"I had trouble starting the download. Error: {e}"
def cmd_mood_recommendation(args):
    """Usage: suggest some music, what should I listen to?, mood music"""
    from core.emotion_detector import emotion_detector
    
    # 1. Infer Mood
    user_mood = emotion_detector.get_primary_emotion(args)
    if user_mood == "neutral" and len(args.split()) < 3:
        # If input is too short to detect, check common keywords manually
        if any(w in args.lower() for w in ["happy", "good", "great", "party"]): user_mood = "joy"
        elif any(w in args.lower() for w in ["sad", "lonely", "down"]): user_mood = "sadness"
        elif any(w in args.lower() for w in ["chill", "study", "relax", "lofi"]): user_mood = "chill"
        elif any(w in args.lower() for w in ["gym", "workout", "pumped"]): user_mood = "excitement"

    print(f" Mood-Music Inference: {user_mood}")
    
    # 2. Map Mood to Search Query
    mood_queries = {
        "joy": "upbeat happy party songs 2026 hits",
        "sadness": "melancholic sad breakup songs playlist",
        "excitement": "high energy gym workout power music",
        "chill": "lofi hip hop chill study beats playlist",
        "love": "romantic love songs couple playlist",
        "anger": "aggressive heavy metal hard rock hype songs",
        "fear": "calming peaceful meditation nature sounds",
        "neutral": "popular top hits radio today"
    }
    
    search_query = mood_queries.get(user_mood, "lofi chill study beats")
    print(f" Searching for {user_mood} music: {search_query}")

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"best {search_query} spotify youtube", region='in-en', max_results=5))
        
        if not results:
            return "I couldn't find a specific playlist for your mood right now. Maybe some classics? "

        # 3. Construct Narrative Result
        mood_intro = {
            "joy": "*dances slightly* You're in a great mood! Let me keep that energy up!",
            "sadness": "*pats your head* It's okay to feel a bit down. Here's something to help you relax...",
            "excitement": "*fists go up* Hell yeah! Let's get pumped!",
            "chill": "*leans back* Perfect. Let's just vibe for a while...",
            "love": "*blushes* Oh... something romantic? How sweet...",
            "anger": "*nods* I get it. Let some steam out with these...",
            "neutral": "*smiles* How about we try something popular today?"
        }
        
        intro = mood_intro.get(user_mood, mood_intro["neutral"])
        response = f"{intro} I found some music that matches your state:\n\n"
        
        for i, res in enumerate(results[:3], 1):
            response += f"{i}. {res['title'][:80]}\n"
            
        response += f"\n*hums a matching tune* Should I play the top choice '{results[0]['title'][:40]}' for you? "
        
        return {
            "response": response,
            "data": {"query": results[0]['title']},
            "suggested_next": "play" 
        }

    except Exception as e:
        print(f"Mood Recommendation Error: {e}")
        return "I hit a snag while looking for music. Try again? "

def register(dispatcher):
    dispatcher.register("music info", cmd_music_info)
    dispatcher.register("song info", cmd_music_info)
    dispatcher.register("lyrics", cmd_lyrics)
    dispatcher.register("popular songs", cmd_trending_indian)
    dispatcher.register("trending songs", cmd_trending_indian)
    dispatcher.register("indian music", cmd_trending_indian)
    dispatcher.register("bollywood", cmd_trending_indian)
    
    # New Advanced Triggers
    dispatcher.register("artist info", cmd_artist_briefing)
    dispatcher.register("who is", cmd_artist_briefing)
    dispatcher.register("tell me about the artist", cmd_artist_briefing)
    
    dispatcher.register("worldwide charts", cmd_global_charts)
    dispatcher.register("global charts", cmd_global_charts)
    dispatcher.register("billboard", cmd_global_charts)
    dispatcher.register("top hits", cmd_global_charts)
    dispatcher.register("global trends", cmd_global_charts)
    
    # Advanced Music Features
    dispatcher.register("download", cmd_download_song)
    dispatcher.register("download song", cmd_download_song)
    dispatcher.register("download music", cmd_download_song)
    
    # Mood Recommendations
    dispatcher.register("suggest music", cmd_mood_recommendation)
    dispatcher.register("music for my mood", cmd_mood_recommendation)
    dispatcher.register("what should i listen to", cmd_mood_recommendation)
    dispatcher.register("play something for me", cmd_mood_recommendation)
    dispatcher.register("suggest some music", cmd_mood_recommendation)
    dispatcher.register("mood music", cmd_mood_recommendation)
