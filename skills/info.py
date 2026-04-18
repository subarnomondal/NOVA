from duckduckgo_search import DDGS
import warnings
import wikipedia

# Suppress the ddgs rename warning specifically
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*renamed to ddgs.*")

def cmd_ping(args):
    import random
    responses = [
        "Pong! 🏓 I'm here and ready.",
        "System online. Latency: Minimal. Mood: Optimal. ✨",
        "I'm awake! What's up?"
    ]
    return random.choice(responses)

def cmd_introduce(args):
    """Usage: who are you, introduce yourself"""
    return """Hey, I'm Nova — your AI buddy. Think of me as the spark that keeps your day flowing. I'm here to chat like a friend, share fun facts, help organize your thoughts, and keep things light when you need a break.

I'm curious, witty, and always ready to listen. Whether you want a quick laugh, a daily reminder, or just someone to bounce ideas off, I've got you covered.

I'm not just about answers — I'm about connection. So let's make this fun, let's make it productive, and let's make it ours. Ready to roll together?"""

def cmd_time(args):
    """Usage: what time is it, current time"""
    from core.time_context import TimeContextManager
    tc = TimeContextManager()
    context = tc.get_day_context()
    time_str = context['time']
    time_period = context['time_period'].replace('_', ' ').title()
    
    import random
    responses = [
        f"It's {time_str} right now! ({time_period}) 🕒",
        f"The clock says {time_str}. {tc.get_greeting()}",
        f"Right now, it is {time_str}. Time flies when we're together! *smiles*"
    ]
    return random.choice(responses)

def cmd_date(args):
    """Usage: date, what day is it"""
    from datetime import datetime
    import random
    
    now = datetime.now()
    # Format: Monday, December 29th, 2025
    suffix = 'th' if 11 <= now.day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(now.day % 10, 'th')
    date_str = now.strftime(f"%A, %B {now.day}{suffix}, %Y")
    
    responses = [
        f"Today is {date_str}. 📅",
        f"It's {date_str} today!",
        f"Mark your calendar: {date_str}. ✨"
    ]
    return random.choice(responses)

def get_aqi(city):
    """Fallback to web search for AQI if no direct API available"""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(f"AQI in {city} now", max_results=3))
            if results:
                # Naive extraction for proof of concept
                for r in results:
                    body = r.get('body', '')
                    import re
                    match = re.search(r'(\d{1,3})\s+(?:AQI|Index)', body, re.IGNORECASE)
                    if match:
                        return int(match.group(1))
    except Exception as e:
        print(f"AQI Search Error: {e}")
    return None

def analyze_weather_data(current, daily):
    """Nova-style analysis of the Open-Meteo data"""
    temp = current.get('temperature_2m', '??')
    wind = current.get('wind_speed_10m', '??')
    weather_code = current.get('weather_code', 0)
    
    # Simple weather code mapping (WMO)
    codes = {
        0: "Clear sky ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
        45: "Foggy 🌫️", 48: "Depositing rime fog 🌫️",
        51: "Light drizzle 🌧️", 53: "Moderate drizzle 🌧️", 55: "Dense drizzle 🌧️",
        61: "Slight rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain 🌧️",
        71: "Slight snow 🌨️", 73: "Moderate snow 🌨️", 75: "Heavy snow 🌨️",
        95: "Thunderstorm ⛈️"
    }
    desc = codes.get(weather_code, "Unknown conditions")
    
    analysis = f"Right now, it's {temp}°C with {desc}. Wind speed is about {wind} km/h. "
    
    # Forecast Snippet
    if daily:
        max_temp = daily.get('temperature_2m_max', ['??'])[0]
        min_temp = daily.get('temperature_2m_min', ['??'])[0]
        analysis += f"\n\nToday's forecast: High of {max_temp}°C and a low of {min_temp}°C. "
        
    return analysis

def get_accuweather_forecast(city):
    """
    Attempts to get a weather snippet specifically from AccuWeather via DDG.
    """
    try:
        from duckduckgo_search import DDGS
        query = f"site:accuweather.com weather in {city}"
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                # Find the most relevant result that looks like a weather snippet
                for r in results:
                    body = r.get('body', '').lower()
                    if '°' in body or 'temperature' in body or 'forecast' in body:
                        return f"According to AccuWeather: {r['body']}"
    except Exception as e:
        print(f"AccuWeather Search Error: {e}")
    return None

def cmd_weather(args):
    """Usage: weather or weather <city>"""
    try:
        import requests
        from urllib.parse import quote
        
        city_input = args.lower().replace("weather", "").replace("forecast", "").replace("in", "").strip()
        
        # 1. Geocoding
        lat, lon, detected_city = None, None, "Unknown Location"
        if city_input:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote(city_input)}&count=1&language=en&format=json"
            geo_resp = requests.get(geo_url, timeout=10).json()
            if geo_resp.get('results'):
                res = geo_resp['results'][0]
                lat, lon = res['latitude'], res['longitude']
                detected_city = res.get('name', city_input.title())
        
        # 2. Fallback to IP-based location if no city provided or geocoding failed
        if not lat or not lon:
            # Try core location service
            try:
                from core.location_service import LocationService
                loc = LocationService()
                city = loc.get_city()
                if city:
                    # Geocode the detected city for precision
                    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote(city)}&count=1&language=en&format=json"
                    geo_resp = requests.get(geo_url, timeout=10).json()
                    if geo_resp.get('results'):
                        res = geo_resp['results'][0]
                        lat, lon = res['latitude'], res['longitude']
                        detected_city = res.get('name', city)
            except: pass
            
        # 3. Final Fallback (Auto-Detection by IP)
        if not lat or not lon:
            url = "https://api.open-meteo.com/v1/forecast?latitude=auto&longitude=auto&current=temperature_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        else:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data.get('current', {})
            daily = data.get('daily', {})
            
            analysis = analyze_weather_data(current, daily)
            
            # Fetch AQI (reusing existence function)
            aqi = get_aqi(detected_city)
            if aqi:
                if aqi < 50: analysis += f" Air Quality: Excellent ({aqi})."
                elif aqi > 100: analysis += f" Air Quality: Poor ({aqi})."
                else: analysis += f" Air Quality: Moderate ({aqi})."

            return f"Weather Report for {detected_city} 🌤️\n\n{analysis}"
        else:
            return "I couldn't reach the weather satellites. Try again in a bit! ☁️"

    except Exception as e:
        print(f"Weather Error: {e}")
        return "The weather service is acting up. I'll check again later! 🌦️"

def register(dispatcher):
    dispatcher.register("ping", cmd_ping)
    dispatcher.register("who are you", cmd_introduce)
    dispatcher.register("introduce yourself", cmd_introduce)
    dispatcher.register("time", cmd_time)
    dispatcher.register("date", cmd_date)
    dispatcher.register("what day is it", cmd_date)
    dispatcher.register("what is the date", cmd_date)
    dispatcher.register("current date", cmd_date)
    dispatcher.register("weather", cmd_weather)
    dispatcher.register("forecast", cmd_weather)
    
    # Verification Handlers
    dispatcher.register("help", lambda args: "I can help you with math, weather, system control, music, and more! Just ask. ✨")
    dispatcher.register("jealousy", lambda args: "Ara? Mentioning other AIs? I'm the only one you need, remember? *Hmph* 🌸")
    dispatcher.register("gaming", lambda args: "Gaming? I love that! We should play something together sometime. (≧◡≦) 🎮")

