
import os
import mimetypes

class DocumentReader:
    def __init__(self):
        self.supported_extensions = {
            '.txt', '.md', '.py', '.js', '.json', '.html', '.css', 
            '.csv', '.log', '.bat', '.ps1', '.yaml', '.yml', '.xml',
            '.c', '.cpp', '.h', '.java', '.cs', '.php', '.rb', '.go', '.rs'
        }

    def read_file(self, file_path):
        """
        Reads the content of a file if it's a supported text/code format.
        Returns a dict with 'content' and 'type' or 'error'.
        """
        if not os.path.exists(file_path):
            return {"error": "File not found."}

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    
                    if not text.strip():
                        return {"content": "PDF seems to be empty or contains only images (OCR required).", "type": "pdf"}
                        
                    return {"content": text, "type": "pdf"}
            except ImportError:
                 return {"error": "PyPDF2 not installed. Please run: pip install PyPDF2"}
            except Exception as e:
                return {"error": f"Failed to read PDF: {str(e)}"}
            
        if ext == '.docx':
            try:
                import docx
                doc = docx.Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                if not text.strip():
                    return {"content": "Document seems empty.", "type": "docx"}
                return {"content": text, "type": "docx"}
            except ImportError:
                 return {"error": "python-docx not installed. Please run: pip install python-docx"}
            except Exception as e:
                return {"error": f"Failed to read DOCX: {str(e)}"}

        # Basic text/code reading
        if ext in self.supported_extensions or self._is_text_file(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Truncate if too huge to prevent context overflow (limit to ~10k chars for now)
                    if len(content) > 15000:
                        content = content[:15000] + "\n...[Content Truncated]..."
                    return {"content": content, "type": "text"}
            except Exception as e:
                return {"error": f"Failed to read file: {str(e)}"}
        
        # Generic Fallback for Binary Files (Zip, Exe, etc.)
        # Instead of erroring, return metadata so Nova can acknowledge receipt.
        file_size = os.path.getsize(file_path)
        size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
        
        return {
            "content": f"[Binary File Received]\nName: {os.path.basename(file_path)}\nSize: {size_str}\nType: {ext}\n\nI can't read the internal contents of this file type yet, but I have received it safely.", 
            "type": "binary"
        }

    def _is_text_file(self, file_path):
        """
        Heuristic to check if a file is text based on mime type or content.
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('text/'):
            return True
        return False

# Global instance
document_reader = DocumentReader()
