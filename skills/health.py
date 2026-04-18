"""
Health, Diet & Medical Intelligence Skill for Nova
Provides grounded medical advice, dietary plans, and nutritional information.
"""

from duckduckgo_search import DDGS
import random
import re
import json
import os
import warnings

# Suppress the ddgs rename warning specifically
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*renamed to ddgs.*")

def cmd_health_advice(args):
    """Usage: health advice <topic> or tell me about <symptom>"""
    query = args.lower().replace("health advice", "").replace("medical info", "").replace("tell me about", "").strip()
    
    if not query:
        return "*adjusts glasses* You haven't specified what health topic you're interested in. I need a subject to provide a consultation. 🩺"

    # 1. Search Knowledge Base First (for grounded facts)
    kb_path = os.path.join("userdata", "domain_knowledge.json")
    kb_fact = ""
    if os.path.exists(kb_path):
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb = json.load(f)
            health_facts = kb.get("health", {}).get("facts", {})
            for key, val in health_facts.items():
                if key.lower() in query or query in key.lower():
                    kb_fact = val
                    break

    # 2. Web Search for deeper info
    search_query = f"{query} medical facts health advice recovery diet"
    print(f"🏥 Health Search: {search_query}")
    
    web_snippet = ""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, region='in-en', max_results=3))
            if results:
                web_snippet = results[0]['body']
    except Exception as e:
        print(f"Health Search Error: {e}")

    # 3. Construct Evidence Block
    evidence = ""
    if kb_fact:
        evidence += f"KNOWLEDGE BASE: {kb_fact}\n"
    if web_snippet:
        evidence += f"MEDICAL RESEARCH: {web_snippet}\n"

    if not evidence:
         return f"I couldn't find specific medical data for '{query}'. Please consult a local professional for serious concerns! 🏥"

    # The LLM will use this as context via the dispatcher
    return f"[EVIDENCE: {evidence}] Based on my medical training, here is a detailed analysis for '{query}':"

def cmd_diet_plan(args):
    """Usage: diet plan <goal> (e.g., weight loss, muscle gain)"""
    goal = args.lower().replace("diet plan", "").replace("meal plan", "").strip()
    
    if not goal:
        return "What is your health goal? I can design a plan for weight loss, muscle gain, or general wellness. 🥗"

    # Grounding for diet
    search_query = f"{goal} healthy diet plan calories macros"
    evidence = ""
    try:
         with DDGS() as ddgs:
            results = list(ddgs.text(search_query, region='in-en', max_results=3))
            if results:
                evidence = results[0]['body']
    except Exception as e:
        print(f"Diet Search Error: {e}")

    # Designing table format prompt for LLM
    return f"[EVIDENCE: {evidence}] I've designed a specialized diet plan focused on {goal}. Respond with a clean Markdown table including columns for Meal, Food Item, and Nutritional Benefit. *looks at you strictly* You better stick to it!"

def register(dispatcher):
    dispatcher.register("health advice", cmd_health_advice)
    dispatcher.register("medical info", cmd_health_advice)
    dispatcher.register("check symptoms", cmd_health_advice)
    dispatcher.register("diet plan", cmd_diet_plan)
    dispatcher.register("meal plan", cmd_diet_plan)
    dispatcher.register("nutrition", cmd_diet_plan)
