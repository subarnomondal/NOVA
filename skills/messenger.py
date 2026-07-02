import json
import os
import time

from core.llm_manager import llm_manager

class ContactManager:
    def __init__(self, contact_file=os.path.join("userdata", "contacts.json")):
        self.contact_file = contact_file
        self.contacts = {}
        self.load_contacts()
        
        # Ensure default test contact exists
        if "myself" not in self.contacts:
            self.add_contact("myself", "8420224011")

    def load_contacts(self):
        try:
            if os.path.exists(self.contact_file):
                with open(self.contact_file, 'r') as f:
                    self.contacts = json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading contacts: {e}")
            self.contacts = {}

    def save_contacts(self):
        try:
            with open(self.contact_file, 'w') as f:
                json.dump(self.contacts, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving contacts: {e}")

    def add_contact(self, name, number):
        self.contacts[name.lower()] = number
        self.save_contacts()
        return True

    def get_number(self, name):
        return self.contacts.get(name.lower())

    def list_contacts(self):
        return self.contacts

# Initialize Contact Manager
contact_manager = ContactManager()



def cmd_add_contact(args):
    """Usage: add contact <name> <number>"""
    try:
        import re
        # Extract number first
        phone_match = re.search(r'(\+?\d{10,15})', args)
        if not phone_match:
            return "I need a valid phone number to add a contact! (e.g. add contact John 1234567890) 📱"
        
        number = phone_match.group(1)
        
        # Extract name (everything else excluding 'add contact' and the number)
        # Robust cleaning for typos and variations
        clean_args = args.lower()
        for phrase in ["add contact", "add condract", "new contact", "save contact", "condract"]:
            clean_args = clean_args.replace(phrase, "")
            
        name_part = clean_args.replace(number, "").strip()
        
        if not name_part:
            return "What name should I save this number as? 🤔"
            
        contact_manager.add_contact(name_part, number)
        return f"Saved! {name_part.title()} is now in your contacts with number {number}. try saying 'whatsapp {name_part} hello'!"
        
    except Exception as e:
        return f"Failed to save contact: {e}"

def cmd_list_contacts(args):
    """Usage: list contacts"""
    contacts = contact_manager.list_contacts()
    if not contacts:
        return "You don't have any contacts saved yet! Try 'add contact name number'."
    
    msg = "Here are your contacts:\n"
    for name, number in contacts.items():
        msg += f"• {name.title()}: {number}\n"
    return msg

def cmd_find_contact(args):
    """Usage: find contact <name>"""
    try:
        import re
        import pyautogui # type: ignore
        import time
        import webbrowser
        
        # Extract search query
        clean_args = args.lower()
        for phrase in ["find contact", "find contract", "search contact", "search contract", "lookup contact", "lookup contract", "search for"]:
            clean_args = clean_args.replace(phrase, "")
        
        query = clean_args.strip()
        if not query:
            return "Who should I look for? Just say 'find contact name'. 🔍"

        # 1. Resolve internally first to see if we have it
        contacts = contact_manager.list_contacts()
        found_number = None
        found_name = None
        
        if query in contacts:
            found_number = contacts[query]
            found_name = query
        else:
            from difflib import get_close_matches
            matches = get_close_matches(query, contacts.keys(), n=1, cutoff=0.7)
            if matches:
                found_name = matches[0]
                found_number = contacts[found_name]

        # 2. Automation: Open WhatsApp and type query in search bar (Ctrl+F)
        # Using the protocol to wake/open WhatsApp
        uri = "whatsapp://"
        webbrowser.open(uri)
        time.sleep(2) # Wait for it to focus
        
        print(f"⌨️ Searching WhatsApp for '{query}' using human typing...")
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)
        pyautogui.write(query, interval=0.1)
        
        if found_number and found_name:
            return f"Opening WhatsApp and searching for '{query}'... *notes down* I actually have {found_name.title()} in my records as {found_number}! ✨"
        else:
            query_display = query.title() if query else "that contact"
            return f"Opening WhatsApp and typing '{query_display}' into the search bar for you now! I hope you find them. 🔍"

    except Exception as e:
        return f"Aww, I couldn't finish the search automation: {e}"

