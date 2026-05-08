
import os
from core.document_reader import document_reader
from core.llm_manager import llm_manager

class DocumentAnalysis:
    def __init__(self):
        self.last_uploaded_file = None
        self.last_analysis = None

    def set_current_file(self, file_path):
        """Sets the context for the current file to be analyzed."""
        self.last_uploaded_file = file_path
        self.last_analysis = None # Reset cache

    def analyze_file(self, file_path=None, mode="summary"):
        """
        Analyzes a file using the LLM. 
        Modes: 'summary', 'analyze', 'gist'
        """
        target_file = file_path or self.last_uploaded_file
        
        if not target_file or not os.path.exists(target_file):
            return "No file has been uploaded yet to analyze! Please upload one first. 📂"

        # 1. Read Content
        doc_result = document_reader.read_file(target_file)
        
        if "error" in doc_result:
             return f"I couldn't read the file. {doc_result['error']}"
        
        content = doc_result.get("content", "")
        file_type = doc_result.get("type", "unknown")
        filename = os.path.basename(target_file)

        if not content.strip():
            return "The file appears to be empty."
            
        # 2. Construct Prompt based on Mode
        if mode == "analyze":
            task_prompt = "Provide a detailed analysis of this file. Explain its purpose, key structures, and important details."
        elif mode == "gist":
            task_prompt = "Give me the gist of this file in 3-4 bullet points. Keep it brief."
        else: # summary
            task_prompt = "Summarize this file in a concise paragraph."

        # Truncate content to fit context window (approx 2000 chars for efficiency)
        # For larger files, we might need a sliding window approach, but this is a V1 implementation.
        preview_content = content[:2500]
        truncation_note = "...(content truncated)..." if len(content) > 2500 else ""
        
        system_prompt = f"""
        CONTEXT: User uploaded a {file_type} file named '{filename}'.
        FILE CONTENT:
        {preview_content}
        {truncation_note}

        TASK: {task_prompt}
        STYLE: Professional and insightful. Point out non-obvious details and maintain a helpful, sharp character.
        RESPONSE FORMAT: Markdown.
        Nova:"""

        # 3. Generate Response
        # FORCE LOCAL LLM for Document Analysis (Privacy/Cost/Offline)
        # We prefer 'custom' (Native GPT4All) if available, or 'local_api' if that's the active one.
        
        target_provider = None # Use system default
        
        # If a specific provider is requested via settings, we could use it here
        # For now, we allow llm_manager to decide based on its swarm logic.

            
        try:
            # We try to force the local provider. 
            # Note: valid providers in LLMManager are "custom", "local_api", "gemini", "openai"
            response = llm_manager.generate(
                system_prompt, 
                max_tokens=400, 
                temperature=0.3, 
                provider=target_provider
            )

            
            if response:
                self.last_analysis = response
                return response
            else:
                return "I tried to analyze this locally, but my local LLM brain isn't responding. Make sure you have a model downloaded."
                
        except Exception as e:
            return f"I had trouble analyzing that file locally. Error: {str(e)}"

    def handle_intent(self, user_input):
        user_input = user_input.lower()
        
        # Check if it's a specific question about the file
        question_keywords = ["what", "how", "why", "when", "where", "find", "is there"]
        is_question = any(q in user_input for q in question_keywords) and len(user_input.split()) > 3
        
        if is_question:
            # Q&A Mode
            return self.analyze_file(mode=f"Answer the following question about the file: {user_input}")
            
        mode = "summary"
        if "gist" in user_input:
            mode = "gist"
        elif "analyze" in user_input or "detail" in user_input:
            mode = "analyze"
            
        return self.analyze_file(mode=mode)

# Singleton Instance
document_analyzer = DocumentAnalysis()

def get_analysis_response(input_text):
    return document_analyzer.handle_intent(input_text)

def register(dispatcher):
    dispatcher.register("analyze this", get_analysis_response)
    dispatcher.register("summarize", get_analysis_response)
    dispatcher.register("give me the gist", get_analysis_response)
    dispatcher.register("what is this file", get_analysis_response)
    dispatcher.register("explain this file", get_analysis_response)
