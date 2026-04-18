import json
import os
import re
from difflib import get_close_matches

def load_contacts():
    try:
        contacts_path = os.path.join("userdata", "contacts.json")
        if os.path.exists(contacts_path):
            with open(contacts_path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading contacts: {e}")
    return {}

def cmd_call(args):
    """Usage: call <number> or call <name>"""
    try:
        phone_number = None
        contact_name = None
        
        # 1. Try to extract digits first
        match = re.search(r"(\+?\d[\d\s-]{7,15})", args)
        
        if match:
            phone_number = match.group(1).replace(" ", "").replace("-", "")
        else:
            # 2. Try to lookup name in contacts
            contacts = load_contacts()
            # Clean args to get potential name (remove 'call', 'dial')
            search_query = args.lower().replace("call", "").replace("dial", "").replace("phone", "").strip()
            
            if search_query and contacts:
                # Direct match
                if search_query in contacts:
                    phone_number = contacts[search_query]
                    contact_name = search_query
                else:
                    # Fuzzy match
                    matches = get_close_matches(search_query, contacts.keys(), n=1, cutoff=0.6)
                    if matches:
                        match_name = matches[0]
                        phone_number = contacts[match_name]
                        contact_name = match_name
        
        if not phone_number:
            return "I couldn't find a number or contact for that. You can say 'Call 9876543210' or 'Call [Name]' if they are in your contacts. 📞"
        
        # Trigger Windows default telephony app (usually Phone Link)
        print(f"📞 Initiating call to: {phone_number} ({contact_name if contact_name else 'Unknown'})")
        os.system(f"start tel:{phone_number}")
        
        import random
        responses = [
            f"Got it! Calling {phone_number} now. Your Phone Link window should pop up any second! 📱",
            f"On it! Dialing {phone_number} for you right now. 📞",
            f"Sure thing! Starting a call to {phone_number}. The Phone Link app should open up shortly! ✨"
        ]
        return random.choice(responses)
        
    except Exception as e:
        print(f"Calling Error: {e}")
        return f"Oops, I ran into a little trouble starting that call. Could you check if Phone Link is set up on your PC? I'm here if you need help! 💙"

def register(dispatcher):
    dispatcher.register("call", cmd_call)
    dispatcher.register("phone", cmd_call)
    dispatcher.register("dial", cmd_call)
