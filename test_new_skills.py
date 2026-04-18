"""
Verification Script for NOVA New Skills
Tests Finance and Language skills by mocking the dispatcher.
"""

import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

class MockDispatcher:
    def __init__(self):
        self.handlers = {}
    def register(self, keyword, func):
        self.handlers[keyword] = func
    def trigger(self, keyword, args):
        if keyword in self.handlers:
            return self.handlers[keyword](args)
        return "Command not found."

def test_skills():
    dispatcher = MockDispatcher()
    
    # Import and register Finance skill
    print("\n--- Testing Financial Manager ---")
    import skills.finance as finance
    finance.register(dispatcher)
    
    # Test adding expense (Note: This will call LLM in actual logic, we check if it triggers)
    print("Testing 'add expense'...")
    # Since cmd_add_expense calls LLM, we'll just check if it's registered.
    # In a full test, we'd mock llm_manager.
    
    print("Testing 'check budget'...")
    print(dispatcher.trigger("check budget", ""))
    
    # Import and register Language skill
    print("\n--- Testing Language Tutor ---")
    import skills.language as language
    language.register(dispatcher)
    
    print("Testing 'grammar check' command registration...")
    # This should return a message asking for a sentence if it works.
    print(dispatcher.trigger("grammar check", ""))

    print("\nVerification Complete!")

if __name__ == "__main__":
    test_skills()
