
import os
import sys
import subprocess
import time

def install_dependency():
    try:
        import ytmusicapi
    except ImportError:
        print(" Installing ytmusicapi...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ytmusicapi"])

def setup_oauth():
    from ytmusicapi import YTMusic
    
    print("\n Nova YouTube Music Sync Setup ")
    print("-----------------------------------")
    print("This will allow Nova to access your playlists and library.")
    print("Please follow the instructions that appear in your browser/terminal.\n")
    
    # This initiates the OAuth flow
    # It will print a URL and a code, then wait for the user to authorize
    # The token is saved to oauth.json
    try:
        # Standard ytmusicapi oauth setup
        # It usually prompts input in console, which is tricky with run_command if interactive
        # But ytmusicapi.setup_oauth() is interactive.
        # We might need to run this in a visible terminal or handle input.
        # Antigravity's run_command is non-interactive usually unless send_command_input is used.
        # However, ytmusicapi.setup(session=...) is for headers.
        # For OAuth:
        # YTMusic.setup_oauth(filepath="oauth.json")
        
        if os.path.exists("oauth.json"):
            print("✅ oauth.json already exists! You are already synced. Delete it if you want to re-sync.")
            return

        print("⚠️  YT Music Authentication (Browser Method) ⚠️")
        print("------------------------------------------------")
        print("1. Open https://music.youtube.com in your browser (Chrome/Firefox/Edge).")
        print("2. Log in if you haven't.")
        print("3. Press F12 to open Developer Tools > Go to 'Network' tab.")
        print("4. Reload the page.")
        print("5. Look for a request like 'browse' or 'home' (filter by 'XHR' or 'Fetch').")
        print("6. Click it, scroll down to 'Request Headers'.")
        print("7. Copy the entire 'Cookie' value (or all headers).")
        print("8. PASTE it below and press Enter twice/Ctrl+Z depending on terminal.\n")
        
        # Use the browser method which asks for headers
        from ytmusicapi import setup
        setup(filepath="oauth.json")
        
        print("\n✅ Success! authorized and saved to 'oauth.json'.")
        print("   Nova can now access your account!")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        print("   You might need to run 'ytmusicapi oauth' in your terminal manually.")

if __name__ == "__main__":
    install_dependency()
    setup_oauth()
