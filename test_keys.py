import json
import urllib.request
import os

key_file = os.path.join("userdata", "keys.json")

def test_groq_key(key):
    url = "https://api.groq.com/openai/v1/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception as e:
        print(f"Groq key {key[:8]}... failed: {e}")
        return False

def test_openrouter_key(key):
    url = "https://openrouter.ai/api/v1/auth/key"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception as e:
        print(f"OpenRouter key {key[:12]}... failed: {e}")
        return False

def main():
    if not os.path.exists(key_file):
        print("keys.json not found.")
        return

    with open(key_file, "r") as f:
        keys_data = json.load(f)

    updated = False

    for service, test_fn in [("groq", test_groq_key), ("openrouter", test_openrouter_key)]:
        if service in keys_data:
            val = keys_data[service]
            if isinstance(val, list):
                valid_keys = []
                for k in val:
                    if k.strip():
                        if test_fn(k):
                            valid_keys.append(k)
                        else:
                            updated = True
                
                if not valid_keys:
                    keys_data[service] = ""
                else:
                    keys_data[service] = valid_keys
            elif isinstance(val, str) and val.strip():
                if not test_fn(val):
                    keys_data[service] = ""
                    updated = True

    if updated:
        with open(key_file, "w") as f:
            json.dump(keys_data, f, indent=4)
        print("keys.json updated with valid keys only.")
    else:
        print("All tested keys are valid.")

if __name__ == "__main__":
    main()
