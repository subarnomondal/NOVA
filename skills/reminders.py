import schedule
import time
import threading
import re
import datetime
import uuid
from skills.messenger import cmd_send_message, contact_manager

# Background thread for schedule
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

def job(msg):
    # Check if this is a WhatsApp/Message task
    lower_msg = msg.lower()
    if any(k in lower_msg for k in ["whatsapp", "message", "text", "send"]):
        print(f"⏰ EXECUTING SCHEDULED TASK: {msg}")
        # Try triggering the messenger skill
        # We assume 'msg' is something like "whatsapp to mom saying hi"
        try:
            response = cmd_send_message(msg)
            print(f"✅ Scheduled Action Result: {response}")
        except Exception as e:
            print(f"❌ Scheduled Action Failed: {e}")
    else:
        # Standard reminder
        print(f"⏰ REMINDER: {msg}")

def cmd_remind(args):
    """Usage: remind me to <action> in <N> seconds/minutes/hours OR at <time> (e.g., 6 pm)"""
    try:
        # First, try relative time pattern
        match = re.search(r"(remind me to|schedule) (.+) in (\d+) (second|minute|hour)s?", args, re.IGNORECASE)
        if match:
            action = match.group(2)
            amount = int(match.group(3))
            unit = match.group(4).lower()
            
            if "second" in unit:
                schedule.every(amount).seconds.do(job, action).tag("reminder")
            elif "minute" in unit:
                schedule.every(amount).minutes.do(job, action).tag("reminder")
            elif "hour" in unit:
                schedule.every(amount).hours.do(job, action).tag("reminder")
                
            import random
            responses = [
                f"You got it! I'll remind you to '{action}' in {amount} {unit}(s). ⏰",
                f"Perfect! '{action}' is now on your schedule for {amount} {unit}(s) from now. ✅",
                f"Done! I've set a reminder for '{action}' in {amount} {unit}(s). I've got your back! 💪"
            ]
            return random.choice(responses)
        # Next, try absolute time pattern like "at 6 pm" or "at 18:30"
        abs_match = re.search(r"(remind me to|schedule) (.+) at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?", args, re.IGNORECASE)
        if abs_match:
            action = abs_match.group(2)
            hour = int(abs_match.group(3))
            minute = int(abs_match.group(4)) if abs_match.group(4) else 0
            meridiem = abs_match.group(5)
            now = datetime.datetime.now()
            if meridiem:
                meridiem = meridiem.lower()
                if meridiem == "pm" and hour < 12:
                    hour += 12
                if meridiem == "am" and hour == 12:
                    hour = 0
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)
            delta_seconds = int((target - now).total_seconds())
            schedule.every(delta_seconds).seconds.do(job, action).tag("reminder")
            
            # Feature: Notify Contact on WhatsApp (User Request: "answering on whatsapp when shidule are making")
            # Check if action involves a person: "meeting with John", "call Mom"
            notify_msg = ""
            # Improved regex to catch "meet Mom" or "meet with Mom" or "call Mom"
            # Captures word characters following the keyword
            person_match = re.search(r'(?:with|call|meet|text|message)\s+(?:\w+\s+)?([a-zA-Z]+)', action, re.IGNORECASE)
            
            if person_match:
                person = person_match.group(1)
                # Check if contact exists
                number = contact_manager.get_number(person)
                if number:
                    # Construct notification
                    notification = f"Hi {person.title()}! Just letting you know I've scheduled: '{action}' at {hour:02d}:{minute:02d}. See you then!"
                    print(f"🔔 Attempting to notify {person} ({number})...")
                    try:
                        # We direct invoke the messenger command string which handles the logic
                        # But simpler: we have the NUMBER. We should construct the command precisely.
                        # "whatsapp to <NUMBER> saying <MSG>" is most robust.
                        cmd_send_message(f"whatsapp to {number} saying {notification}")
                        notify_msg = f" (I also sent a WhatsApp to {person} to let them know!)"
                        print("✅ Notification sent.")
                    except Exception as e:
                        print(f"❌ Notification Failed: {e}")
                        notify_msg = " (I tried to WhatsApp them, but something went wrong.)"
                else:
                    print(f"⚠️ Contact '{person}' not found in address book.")
            
            import random
            responses = [
                f"Got it! I'll remind you to '{action}' at {hour:02d}:{minute:02d}. ⏰{notify_msg}",
                f"Scheduled '{action}' for {hour:02d}:{minute:02d}. ✅{notify_msg}",
                f"Reminder set for '{action}' at {hour:02d}:{minute:02d}.{notify_msg}"
            ]
            return random.choice(responses)
        # If no pattern matched
        return "I'd love to help you schedule something! Just let me know what and when - like 'remind me to call mom in 10 minutes' 😊"
            
    except Exception as e:
        return f"Oops, I had a little trouble setting that up. Here's what happened: {e}"

def cmd_list_schedule(args):
    """Usage: show my schedule"""
    jobs = schedule.get_jobs("reminder")
    if not jobs:
        import random
        responses = [
            "Your schedule's all clear! Want me to add something? 📅",
            "Nothing on the schedule right now. Need me to set up a reminder? ✨",
            "All free at the moment! What would you like to schedule? 😊"
        ]
        return random.choice(responses)
    
    
    # Simple list of pending jobs
    response = "Here’s what’s on your schedule:\n"
    for j in jobs:
        # Extract job detail if possible
        response += f"- {str(j.job_func.args[0])} (Coming up next)\n"
    return response

# API Functions for UI
def get_all_jobs():
    jobs = schedule.get_jobs("reminder")
    job_list = []
    for j in jobs:
        # schedule library doesn't expose stable IDs by default easily, 
        # but we can use the object id or tags if we manage them.
        # Ideally, we should wrap jobs in a class with IDs.
        # For simple workaround, we refer by index or a hash of the job object, 
        # but index is unstable if one runs.
        # However, schedule doesn't support 'get by id'.
        # We will use valid index for deletion, or just return basic info.
        
        # We will assign a custom attribute if possible, or just generate a list
        # that client can use to display. Deletion is tricky without IDs.
        
        # Better approach: We wrap adding jobs to store them in a dict with ID.
        action = str(j.job_func.args[0])
        next_run = str(j.next_run)
        job_list.append({
            "action": action,
            "next_run": next_run,
            # We will use the job object's memory address as a temporary ID for deletion 
            # (risky but works for runtime) or tag.
            "id": uuid.uuid4().hex 
        })
    return job_list

def cancel_job_by_id(job_id):
    jobs = schedule.get_jobs("reminder")
    for j in jobs:
        if uuid.uuid4().hex == job_id:
            schedule.cancel_job(j)
            return True
    return False

def register(dispatcher):
    dispatcher.register("remind", cmd_remind)
    dispatcher.register("schedule", cmd_remind)
    dispatcher.register("my schedule", cmd_list_schedule)
    dispatcher.register("list schedule", cmd_list_schedule)
    dispatcher.register("what's next", cmd_list_schedule)

