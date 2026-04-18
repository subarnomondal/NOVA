
import os
import re
from core.vision_manager import VisionManager
from core.llm_manager import llm_manager

class VisionSkill:
    def __init__(self):
        self.vision = VisionManager()

    def _is_question(self, text):
        # Heuristic: looks for '?' or option markers like 'A)', '1.' or keywords
        markers = ['?', 'A)', 'B)', 'C)', 'D)', '1.', '2.', 'a.', 'b.', 'c.', 'd.']
        keywords = ['question', 'solve', 'answer', 'calculate', 'what is', 'find the']
        
        count = sum(1 for m in markers if m in text)
        keyword_match = any(k in text.lower() for k in keywords)
        
        return count >= 1 or '?' in text or keyword_match

    def solve_mcq(self, text):
        prompt = f"""
        You are Nova, an intelligent and highly capable digital companion.
        You are looking at a question extracted from an image.
        
        Your Goal: Solve it correctly, but respond in a natural, helpful way. 
        - Don't just list steps 1, 2, 3.
        - Act like you're teaching a student or helping a friend.
        - Context: You are smart, professional, and deeply caring.
        - If it's a simple math problem, solve it quickly.
        - If it's complex, explain it clearly without sounding robotic.
        
        QUESTION CONTEXT:
        {text}
        
        YOUR RESPONSE (In character):
        """
        
        print("🧠 Nova Brain: Analyzing MCQ...")
        try:
            response = llm_manager.generate(
                prompt, 
                max_tokens=200,
                temperature=0.7,
                system_prompt="You are a helpful tutor solving questions from images."
            )
            if response:
                return response.get('text', response) if isinstance(response, dict) else response
            else:
                return " (I see the text, but I can't solve it because my LLM brain isn't responding.)"
        except Exception as e:
            print(f"❌ MCQ solving error: {e}")
            return " (I see the text, but I can't solve it because my LLM brain isn't loaded.)"

    def handle_vision(self, input_text):
        # Improved regex to capture Windows paths, including potential spaces and varying drive letters
        path_pattern = r'([a-zA-Z]:\\[\w\s\-\.\(\)\\]+\.(?:png|jpg|jpeg|bmp|tiff))'
        match = re.search(path_pattern, input_text, re.IGNORECASE)
        
        if match:
            path = match.group(0).strip().replace('"', '').replace("'", "")
            
            # Get comprehensive analysis
            analysis = self.vision.process_image(path)
            
            # If error
            if isinstance(analysis, str) or "error" in analysis:
                return str(analysis)
            
            # Format the visual analysis
            formatted = self.vision.format_analysis(analysis)
            
            # Check if there's text that looks like a question
            raw_text = analysis.get("text", "")
            if raw_text and self._is_question(raw_text):
                print("🧠 Detecting question... Engaging Reasoning Core.")
                answer = self.solve_mcq(raw_text)
                formatted += f"\n\n🧠 **Nova Analysis**:\n{answer}"
            else:
                # If no question, use LLM to comment on visual content
                if analysis.get("objects"):
                    top_objects = [obj['label'] for obj in analysis['objects'][:3]]
                    context = f"Visual: {', '.join(top_objects)}"
                    if analysis.get("metadata", {}).get("timestamp"):
                        context += f" | Taken: {analysis['metadata']['timestamp']}"
                    
                    prompt = f"""You are Nova. The user showed you an image.
                    
VISUAL CONTENT: {context}

Respond briefly (1-2 sentences) in character. Be observant and helpful.
Nova:"""
                    
                    try:
                        comment = llm_manager.generate(
                            prompt, 
                            max_tokens=80,
                            temperature=0.8
                        )
                        if comment:
                            comment_text = comment.get('text', comment) if isinstance(comment, dict) else comment
                            formatted += f"\n\n💭 {comment_text.strip()}"
                    except Exception as e:
                        print(f"Vision commentary error: {e}")
            
            return formatted
        else:
            return "I need an image file path to read! Please drag and drop an image or paste the path."

def get_vision_response(input_text):
    skill = VisionSkill()
    return skill.handle_vision(input_text)

def register(dispatcher):
    """Register triggers for vision skill"""
    dispatcher.register("vision", get_vision_response)
    dispatcher.register("analyze image", get_vision_response)
    dispatcher.register("read text from image", get_vision_response)
    dispatcher.register("solve mcq", get_vision_response)
