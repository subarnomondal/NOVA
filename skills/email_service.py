import webbrowser
import urllib.parse
import re
import json
import os
from skills.messenger import ContactManager

# Global context for LLM
NOVA_CONTEXT = None

# Reuse the Contact Manager for phone/email if possible, but Messenger uses 'contacts.json' which stores Numbers.
# We will create a separate EmailDirectory for simplicity or extend functionality.
# For now, let's create a separate simple manager for emails.

class EmailDirectory:
    def __init__(self, email_file=os.path.join("userdata", "emails.json")):
        self.email_file = email_file
        self.emails = {}
        self.load_emails()
        
        # Default test
        if "myself" not in self.emails:
            self.add_email("myself", "user@example.com") # User should update this

    def load_emails(self):
        try:
            if os.path.exists(self.email_file):
                with open(self.email_file, 'r') as f:
                    self.emails = json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading emails: {e}")
            self.emails = {}

    def save_emails(self):
        try:
            with open(self.email_file, 'w') as f:
                json.dump(self.emails, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving emails: {e}")

    def add_email(self, name, email):
        self.emails[name.lower()] = email
        self.save_emails()
        return True

    def get_email(self, name):
        return self.emails.get(name.lower())
    
    def list_emails(self):
        return self.emails

email_manager = EmailDirectory()

def cmd_add_email(args):
    """Usage: add email <name> <address>"""
    try:
        # Simple extraction
        parts = args.replace("add email", "").strip().split(maxsplit=1)
        if len(parts) < 2:
             # Try regex for email
             email_match = re.search(r'[\w\.-]+@[\w\.-]+', args)
             if email_match:
                 email = email_match.group(0)
                 name = args.replace("add email", "").replace(email, "").strip()
             else:
                 return "I need a name and an email address! (e.g. add email John john@test.com) 📧"
        else:
             name, email = parts[0], parts[1]

        # Verify email format roughly
        if "@" not in email:
            # swap?
            if "@" in name:
                name, email = email, name
            else:
                return "That doesn't look like a valid email address!"

        email_manager.add_email(name, email)
        return f"Saved! {name.title()}'s email is now {email}."
        
    except Exception as e:
        return f"Failed to save email: {e}"

def cmd_list_emails(args):
    emails = email_manager.list_emails()
    if not emails:
        return "No emails saved yet."
    msg = "Saved Emails:\n"
    for n, e in emails.items():
        msg += f"• {n.title()}: {e}\n"
    return msg

def fetch_explanation(topic):
    """Fetch a summary from DuckDuckGo to use as explanation"""
    from duckduckgo_search import DDGS
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"explain {topic} simple", max_results=1))
            if results:
                return results[0].get('body', "")
    except:
        pass
    return f"Here is some information about {topic}."

def cmd_advanced_draft(args):
    """
    Advanced email drafting for the reasoning loop.
    Usage: draft formal email about <topic>
    """
    try:
        from core.llm_manager import llm_manager
        tone = "professional"
        if "casual" in args.lower(): tone = "casual"
        if "academic" in args.lower(): tone = "academic and formal"
        
        topic = args.replace("draft", "").replace("formal", "").replace("casual", "").replace("academic", "").replace("email", "").replace("about", "").strip()
        
        system_prompt = f"You are a professional assistant. Draft an {tone} email about the provided topic. Include a clear subject and structured body."
        draft = llm_manager.generate(f"Topic: {topic}", system_prompt=system_prompt)
        return draft if draft else "I couldn't generate a draft right now."
    except Exception as e:
        return f"Drafting Error: {e}"

def cmd_send_email(args):
    """
    Advanced Email Dispatcher with Automatic Professional Drafting.
    Usage: send email to John about the project meeting
    """
    try:
        from core.llm_manager import llm_manager
        
        # 1. Resolve Target (Recipient)
        target = None
        # Check for direct email address
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', args)
        if email_match:
            target = email_match.group(0)
            # Remove email from args to get the pure topic
            topic_pure = args.replace(target, "").replace("send email to", "").replace("mail", "").strip()
        else:
            # Check contacts
            to_match = re.search(r'to\s+([\w\s]+?)(?:\s+about|\s+saying|\s+regarding|\s+that|\s*$)', args, re.IGNORECASE)
            if to_match:
                name = to_match.group(1).strip()
                target = email_manager.get_email(name)
                topic_pure = args.split(name)[-1].strip()
            else:
                return "Who should I send this email to? 📧"

        if not target:
            return "I couldn't find that contact's email address. Try 'add email <name> <address>' first!"

        # 2. Extract/Clean Topic
        topic = topic_pure.replace("about", "").replace("saying", "").replace("regarding", "").replace("that", "").strip()
        if not topic:
            return f"What should the email to {target} be about? 📝"

        # 3. Generate Professional Draft using LLM
        print(f"📧 Drafting professional email for: {topic}")
        system_prompt = (
            "You are Nova, a professional yet friendly assistant. "
            "Draft a professional email based on the user's brief note. "
            "Structure it with 'Subject: <subject>' on the first line, followed by the body. "
            "Keep it concise, clear, and polite."
        )
        
        draft = llm_manager.generate(f"Brief Note: {topic}", system_prompt=system_prompt)
        
        if not draft or "Subject:" not in draft:
            # Fallback
            subject = f"Message regarding: {topic[:30]}..."
            body = topic
        else:
            try:
                lines = draft.strip().split('\n')
                subject_line = [l for l in lines if l.lower().startswith("subject:")][0]
                subject = subject_line.replace("Subject:", "").replace("subject:", "").strip()
                # Everything after the subject line is the body
                body = "\n".join([l for l in lines if l != subject_line]).strip()
            except:
                subject = "Professional Update"
                body = draft

        # 4. Open Mail Client
        params = {"subject": subject, "body": body}
        query_string = urllib.parse.urlencode(params).replace("+", "%20")
        mailto_link = f"mailto:{target}?{query_string}"
        
        if webbrowser.open(mailto_link):
            return f"I've prepared a professional email to {target}! 📧✨"
        else:
            return f"I couldn't open your mail client, but here is the draft:\n\n*Subject:* {subject}\n\n{body}"
        
    except Exception as e:
        print(f"❌ Email Error: {e}")
        return f"Sorry, I ran into an issue preparing that email: {str(e)}"

def register(dispatcher, nova_instance=None):
    global NOVA_CONTEXT
    if nova_instance:
        NOVA_CONTEXT = nova_instance
        
    dispatcher.register("send email", cmd_send_email)
    dispatcher.register("mail", cmd_send_email)
    dispatcher.register("explain on mail", cmd_send_email)
    dispatcher.register("write email", cmd_send_email) # New trigger for drafting
    dispatcher.register("draft email", cmd_send_email)
    dispatcher.register("add email", cmd_add_email)
    dispatcher.register("list emails", cmd_list_emails)
