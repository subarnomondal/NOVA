import os
import requests # type: ignore
import re
from urllib.parse import urlparse
from duckduckgo_search import DDGS  # Added for image search functionality
# Fallback if text search is needed, but DDGS has images() method too

def cmd_download(args):
    """Usage: download <url> or download image of <thing>"""
    try:
        # Extract URL using regex
        url_match = re.search(r'(https?://[^\s]+)', args)
        
        url = ""
        filename_hint = ""
        
        if url_match:
            url = url_match.group(1).strip()
        else:
            # It's a natural language request, try to search for an image/file
            query = args.replace("download", "").replace("save", "").replace("get", "").strip()
            
            # Simple heuristic: if user asks for "image of" or "picture of", use image search
            if "image" in query or "picture" in query or "photo" in query:
                print(f" Searching for images of: {query}")
                try:
                    with DDGS() as ddgs:
                        # Search for 1 image
                        results = list(ddgs.images(query, max_results=1))
                        if results:
                            url = results[0]['image']
                            print(f" Found image URL: {url}")
                            # Clean up filename from query
                            filename_hint = query.replace(" ", "_").replace("image_of_", "").replace("picture_of_", "") + ".jpg"
                        else:
                            return f"I searched for images of '{query}' but couldn't find any downloadable ones. "
                except Exception as s_err:
                     print(f"Search Error: {s_err}")
                     return "I tried to search for that image, but ran into a connection issue. "
            else:
                 return "I'd love to download that! If it's a specific file, please paste the link. If you want an image, ask for 'image of [thing]'. "

        if not url:
             return "I couldn't find a valid URL to download. "
        
        # Determine filename (use hint if available from search)
        
        # Determine filename
        if filename_hint:
             filename = filename_hint
        else:
            path = urlparse(url).path
            filename = os.path.basename(path)
            if not filename or '.' not in filename:
                filename = "downloaded_file_" + os.urandom(4).hex()
            
        # Create downloads folder
        download_dir = "downloads"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
            
        filepath = os.path.join(download_dir, filename)
        
        # Perform download
        print(f" Downloading: {url}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        import random
        responses = [
            f"All done! Your file is saved in the downloads folder as '{filename}'. ✅",
            f"Success! I've downloaded '{filename}' to your downloads folder. ",
            f"Got it! You'll find '{filename}' in the downloads folder now. "
        ]
        return random.choice(responses)
        
    except Exception as e:
        print(f"Download Error: {e}")
        return f"Hmm, I ran into trouble downloading that file. Here's what went wrong: {str(e)}"

def register(dispatcher):
    dispatcher.register("download", cmd_download)
    dispatcher.register("get file", cmd_download)
    dispatcher.register("save from", cmd_download)
