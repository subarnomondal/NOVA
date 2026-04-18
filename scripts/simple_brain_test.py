"""
Simple test to verify local brain works without complex loading
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.llm_manager import LLMManager

def simple_test():
    print("🧪 Simple Local Brain Test\n")
    
    llm = LLMManager()
    print(f"Show Thoughts: {llm.show_thoughts}")
    
    # Test with a simple prompt
    print("\n📝 Testing generation...")
    response = llm.generate(
        "Hello! Who are you?",
        max_tokens=100,
        temperature=0.7
    )
    
    print(f"\n✅ Response:\n{response}\n")
    
    if response:
        if "<thought>" in response.lower() or "<THOUGHT>" in response:
            print("✅ Thought tags detected!")
        else:
            print("⚠️ No thought tags in response (model may not be following instruction)")
        print("\n✅ Local brain is working!")
    else:
        print("❌ No response generated")

if __name__ == "__main__":
    simple_test()
