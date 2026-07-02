
import requests # type: ignore
import json
import os

class LocationService:
    def __init__(self, profile_path=os.path.join("userdata", "user_profile.json")):
        self.profile_path = profile_path
        self.location_data = self._load_location()

    def _load_location(self):
        """Loads cached location from profile or fetches new."""
        # 1. Check if we have cached location in profile
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    loc = data.get("personal_info", {}).get("location_data")
                    if loc and loc.get("city"):
                        return loc
            except:
                pass
        
        # 2. If not, fetch it
        return self.fetch_location()

    def fetch_location(self):
        """Fetches precise location using IP-API."""
        print(" Detecting precise location via IP...")
        try:
            # Using ip-api.com (Free, no key required for basic usage)
            response = requests.get("http://ip-api.com/json/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    loc_data = {
                        "city": data.get("city"),
                        "region": data.get("regionName"),
                        "country": data.get("country"),
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "timezone": data.get("timezone")
                    }
                    print(f" Location Detected: {loc_data['city']}, {loc_data['region']}")
                    self._save_location_to_profile(loc_data)
                    return loc_data
        except Exception as e:
            print(f"⚠️ Location Fetch Error: {e}")
        
        return None

    def _save_location_to_profile(self, loc_data):
        """Updates user_profile.json with new location data."""
        if not os.path.exists(self.profile_path):
            return

        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            # Update structure
            if "personal_info" not in profile: profile["personal_info"] = {}
            profile["personal_info"]["location"] = f"{loc_data['city']}, {loc_data['country']}"
            profile["personal_info"]["location_data"] = loc_data
            
            # Also update timezone if found
            if loc_data.get("timezone"):
                if "preferences" not in profile: profile["preferences"] = {}
                profile["preferences"]["timezone"] = loc_data["timezone"]

            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Failed to save location to profile: {e}")

    def get_city(self):
        if self.location_data:
            return self.location_data.get("city")
        return None

    def get_coordinates(self):
        if self.location_data:
            return self.location_data.get("lat"), self.location_data.get("lon")
        return None, None

# Singleton-esque usage
# Global singleton
location_service = LocationService()

if __name__ == "__main__":
    print(location_service.get_city())
