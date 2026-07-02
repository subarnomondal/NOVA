import requests
import random
from datetime import datetime

# --- HELPER FUNCTIONS ---

def fetch_earthquakes():
    """Fetch real-time earthquakes from USGS (Last 24 hours, Magnitude 2.5+)"""
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            results = []
            for f in features[:10]: # Get top 10
                prop = f['properties']
                geom = f['geometry']['coordinates']
                results.append({
                    "title": prop['title'],
                    "place": prop['place'],
                    "mag": prop['mag'],
                    "time": datetime.fromtimestamp(prop['time']/1000).strftime('%H:%M'),
                    "lat": geom[1],
                    "lon": geom[0]
                })
            return results
    except Exception as e:
        print(f"Earthquake Fetch Error: {e}")
    return []

def fetch_nasa_events():
    """Fetch natural events from NASA EONET (Wildfires, Storms, Volcanoes)"""
    try:
        url = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&category=wildfires,severeStorms,volcanoes"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            results = []
            for e in events[:10]:
                if not e.get('geometries'): continue
                geom = e['geometries'][0]['coordinates']
                results.append({
                    "title": e['title'],
                    "category": e['categories'][0]['title'],
                    "lat": geom[1],
                    "lon": geom[0]
                })
            return results
    except Exception as e:
        print(f"NASA EONET Error: {e}")
    return []

def fetch_tides(station_id="9414290"):
    """Fetch real-time tides from NOAA CO-OPS API"""
    try:
        url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?date=latest&station={station_id}&product=water_level&datum=mllw&time_zone=lst_ldt&units=metric&format=json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                return data['data'][-1]
    except Exception as e:
        print(f"Tide Fetch Error: {e}")
    return {"error": "Could not fetch tide data"}

# --- COMMAND HANDLERS ---

def cmd_earthquakes(args):
    """Usage: earthquakes, earthquake alerts"""
    try:
        quakes = fetch_earthquakes()
        if not quakes:
            response = "I've scanned the seismic sensors, bestie, and everything seems super calm! No major quakes to report! Stay safe! ✨"
        else:
            response = f"Oh no! My sensors just picked up {len(quakes)} earthquakes!  I've marked them on your Earth Mission Control dashboard for you! Stay safe! ️"
            
        return {
            "response": response,
            "data": {
                "type": "natural_events",
                "events": quakes
            }
        }
    except Exception as e:
        return f"Oops! I couldn't fetch the earthquake data. ️ Error: {e}"

def cmd_natural_events(args):
    """Usage: natural events, what's happening on earth"""
    try:
        nasa_events = fetch_nasa_events()
        quakes = fetch_earthquakes()
        all_events = nasa_events + quakes
        
        if not all_events:
            response = "I've checked the satellites, and everything looks peaceful! No major wildfires or storms detected right now. ✨"
        else:
            response = f"Scanning the globe for you! ️ I found {len(all_events)} environmental events! Opening Earth Mission Control... "
            
        return {
            "response": response,
            "data": {
                "type": "natural_events",
                "events": all_events
            }
        }
    except Exception as e:
        return f"Satellite link error! I couldn't reach NASA's network. ️"

def cmd_tides(args):
    """Usage: tides near <city>"""
    try:
        # Mock station mapping for demo
        stations = {"san francisco": "9414290", "new york": "8518750", "boston": "8443970"}
        query = args.lower().replace("tides near", "").replace("tides in", "").replace("tides", "").strip()
        station_id = stations.get(query, "9414290")
        
        tide_info = fetch_tides(station_id)
        if "error" in tide_info:
            return "I had a little splashy trouble getting the tide data. "
            
        return f"Checking the tides!  The current water level at the nearest station is {tide_info.get('v', 'unknown')}m! Stay wavy, bestie! ✨"
    except Exception as e:
        return "Tide sensors are a bit offline right now! "

def register(dispatcher):
    dispatcher.register("natural events", cmd_natural_events)
    dispatcher.register("what's happening on earth", cmd_natural_events)
    dispatcher.register("nasa news", cmd_natural_events)
    dispatcher.register("earthquakes", cmd_earthquakes)
    dispatcher.register("earthquake alerts", cmd_earthquakes)
    dispatcher.register("tides", cmd_tides)
