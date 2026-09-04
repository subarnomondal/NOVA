"""
PersonalBrain — CLIO's unified personal knowledge hub.

Single source of truth for everything Clio knows about the user.
Merges: user_profile.json + user_facts.json + brain.json (goals, mood, life events).

Usage:
    from core.personal_brain import personal_brain
    context = personal_brain.get_rich_context()          # inject into system prompt
    personal_brain.log_life_event("started gym", "motivated", ["health", "fitness"])
    personal_brain.add_goal("Wake up at 6am", goal_type="habit")
    personal_brain.learn_from_exchange(user_text, clio_text)  # auto-extract facts
"""

import json
import os
import time
import re
from datetime import datetime, date
from typing import Optional

_BRAIN_FILE = os.path.join("userdata", "brain.json")
_PROFILE_FILE = os.path.join("userdata", "user_profile.json")
_FACTS_FILE = os.path.join("userdata", "user_facts.json")

_EMPTY_BRAIN = {
    "life_events": [],
    "goals": [],
    "mood_log": []
}


class PersonalBrain:
    """Unified personal knowledge hub. Use the module-level singleton `personal_brain`."""

    def __init__(self):
        self._brain: dict = {}
        self._profile: dict = {}
        self._facts: dict = {}
        self._load()

    # ------------------------------------------------------------------ load/save

    def _load(self):
        self._brain = self._read_json(_BRAIN_FILE, _EMPTY_BRAIN.copy())
        self._profile = self._read_json(_PROFILE_FILE, {})
        self._facts = self._read_json(_FACTS_FILE, {})

    def _read_json(self, path: str, default: dict) -> dict:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default

    def _save_brain(self):
        os.makedirs(os.path.dirname(_BRAIN_FILE), exist_ok=True)
        with open(_BRAIN_FILE, "w", encoding="utf-8") as f:
            json.dump(self._brain, f, indent=2, ensure_ascii=False)

    def _save_facts(self):
        os.makedirs(os.path.dirname(_FACTS_FILE), exist_ok=True)
        with open(_FACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._facts, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------ profile helpers

    def get_name(self) -> str:
        from core.user_profile import user_profile
        return user_profile.get_name()

    def get_profile_field(self, *keys, default=""):
        """Safely navigate nested profile keys."""
        val = self._profile
        for k in keys:
            if not isinstance(val, dict):
                return default
            val = val.get(k, default)
        return val if val != "" else default

    # ------------------------------------------------------------------ goals & habits

    def add_goal(self, title: str, goal_type: str = "habit", target: str = "") -> dict:
        """Add or update a goal/habit. Returns the goal dict."""
        # Deduplicate by title (case-insensitive)
        existing = next(
            (g for g in self._brain.get("goals", [])
             if g["title"].lower() == title.lower()),
            None
        )
        if existing:
            existing["target"] = target or existing.get("target", "")
            self._save_brain()
            return existing

        goal = {
            "id": f"g_{int(time.time())}",
            "title": title,
            "type": goal_type,      # "daily" | "habit" | "milestone"
            "target": target,
            "streak": 0,
            "last_checked": None,
            "done_today": False,
            "created": date.today().isoformat()
        }
        self._brain.setdefault("goals", []).append(goal)
        self._save_brain()
        print(f"🎯 PersonalBrain: Goal added — {title}")
        return goal

    def mark_goal_done(self, goal_id_or_title: str) -> bool:
        """Mark a goal as done for today and update streak."""
        today = date.today().isoformat()
        for g in self._brain.get("goals", []):
            if g["id"] == goal_id_or_title or g["title"].lower() == goal_id_or_title.lower():
                if g.get("last_checked") != today:
                    g["streak"] = g.get("streak", 0) + 1
                    g["last_checked"] = today
                g["done_today"] = True
                self._save_brain()
                return True
        return False

    def get_goals_summary(self) -> str:
        """Compact goals string for system prompt injection."""
        goals = self._brain.get("goals", [])
        if not goals:
            return ""

        today = date.today().isoformat()
        lines = []
        for g in goals:
            status = "✅" if g.get("done_today") and g.get("last_checked") == today else "⏳"
            streak = f" (streak: {g['streak']} days)" if g.get("streak", 0) > 0 else ""
            lines.append(f"{status} [{g['type'].upper()}] {g['title']}{streak}")

        return "ACTIVE GOALS & HABITS:\n" + "\n".join(lines)

    # ------------------------------------------------------------------ life events & mood

    def log_life_event(self, event: str, mood: str = "neutral", tags: Optional[list] = None):
        """Persist a diary-style life event."""
        entry = {
            "date": datetime.now().isoformat()[:10],
            "event": event,
            "mood": mood,
            "tags": tags or []
        }
        self._brain.setdefault("life_events", []).append(entry)
        # Cap at 200 events
        if len(self._brain["life_events"]) > 200:
            self._brain["life_events"] = self._brain["life_events"][-200:]
        self._save_brain()
        print(f"📔 PersonalBrain: Life event logged — {event[:60]}")

    def log_mood(self, mood: str, note: str = ""):
        """Log today's mood."""
        entry = {
            "date": datetime.now().isoformat()[:10],
            "mood": mood,
            "note": note
        }
        log = self._brain.setdefault("mood_log", [])
        # Replace today's entry if already exists
        today = entry["date"]
        log[:] = [e for e in log if e.get("date") != today]
        log.append(entry)
        if len(log) > 90:
            self._brain["mood_log"] = log[-90:]
        self._save_brain()

    def get_recent_mood(self) -> str:
        """Latest mood entry as a short string."""
        log = self._brain.get("mood_log", [])
        if not log:
            return ""
        last = log[-1]
        return f"{last['mood']} (as of {last['date']})"

    def get_recent_life_events(self, n: int = 5) -> str:
        """Last N life events as a string."""
        events = self._brain.get("life_events", [])
        if not events:
            return ""
        recent = events[-n:]
        lines = [f"[{e['date']}] {e['event']} (mood: {e.get('mood', '?')})" for e in recent]
        return "RECENT LIFE EVENTS:\n" + "\n".join(lines)

    # ------------------------------------------------------------------ fact learning

    def learn_from_exchange(self, user_text: str, clio_text: str = ""):
        """
        Auto-extract personal facts from a conversation turn.
        Routes through LTMManager for storage.
        """
        try:
            from core.ltm_manager import LTMManager
            ltm = LTMManager()
            ltm.auto_extract_facts(user_text)

            # Also scan clio_text for goal-relevant keywords and mood signals
            self._detect_goal_mentions(user_text)
            self._detect_mood(user_text)
        except Exception as e:
            print(f"⚠️ PersonalBrain.learn_from_exchange: {e}")

    def _detect_goal_mentions(self, text: str):
        """Detect if user is setting a new goal/habit from their message."""
        text_l = text.lower()
        goal_patterns = [
            r"i want to (?:start|begin|try) (.+?)(?:\.|$)",
            r"my goal is to (.+?)(?:\.|$)",
            r"i(?:'m| am) trying to (.+?)(?:\.|$)",
            r"i need to (?:start|begin) (.+?)(?:\.|$)",
            r"help me (?:with |to )?(.+?) (?:every day|daily|each day)",
            r"remind me to (.+?) (?:every day|daily|each day|every morning|every night)",
        ]
        for pattern in goal_patterns:
            m = re.search(pattern, text_l)
            if m:
                candidate = m.group(1).strip()
                # Filter noise
                if 5 < len(candidate) < 80 and candidate not in ("this", "that", "it"):
                    self.add_goal(candidate.capitalize(), goal_type="habit")
                    break  # one goal per message

    def _detect_mood(self, text: str):
        """Lightweight mood detection from user text."""
        text_l = text.lower()
        mood_map = {
            "stressed": ["stressed", "stress", "anxious", "anxiety", "worried", "overwhelmed"],
            "happy": ["happy", "great", "awesome", "excited", "fantastic", "amazing"],
            "sad": ["sad", "depressed", "down", "unhappy", "upset", "crying"],
            "tired": ["tired", "exhausted", "sleepy", "fatigue", "drained"],
            "motivated": ["motivated", "inspired", "pumped", "ready", "focused"],
            "bored": ["bored", "boring", "nothing to do"],
            "angry": ["angry", "mad", "furious", "pissed", "annoyed"],
        }
        for mood, keywords in mood_map.items():
            if any(kw in text_l for kw in keywords):
                self.log_mood(mood, note=text[:120])
                break

    # ------------------------------------------------------------------ main context builder

    def get_rich_context(self) -> str:
        """
        Returns a dense, personalized context string for LLM system prompt injection.
        Called once per generate() call in llm_manager.

        Returns empty string when strict_privacy=true — no personal data goes to cloud APIs.
        """
        self._load()  # Refresh from disk (cheap — files are small)

        # Privacy gate: if strict_privacy is on, never send personal data to cloud LLMs
        if self._profile.get("preferences", {}).get("strict_privacy", True):
            return ""

        parts = []

        # --- Core Identity ---
        name = self.get_name()
        birthday = self.get_profile_field("personal_info", "birthday")
        location = self.get_profile_field("personal_info", "location")
        occupation = self.get_profile_field("personal_info", "occupation")
        gender = self.get_profile_field("personal_info", "gender")
        life_context = self.get_profile_field("personal_info", "life_context")
        relationship = self.get_profile_field("personal_info", "relationship_status")

        identity_lines = [f"- Name: {name}"]
        if birthday:
            identity_lines.append(f"- Birthday: {birthday}")
        if location:
            identity_lines.append(f"- Location: {location}")
        if occupation:
            identity_lines.append(f"- Occupation: {occupation}")
        if gender:
            identity_lines.append(f"- Gender: {gender}")
        if relationship:
            identity_lines.append(f"- Relationship: {relationship}")
        if life_context:
            identity_lines.append(f"- About them: {life_context}")

        parts.append("PERSONAL PROFILE (Your user — treat this as sacred knowledge):\n" + "\n".join(identity_lines))

        # --- Interests from profile ---
        interests = self.get_profile_field("personal_info", "interests", default=[])
        if interests and isinstance(interests, list):
            parts.append(f"INTERESTS: {', '.join(interests[:8])}")

        # --- LTM Facts ---
        try:
            from core.ltm_manager import LTMManager
            ltm = LTMManager()
            facts_str = ltm.get_summary_for_prompt()
            if facts_str.strip():
                parts.append(facts_str.strip())
        except Exception:
            pass

        # --- Goals & Habits ---
        goals_str = self.get_goals_summary()
        if goals_str:
            parts.append(goals_str)

        # --- Current Mood ---
        mood = self.get_recent_mood()
        if mood:
            parts.append(f"CURRENT MOOD: {mood}")

        # --- Recent Life Events ---
        events_str = self.get_recent_life_events(n=3)
        if events_str:
            parts.append(events_str)

        if not parts:
            return ""

        header = "\n\n--- CLIO PERSONAL BRAIN (Your living knowledge of this person) ---\n"
        footer = "\n--- END PERSONAL BRAIN ---\n\n"
        body = "\n\n".join(parts)
        return header + body + footer

    # ------------------------------------------------------------------ convenience

    def get_goals(self) -> list:
        """Return all goals."""
        return self._brain.get("goals", [])

    def delete_goal(self, title: str) -> bool:
        goals = self._brain.get("goals", [])
        before = len(goals)
        self._brain["goals"] = [g for g in goals if g["title"].lower() != title.lower()]
        if len(self._brain["goals"]) < before:
            self._save_brain()
            return True
        return False


# Module-level singleton — import this everywhere
personal_brain = PersonalBrain()
