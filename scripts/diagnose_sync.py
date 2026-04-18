import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.assistant import Nova

def diagnose_sync():
    print("🔍 Diagnosing UI/Core Sync Issue...")
    nova = Nova()
    
    # Test with a simple request
    test_input = "Hello, how are you?"
    
    print(f"\n[INPUT]: {test_input}")
    print("\n" + "="*60)
    
    response = nova.handle_input(test_input)
    
    print("\n[RAW RESPONSE]:")
    print(response)
    print("\n" + "="*60)
    
    print(f"\n[RESPONSE TYPE]: {type(response)}")
    print(f"[RESPONSE LENGTH]: {len(response) if response else 0} characters")
    
    # Check if reasoning log is present
    if response and "> **Reasoning Process:**" in response:
        print("\n✅ Reasoning log IS present in response")
    else:
        print("\n❌ Reasoning log NOT found in response")
    
    # Check for thought tags
    if response and ("<thought>" in response.lower() or "<THOUGHT>" in response):
        print("⚠️ WARNING: Thought tags still present (not cleaned)")
    else:
        print("✅ Thought tags properly cleaned")

if __name__ == "__main__":
    diagnose_sync()
