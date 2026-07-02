"""
Language & Vocabulary Tutor Skill for NOVA
Assists with translation, grammar, and linguistic growth.
"""

import json
import os
import random
from duckduckgo_search import DDGS

# Path for user language progress
LANGUAGE_DATA_PATH = os.path.join("userdata", "user_language_progress.json")

def load_language_data():
    if os.path.exists(LANGUAGE_DATA_PATH):
        try:
            with open(LANGUAGE_DATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading language data: {e}")
    return {"favorite_words": [], "last_wotd": None}

def save_language_data(data):
    try:
        os.makedirs("userdata", exist_ok=True)
        with open(LANGUAGE_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"⚠️ Error saving language data: {e}")

def cmd_word_of_the_day(args):
    """Usage: word of the day"""
    lang = "English"
    if "in" in args.lower():
        lang = args.lower().split("in", 1)[1].strip()
    
    try:
        from core.llm_manager import llm_manager
        
        print(f"🧠 Generating Word of the Day in {lang}...")
        prompt = (
            f"Generate a 'Word of the Day' in {lang}. Include: "
            "1. The Word, 2. Part of speech, 3. Definition, 4. Example sentence. "
            "Keep it professional and academic."
        )
        wotd = llm_manager.generate(prompt, raw_gen=False)
        
        return f"🌟 **Word of the Day ({lang.title()}):**\n\n{wotd}\n\n*Keep learning!* 📚"
    except Exception as e:
        return f"Language Error: {e}"

def cmd_translate(args):
    """Usage: translate <text> to <lang>"""
    if " to " not in args.lower():
        return "Please specify the language like: 'translate hello to Spanish'. 🌐"
    
    parts = re.split(r' to ', args, flags=re.IGNORECASE)
    text = parts[0].replace("translate", "").strip()
    lang = parts[1].strip()
    
    try:
        from core.llm_manager import llm_manager
        
        print(f"🌐 Translating '{text}' to {lang}...")
        system_prompt = (
            f"You are a professional translator. Translate the text to {lang}. "
            "Provide the translation and a brief explanation of the context or grammar if necessary."
        )
        translation = llm_manager.generate(f"Translate: {text}", system_prompt=system_prompt)
        
        return f"🌍 **Translation to {lang.title()}:**\n\n{translation}"
    except Exception as e:
        return f"Translation Error: {e}"

import re

def cmd_grammar_check(args):
    """Usage: grammar check <sentence>"""
    sentence = args.lower().replace("grammar check", "").replace("check grammar", "").strip()
    if not sentence:
        return "What sentence should I check? ✍️"
    
    try:
        from core.llm_manager import llm_manager
        
        print(f"✍️ Checking grammar: {sentence}")
        system_prompt = (
            "You are a linguistic expert. Check the grammar of the provided sentence. "
            "If it's correct, say so. If there are errors, correct them and explain why."
        )
        check = llm_manager.generate(f"Sentence: {sentence}", system_prompt=system_prompt)
        
        return f"🔍 **Grammar Analysis:**\n\n{check}"
    except Exception as e:
        return f"Grammar Error: {e}"

def register(dispatcher):
    dispatcher.register("word of the day", cmd_word_of_the_day)
    dispatcher.register("wotd", cmd_word_of_the_day)
    dispatcher.register("learn word", cmd_word_of_the_day)
    
    dispatcher.register("translate", cmd_translate)
    dispatcher.register("translate to", cmd_translate)
    
    dispatcher.register("grammar check", cmd_grammar_check)
    dispatcher.register("check grammar", cmd_grammar_check)
    dispatcher.register("fix sentence", cmd_grammar_check)
