
import os
import re

class CodebaseReader:
    """
    CodebaseReader
    Provides Nova with the ability to search and read through its own source code 
    to answer architectural questions. (Mini-RAG)
    """
    def __init__(self, root_dir=None):
        self.root_dir = root_dir or os.getcwd()
        self.ignored_dirs = {'.git', '__pycache__', '.venv', 'node_modules', 'screenshots', 'temp'}
        self.supported_exts = {'.py', '.js', '.html', '.css', '.json', '.md', '.txt', '.yaml', '.yml'}

    def list_all_files(self):
        """Returns a tree-like list of files in the project."""
        file_list = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_exts):
                    rel_path = os.path.relpath(os.path.join(root, file), self.root_dir)
                    file_list.append(rel_path)
        return file_list

    def search_codebase(self, query):
        """Search for a keyword in the codebase."""
        matches = []
        file_list = self.list_all_files()
        
        for file in file_list:
            abspath = os.path.join(self.root_dir, file)
            try:
                with open(abspath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if query.lower() in content.lower():
                        matches.append(file)
            except:
                continue
        
        return matches[:20] # Limit to top 20 matches

    def get_file_summary(self, path):
        """Get a summary of a file (size, lines, imports)."""
        abspath = os.path.join(self.root_dir, path)
        if not os.path.exists(abspath):
            return "File not found."
            
        try:
            with open(abspath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                imports = [l.strip() for l in lines if l.startswith(('import ', 'from '))]
                return {
                    "path": path,
                    "size": os.path.getsize(abspath),
                    "lines": len(lines),
                    "imports": imports[:10] # Top 10 imports
                }
        except:
            return "Error reading file info."

    def handle_reader(self, args):
        """Dispatcher for codebase reader commands."""
        args_lower = args.lower()
        if "list files" in args_lower:
            files = self.list_all_files()
            return "📁 **Codebase Files:**\n" + "\n".join(files[:30]) + (f"\n... and {len(files)-30} more" if len(files) > 30 else "")
        elif "search" in args_lower:
            query = args.replace("reader search", "").replace("search", "").strip()
            matches = self.search_codebase(query)
            if matches:
                return f"🔍 **Found '{query}' in:**\n" + "\n".join(matches)
            return f"❌ No matches found for '{query}'."
        return "Reader available: 'list files', 'search [query]'."

def register(dispatcher):
    reader = CodebaseReader()
    dispatcher.register("reader", reader.handle_reader)
    dispatcher.register("search code", reader.handle_reader)
    dispatcher.register("list project files", reader.handle_reader)
