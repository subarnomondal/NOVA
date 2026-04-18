import json
import os
import sys

# Add parent directory to path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.domain_knowledge import DomainKnowledge
from core.neural_chat import NeuralChat

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def add_fact():
    print("\n--- 📚 Add New Fact ---")
    dk = DomainKnowledge()
    
    print("\nExisting Domains:", ", ".join(dk.domains.keys()))
    domain = input("Enter Domain (or new domain name): ").strip().lower()
    
    topic = input("Enter Topic (e.g., 'Mars Capital'): ").strip()
    fact = input("Enter Fact (e.g., 'Muskville'): ").strip()
    
    if domain and topic and fact:
        dk.add_knowledge(domain, topic, fact)
        print("✅ Fact added successfully!")
    else:
        print("❌ All fields are required.")
    
    input("\nPress Enter to continue...")

def add_conversation():
    print("\n--- 💬 Add New Conversation Pattern ---")
    
    tag = input("Enter Intent Tag (e.g., 'greeting_morning'): ").strip().lower()
    
    patterns = []
    print("Enter Patterns (User inputs). Type 'done' when finished.")
    while True:
        p = input("> ").strip()
        if p.lower() == 'done': break
        if p: patterns.append(p)
        
    responses = []
    print("Enter Responses (AI replies). Type 'done' when finished.")
    while True:
        r = input("> ").strip()
        if r.lower() == 'done': break
        if r: responses.append(r)
        
    if tag and patterns and responses:
        # Load existing intents
        intents_file = os.path.join("userdata", "intents.json")
        
        try:
            os.makedirs(os.path.dirname(intents_file), exist_ok=True)
            with open(intents_file, 'r') as f:
                data = json.load(f)
        except:
            data = {"intents": []}
            
        # Check if tag exists
        found = False
        for intent in data['intents']:
            if intent['tag'] == tag:
                intent['patterns'].extend(patterns)
                intent['responses'].extend(responses)
                found = True
                print(f"Updated existing tag '{tag}'.")
                break
        
        if not found:
            data['intents'].append({
                "tag": tag,
                "patterns": patterns,
                "responses": responses
            })
            print(f"Created new tag '{tag}'.")
            
        with open(intents_file, 'w') as f:
            json.dump(data, f, indent=4)
            
        print("\n🔄 Retraining Neural Network...")
        chat = NeuralChat()
        chat.train(epochs=500) # Quick retrain
        print("✅ Training Complete!")
        
    else:
        print("❌ Missing data.")
        
    input("\nPress Enter to continue...")

def main():
    while True:
        clear_screen()
        print("🧠 NOVA Knowledge Trainer 🧠")
        print("1. Add Fact (Domain Knowledge)")
        print("2. Add Conversation (Intents & Neural Training)")
        print("3. Exit")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            add_fact()
        elif choice == '2':
            add_conversation()
        elif choice == '3':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
