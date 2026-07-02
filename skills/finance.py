"""
Financial Manager Skill for NOVA
Provides expense tracking, budgeting, and currency conversion.
"""

import json
import os
import re
import datetime
from duckduckgo_search import DDGS

# Path for user financial data
FINANCE_DATA_PATH = os.path.join("userdata", "user_finance.json")

def load_finance_data():
    if os.path.exists(FINANCE_DATA_PATH):
        try:
            with open(FINANCE_DATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading finance data: {e}")
    return {"expenses": [], "budgets": {}}

def save_finance_data(data):
    try:
        os.makedirs("userdata", exist_ok=True)
        with open(FINANCE_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"⚠️ Error saving finance data: {e}")

def cmd_add_expense(args):
    """Usage: add expense <amount> for <item> or <item> costing <amount>"""
    try:
        from core.llm_manager import llm_manager
        
        # Use LLM to extract amount and item for better natural language support
        system_prompt = (
            "Extract the expense amount and the item/category from the user's input. "
            "Respond in JSON format: {\"amount\": float, \"item\": \"string\"}. "
            "If no amount is found, return {\"error\": \"no_amount\"}."
        )
        extraction = llm_manager.generate(f"User input: {args}", system_prompt=system_prompt, raw_gen=True)
        
        try:
            # Clean extraction for JSON parsing
            clean_json = extraction.strip() if extraction else "{}"
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
            result = json.loads(clean_json)
        except (json.JSONDecodeError, ValueError, KeyError):
            return "I couldn't quite catch the amount. Could you say it like 'add expense 50 for lunch'?"

        if "error" in result:
            return "What was the amount for this expense? I need a number to track it! "

        amount = result["amount"]
        item = result["item"]
        
        data = load_finance_data()
        entry = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "item": item
        }
        # Ensure expenses is a list
        if not isinstance(data.get("expenses"), list):
            data["expenses"] = []
        data["expenses"].append(entry)
        save_finance_data(data)
        
        return f"Got it! Recorded {amount} for '{item}'. Your wallet is watching! "
        
    except Exception as e:
        return f"Finance Error: {e}"

def cmd_check_budget(args):
    """Usage: check budget or how much did I spend?"""
    data = load_finance_data()
    expenses = data.get("expenses", [])
    
    if not expenses:
        return "You haven't recorded any expenses yet. Your bank account is safe... for now! ✨"
    
    total = sum(e["amount"] for e in expenses)
    recent = expenses[-5:]
    
    msg = f" **Financial Summary**\nTotal Spending: **{total:.2f}**\n\n**Recent Transactions:**\n"
    for e in reversed(recent):
        msg += f"• {e['date'].split(' ')[0]}: {e['amount']} - {e['item']}\n"
        
    if len(expenses) > 5:
        msg += "\n*and more...*"
        
    return msg

def cmd_currency_convert(args):
    """Usage: convert 50 USD to INR"""
    query = args.lower().replace("convert", "").strip()
    if not query:
        return "Which currencies should I convert? (e.g., '50 USD to INR') "
    
    try:
        from core.llm_manager import llm_manager
        
        # Use LLM with DDGS evidence for real-time rates
        search_query = f"currency exchange rate {query}"
        evidence = ""
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, region='in-en', max_results=2))
            if results:
                evidence = results[0]['body']
        
        prompt = f"[EVIDENCE: {evidence}] Perform the currency conversion: {query}. Output ONLY the numeric result and currency."
        result = llm_manager.generate(prompt, raw_gen=True)
        
        result_str = result.strip() if result else "unknown"
        return f" **Conversion:** {result_str}"
    except Exception as e:
        return f"Currency Error: {e}"

def register(dispatcher):
    dispatcher.register("add expense", cmd_add_expense)
    dispatcher.register("record expense", cmd_add_expense)
    dispatcher.register("track spending", cmd_add_expense)
    dispatcher.register("spent", cmd_add_expense)
    
    dispatcher.register("check budget", cmd_check_budget)
    dispatcher.register("show expenses", cmd_check_budget)
    dispatcher.register("how much did i spend", cmd_check_budget)
    dispatcher.register("spending summary", cmd_check_budget)
    
    dispatcher.register("convert currency", cmd_currency_convert)
    dispatcher.register("convert", cmd_currency_convert)
    dispatcher.register("exchange rate", cmd_currency_convert)
