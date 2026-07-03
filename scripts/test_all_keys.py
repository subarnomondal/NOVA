import json
import urllib.request
import os

key_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "userdata", "keys.json")

def _test_endpoint(url, headers=None):
    headers = headers or {}
    try:
        req = urllib.request.Request(url, headers=headers)
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

def test_gemini(key):
    return _test_endpoint(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro?key={key}")

def test_openai(key):
    return _test_endpoint("https://api.openai.com/v1/models", {"Authorization": f"Bearer {key}"})

def test_weather(key):
    return _test_endpoint(f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={key}")

def test_news(key):
    return _test_endpoint(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={key}")

def test_elevenlabs(key):
    return _test_endpoint("https://api.elevenlabs.io/v1/voices", {"xi-api-key": key})

def test_huggingface(key):
    return _test_endpoint("https://huggingface.co/api/models", {"Authorization": f"Bearer {key}"})

def test_groq(key):
    return _test_endpoint("https://api.groq.com/openai/v1/models", {"Authorization": f"Bearer {key}"})

def test_openrouter(key):
    return _test_endpoint("https://openrouter.ai/api/v1/auth/key", {"Authorization": f"Bearer {key}"})


TESTERS = {
    "gemini": test_gemini,
    "openai": test_openai,
    "weather_api": test_weather,
    "news_api": test_news,
    "elevenlabs": test_elevenlabs,
    "huggingface": test_huggingface,
    "groq": test_groq,
    "openrouter": test_openrouter
}

def main():
    if not os.path.exists(key_file):
        print("keys.json not found.")
        return

    with open(key_file, "r") as f:
        keys_data = json.load(f)

    updated = False

    for service, tester in TESTERS.items():
        if service in keys_data:
            val = keys_data[service]
            if isinstance(val, list):
                valid_keys = []
                for k in val:
                    if k.strip():
                        print(f"Testing {service} key {k[:8]}...")
                        if tester(k):
                            print(" -> VALID")
                            valid_keys.append(k)
                        else:
                            print(" -> INVALID (Blanking)")
                            updated = True
                
                if len(valid_keys) != len(val):
                    keys_data[service] = valid_keys if valid_keys else ""
            elif isinstance(val, str) and val.strip():
                print(f"Testing {service} key {val[:8]}...")
                if tester(val):
                    print(" -> VALID")
                else:
                    print(" -> INVALID (Blanking)")
                    keys_data[service] = ""
                    updated = True

    if updated:
        with open(key_file, "w") as f:
            json.dump(keys_data, f, indent=4)
        print("keys.json updated. Invalid keys were made blank.")
    else:
        print("All populated keys are valid. No changes needed.")

if __name__ == "__main__":
    main()