def cmd_delete_contact(args):
    """Usage: delete contact <name>"""
    try:
        clean_args = args.lower()
        for phrase in ["delete contact", "delete contract", "remove contact", "remove contract", "forget contact"]:
            clean_args = clean_args.replace(phrase, "")
        
        name = clean_args.strip()
        if not name:
            return "Which contact (or contract) should I delete? 🗑️"

        contacts = contact_manager.list_contacts()
        if name in contacts:
            del contact_manager.contacts[name]
            contact_manager.save_contacts()
            return f"Done! I've removed {name.title()} from your contacts. *dusts hands* 🧹"
        else:
            return f"I couldn't find anyone named '{name}' in your contacts to delete. 🧐"
    except Exception as e:
        return f"Error deleting contact: {e}"

def cmd_advanced_whatsapp_draft(args):
    """
    Advanced WhatsApp drafting.
    Usage: draft whatsapp for <topic> to <name>
    """
    try:
        from core.llm_manager import llm_manager
        tone = "casual"
        if "formal" in args.lower() or "teacher" in args.lower(): tone = "respectful and formal"
        
        topic = args.replace("draft", "").replace("whatsapp", "").replace("for", "").replace("to", "").strip()
        
        system_prompt = f"You are a helpful assistant. Write a short, clear WhatsApp message in a {tone} tone about: {topic}. No subject lines, just the message."
        draft = llm_manager.generate(f"Message content: {topic}", system_prompt=system_prompt)
        return draft if draft else "I couldn't generate a message."
    except Exception as e:
        return f"ERROR [MESSENGER_DRAFT_FAILURE]: {e}"

def cmd_send_message(args):
    """
    Advanced WhatsApp Dispatcher with Automatic Professional Drafting.
    Usage: whatsapp John saying I will be late or send message to 1234567890 saying hello
    """
    import re
    import random
    try:
        from core.llm_manager import llm_manager
        
        # 1. Resolve Contact/Number
        raw_phone = None
        # Check for direct number
        phone_match = re.search(r'(\+?\d{10,15})', args)
        if phone_match:
            raw_phone = phone_match.group(1)
            # Remove phone from args for cleaner topic extraction
            msg_args = args.replace(raw_phone, "").strip()
        else:
            # Check contacts
            contacts = contact_manager.list_contacts()
            # Try to find name between 'to'/'whatsapp' and 'saying'/'about'
            to_match = re.search(r'(?:to|whatsapp)\s+([\w\s]+?)(?:\s+saying|\s+about|\s+that|\s*$)', args, re.IGNORECASE)
            if to_match:
                name = to_match.group(1).strip()
                raw_phone = contact_manager.get_number(name)
                if not raw_phone:
                    # Fuzzy match
                    from difflib import get_close_matches
                    matches = get_close_matches(name.lower(), contacts.keys(), n=1, cutoff=0.7)
                    if matches:
                        raw_phone = contacts[matches[0]]
                        name = matches[0]
                msg_args = args.split(name)[-1].strip() if raw_phone else args
            else:
                return "Who should I message on WhatsApp? 📱"

        if not raw_phone:
            return "I couldn't find that contact. Try 'add contact <name> <number>' first!"

        # 2. Extract Message Intent
        # Look for content after 'saying', 'about', or just the remaining args
        content = ""
        if "saying" in msg_args.lower():
            content = msg_args.split("saying", 1)[1].strip()
        elif "about" in msg_args.lower():
            content = msg_args.split("about", 1)[1].strip()
        else:
            # Clean up command words including typos
            content = msg_args.lower()
            for cmd in ["whatsapp", "send message", "message", "massage", "massege", "to"]:
                content = content.replace(cmd, "")
            content = content.strip()

        if not content:
            return f"What would you like me to say to {raw_phone}? 📝"

        # 3. Professionalize Message using LLM
        print(f"📱 Professionalizing WhatsApp message for: {content}")
        system_prompt = (
            "You are Nova, a professional and efficient assistant. "
            "Rewrite the user's brief note into a short, clear, and professional WhatsApp message. "
            "Do NOT include subject lines or formal email closings. "
            "Just the message content. Keep it short for mobile reading."
        )
        
        professional_msg = llm_manager.generate(f"Note: {content}", system_prompt=system_prompt)
        
        if not professional_msg:
            professional_msg = content # Fallback
            
        # 4. Format and Dispatch
        clean_phone = str(raw_phone).replace('+', '').replace(' ', '').replace('-', '')
        if len(clean_phone) == 10: 
            clean_phone = "91" + clean_phone # Default to India prefix if 10 digits
        
        import webbrowser
        import pyautogui # type: ignore
        
        uri = f"whatsapp://send?phone={clean_phone}"
        print(f"🚀 Launching WhatsApp: {uri}")
        
        if webbrowser.open(uri):
            time.sleep(3) # Wait for WhatsApp to open and focus
            pyautogui.write(professional_msg, interval=0.05)
            # We don't press 'enter' automatically for safety, let the user review
            return f"I've drafted a professional WhatsApp message for you! ✅"
        else:
            return f"I couldn't open WhatsApp, but here's your professional draft: \"{professional_msg}\""
            
    except Exception as e:
        print(f"❌ Messenger Error: {e}")
        return f"Sorry, I couldn't prepare that WhatsApp message: {str(e)}"

