"""
Correction Manager for NOVA
Detects when user is correcting NOVA, fact-checks corrections, and learns from them
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, Optional, Tuple
from duckduckgo_search import DDGS

class CorrectionManager:
    def __init__(self, corrections_file=os.path.join("userdata", "corrections.json")):
        self.corrections_file = corrections_file
        self.corrections = self._load_corrections()
        
        # Phrases that indicate user is making a correction
        self.correction_indicators = [
            "that's wrong", "that's incorrect", "not accurate", "that's not right",
            "actually", "in fact", "correction", "you're wrong", "no,", "nope,",
            "not true", "false", "incorrect", "mistake", "error in that",
            "let me correct you", "to correct you", "i need to correct",
            "that statement isn't accurate", "did not become", "was not", "were not"
        ]
    
    def _load_corrections(self) -> Dict:
        """Load previous corrections from file"""
        if os.path.exists(self.corrections_file):
            try:
                with open(self.corrections_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"corrections": []}
        return {"corrections": []}
    
    def save_corrections(self):
        """Save corrections to file"""
        with open(self.corrections_file, 'w', encoding='utf-8') as f:
            json.dump(self.corrections, f, indent=2, ensure_ascii=False)
    
    def is_correction(self, user_input: str, nova_last_response: str = "") -> bool:
        """Detect if user is making a correction"""
        user_lower = user_input.lower()
        
        # Check for explicit correction phrases
        for indicator in self.correction_indicators:
            if indicator in user_lower:
                return True
        
        # Check for contradicting patterns like "X did not Y" or "X was not Y"
        contradiction_patterns = [
            r"did not \w+",
            r"was not \w+",
            r"were not \w+",
            r"didn't \w+",
            r"wasn't \w+",
            r"weren't \w+"
        ]
        
        for pattern in contradiction_patterns:
            if re.search(pattern, user_lower):
                return True
        
        return False
    
    def extract_correction(self, user_input: str) -> Optional[str]:
        """Extract the corrected fact from user's message"""
        # Remove correction indicators to get the core fact
        clean_input = user_input
        for indicator in self.correction_indicators:
            clean_input = clean_input.replace(indicator, "").strip()
        
        # Remove leading punctuation and common sentence starters
        clean_input = re.sub(r"^[,.:;!?\s]+", "", clean_input)
        clean_input = re.sub(r"^(well|so|but|and|also)\s+", "", clean_input, flags=re.IGNORECASE)
        
        return clean_input.strip() if len(clean_input) > 10 else None
    
    def fact_check(self, statement: str) -> Tuple[bool, str]:
        """Use DuckDuckGo to verify the correction"""
        try:
            # Search for the statement
            with DDGS() as ddgs:
                results = list(ddgs.text(statement, max_results=3))
            
            if not results:
                return False, "No search results found"
            
            # Extract snippets from top results
            evidence = ""
            for i, result in enumerate(results[:2], 1):
                evidence += f"Source {i}: {result.get('body', '')[:200]}...\n"
            
            # Simple heuristic: If the statement appears in search results, consider it verified
            statement_lower = statement.lower()
            for result in results:
                body = result.get('body', '').lower()
                title = result.get('title', '').lower()
                
                # Check if key parts of the statement appear in results
                if any(word in body or word in title for word in statement_lower.split() if len(word) > 4):
                    return True, evidence
            
            return False, "Could not verify this claim"
            
        except Exception as e:
            print(f"⚠️ Fact check error: {e}")
            # If search fails, assume user is right (benefit of doubt)
            return True, "Search unavailable, accepted by default"
    
    def store_correction(self, original_claim: str, correction: str, verified: bool, evidence: str):
        """Store the correction for future reference"""
        correction_entry = {
            "timestamp": datetime.now().isoformat(),
            "original_claim": original_claim,
            "correction": correction,
            "verified": verified,
            "evidence": evidence[:500] if evidence else ""  # Limit evidence length
        }
        
        self.corrections["corrections"].append(correction_entry)
        self.save_corrections()
        print(f"✅ Stored correction: {correction[:50]}...")
    
    def get_correction_response(self, correction: str, verified: bool, evidence: str, personality: str = "alya") -> str:
        """Generate appropriate response to correction"""
        
        if personality in ["nova", "sweetheart", "friendly"]:
            if verified:
                responses = [
                    f"*adjusts glasses* You're absolutely right! {correction} I've updated my knowledge. Thank you for teaching me! ✨",
                    f"*blushes* Ah, I was wrong... {correction} I'll remember this! Thanks for the correction. 😊",
                    f"*nods* You're correct! {correction} I've learned something new today. Thank you! 🌹"
                ]
            else:
                responses = [
                    f"*looks uncertain* Hmm, I fact-checked that and found some conflicting information. Are you absolutely sure? 🤔",
                    f"*hesitates* I tried to verify that, but I'm getting mixed results... Could you double-check? 💭"
                ]
        elif personality == "professional":
            if verified:
                responses = [f"Correction acknowledged. Updated knowledge base: {correction}"]
            else:
                responses = [f"Verification inconclusive. Please confirm: {correction}"]
        else:
            if verified:
                responses = [f"You're right! I've learned: {correction}"]
            else:
                responses = [f"I couldn't verify that. Are you sure?"]
        
        import random
        return random.choice(responses)
    
    def get_stats(self) -> Dict:
        """Get statistics about corrections"""
        verified_count = sum(1 for c in self.corrections.get("corrections", []) if c.get("verified", False))
        return {
            "total_corrections": len(self.corrections.get("corrections", [])),
            "verified_corrections": verified_count,
            "latest_correction": self.corrections.get("corrections", [])[-1] if self.corrections.get("corrections") else None
        }

if __name__ == "__main__":
    # Test
    cm = CorrectionManager()
    
    print("=== Correction Manager Test ===\n")
    
    # Test detection
    test_inputs = [
        "That's wrong. William I became king in 1815",
        "Actually, the capital is Amsterdam",
        "No, Python was created in 1991",
        "What is the weather today?"  # Not a correction
    ]
    
    for inp in test_inputs:
        is_corr = cm.is_correction(inp)
        print(f"Input: {inp}")
        print(f"Is correction: {is_corr}")
        if is_corr:
            extracted = cm.extract_correction(inp)
            print(f"Extracted: {extracted}")
        print()
