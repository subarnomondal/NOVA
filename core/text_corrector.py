"""
Text Corrector Module for NOVA
Provides high-quality text corrections (spelling, grammar, and style) using the LLM.
"""

import threading
from typing import Dict, Any, Optional

class TextCorrector:
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        import os
        self.dictionary_file = os.path.join("userdata", "user_dictionary.json")
        self.custom_words = self._load_dictionary()

    def _load_dictionary(self):
        try:
            import json, os
            if os.path.exists(self.dictionary_file):
                with open(self.dictionary_file, 'r') as f:
                    return json.load(f)
            return []
        except:
            return []

    def add_word(self, word):
        if word.lower() not in [w.lower() for w in self.custom_words]:
            self.custom_words.append(word)
            self._save_dictionary()
            return True
        return False

    def _save_dictionary(self):
        import json
        with open(self.dictionary_file, 'w') as f:
            json.dump(self.custom_words, f)

    def correct(self, text: str, mode: str = "balanced") -> Dict[str, Any]:
        """
        Correct common spelling, grammar, and style errors.
        Modes: 'spelling', 'grammar', 'balanced', 'professional'.
        """
        if not text:
            return {"original": "", "corrected": "", "changes": []}
            
        system_prompt = self._get_system_prompt(mode)
        prompt = f"Please correct the following text: \"{text}\""
        
        try:
            # Generate the correction from LLM
            corrected_text = self.llm_manager.generate(
                user_input=prompt,
                system_prompt=system_prompt,
                max_tokens=256,
                temperature=0.3 # Low temperature for accurate corrections
            )
            
            # Clean up potential LLM additions (like "Here is the corrected text:")
            corrected_text = self._clean_llm_response(corrected_text)
            
            return {
                "original": text,
                "corrected": corrected_text,
                "mode": mode,
                "is_changed": text.strip() != corrected_text.strip()
            }
            
        except Exception as e:
            print(f"⚠️ Text correction error: {e}")
            return {"original": text, "corrected": text, "error": str(e), "is_changed": False}

    def _get_system_prompt(self, mode: str) -> str:
        """Get the system prompt based on the correction mode."""
        base_instructions = (
            "You are a professional editor. Your goal is to correct the user's text. "
            "Respond ONLY with the corrected text. Do not add any preamble, explanations, "
            "or quotes around the output unless they were in the original text."
        )
        
        if self.custom_words:
            word_list = ", ".join(self.custom_words)
            base_instructions += f"\nIMPORTANT: Treat the following words as correctly spelled: {word_list}."
        
        mode_prompts = {
            "spelling": "Focus exclusively on fixing spelling errors and typos. Keep the original grammar and style intact.",
            "grammar": "Focus on fixing grammar, punctuation, and syntax errors. Improve clarity but maintain the original tone.",
            "balanced": "Correct spelling, grammar, and improve the general flow and naturalness of the text.",
            "professional": "Transform the text into professional, formal business writing. Optimize for clarity, conciseness, and tone."
        }
        
        specific_instruction = mode_prompts.get(mode, mode_prompts["balanced"])
        return f"{base_instructions} {specific_instruction}"

    def _clean_llm_response(self, text: str) -> str:
        """Cleanup common LLM-isms and extract just the corrected text."""
        if not text:
            return ""
            
        # 1. Remove common introductory phrases (case insensitive)
        intro_phrases = [
            "the corrected text is:", "here is the corrected text:", 
            "sure, here's the correction:", "the corrected version is:",
            "revised text:", "edited version:", "corrected text:",
            "the improved text is:", "here's the fixed version:"
        ]
        
        cleaned = text.strip()
        
        # Split by lines and check the first few
        lines = cleaned.split('\n')
        for phrase in intro_phrases:
            if lines[0].lower().strip().startswith(phrase):
                # If the first line is just the intro, remove it
                if len(lines[0].strip()) <= len(phrase) + 2:
                    cleaned = '\n'.join(lines[1:]).strip()
                else:
                    # Remove from the line itself
                    cleaned = lines[0][len(phrase):].strip() + '\n' + '\n'.join(lines[1:])
                    cleaned = cleaned.strip()
                break
        
        # 2. Extract text inside quotes if the whole response is quoted
        import re
        quote_match = re.search(r'^["\'](.*?)["\']$', cleaned, re.DOTALL)
        if quote_match:
            cleaned = quote_match.group(1).strip()
            
        # 3. Stop at explanations (common patterns in small models)
        explanation_markers = [
            "\n\nExplanation:", "\n\nChanges made:", "\n\nI have corrected",
            "\n\nThe spelling", "\n\nNote:", "\n\nHere are", "\n\nCorrection details:",
            "Here is the corrected text:", "Nova:", "User:"
        ]
        
        for marker in explanation_markers:
            if marker in cleaned:
                cleaned = cleaned.split(marker)[0].strip()
                
        # 4. If the text contains <|endoftext|>, stop there
        if "<|endoftext|>" in cleaned:
            cleaned = cleaned.split("<|endoftext|>")[0].strip()

        # 5. Final check: if it starts with a quote but doesn't end with one, 
        # it might be the start of the correction.
        if cleaned.startswith('"') and not cleaned.endswith('"'):
            # Try to find the closing quote before an explanation
            close_quote = cleaned.find('"', 1)
            if close_quote != -1:
                cleaned = cleaned[1:close_quote].strip()
            else:
                cleaned = cleaned[1:].strip()
        
        # 6. If it's a single sentence, stop at the first double newline
        if "\n\n" in cleaned:
            cleaned = cleaned.split("\n\n")[0].strip()
                
        return cleaned

# Singleton instance will be created in desktop.py