def cmd_whatsapp_call(args):
    """
    Initiates a WhatsApp voice call.
    Usage: whatsapp call <name> or call <name> on whatsapp
    """
    import webbrowser
    from difflib import get_close_matches
    
    clean_args = args.lower()
    for phrase in ["whatsapp call", "call on whatsapp", "voice call", "call"]:
        clean_args = clean_args.replace(phrase, "")
    
    name = clean_args.strip()
    if not name:
        return "Who should I call on WhatsApp? 📞"
        
    contacts = contact_manager.list_contacts()
    # Direct lookup
    phone = contact_manager.get_number(name)
    
    # Fuzzy lookup
    if not phone:
        matches = get_close_matches(name.lower(), contacts.keys(), n=1, cutoff=0.7)
        if matches:
            name = matches[0]
            phone = contacts[name]
            
    if not phone:
        return f"I couldn't find {name} in your contacts. Try adding them first! 📱"
        
    # Standardize phone format
    clean_phone = str(phone).replace('+', '').replace(' ', '').replace('-', '')
    if len(clean_phone) == 10: 
        clean_phone = "91" + clean_phone
    
    # URI for WhatsApp Voice Call
    uri = f"whatsapp://voice/?phone={clean_phone}"
    print(f"🚀 [Messenger] Initiating WhatsApp Call to {name}: {uri}")
    
    if webbrowser.open(uri):
        return f"Starting a WhatsApp voice call with {name.title()}! 📞"
    else:
        return f"I tried to start the call for {name.title()}, but I had trouble opening WhatsApp."

def register(dispatcher):
    dispatcher.register("send message", cmd_send_message)
    dispatcher.register("whatsapp", cmd_send_message)
    
    # WhatsApp Calling
    dispatcher.register("whatsapp call", cmd_whatsapp_call)
    dispatcher.register("call on whatsapp", cmd_whatsapp_call)

    # Removed "message" - too generic, causes false matches with "helo" etc.
    dispatcher.register("massage", cmd_send_message)
    dispatcher.register("massege", cmd_send_message) # User typo
    # Removed "text" - too generic
    
    # Contact Management
    dispatcher.register("add contact", cmd_add_contact)
    dispatcher.register("add condract", cmd_add_contact) # User typo
    dispatcher.register("condract", cmd_add_contact) # User typo
    dispatcher.register("add contract", cmd_add_contact)
    dispatcher.register("contract", cmd_add_contact)
    dispatcher.register("save contact", cmd_add_contact)
    dispatcher.register("save contract", cmd_add_contact)
    
    dispatcher.register("list contacts", cmd_list_contacts)
    dispatcher.register("list contracts", cmd_list_contacts)
    
    dispatcher.register("find contact", cmd_find_contact)
    dispatcher.register("find contract", cmd_find_contact)
    dispatcher.register("search contact", cmd_find_contact)
    dispatcher.register("search contract", cmd_find_contact)
    dispatcher.register("lookup contact", cmd_find_contact)
    dispatcher.register("lookup contract", cmd_find_contact)
    
    dispatcher.register("delete contact", cmd_delete_contact)
    dispatcher.register("delete contract", cmd_delete_contact)
    dispatcher.register("remove contact", cmd_delete_contact)
    dispatcher.register("remove contract", cmd_delete_contact)
    dispatcher.register("forget contact", cmd_delete_contact)
    dispatcher.register("forget contract", cmd_delete_contact)
