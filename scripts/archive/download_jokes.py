import json
import urllib.request
import os

def fetch_large_joke_dataset():
    print("Downloading 10,000+ jokes...")
    jokes = set()
    
    # We will use public datasets from github (taivop/joke-dataset)
    datasets = [
        "https://raw.githubusercontent.com/taivop/joke-dataset/master/wocka.json",
        "https://raw.githubusercontent.com/taivop/joke-dataset/master/stupidstuff.json"
    ]
    
    for url in datasets:
        print(f"Fetching from {url}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                for item in data:
                    body = item.get('body', '').strip()
                    title = item.get('title', '').strip()
                    
                    if len(body) > 1000: # Skip extremely long jokes
                        continue
                        
                    if title and title.lower() not in body.lower():
                        joke_text = f"{title}\n{body}"
                    else:
                        joke_text = body
                        
                    if joke_text:
                        jokes.add(joke_text)
        except Exception as e:
            print(f"Error fetching dataset: {e}")

    os.makedirs("userdata", exist_ok=True)
    with open("userdata/jokes.json", "w", encoding="utf-8") as f:
        json.dump(list(jokes), f, indent=4)
        
    print(f"Successfully saved {len(jokes)} jokes to userdata/jokes.json")

if __name__ == "__main__":
    fetch_large_joke_dataset()
