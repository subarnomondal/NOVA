
import os
import re
import ast
import traceback

class CodeArchitect:
    """
    CodeArchitect Skill
    Enables Nova to read, edit, and verify its own source code autonomously.
    """
    def __init__(self, workspace_root=None):
        self.workspace_root = workspace_root or os.getcwd()

    def _resolve_path(self, path):
        if os.path.isabs(path):
            return path
        return os.path.join(self.workspace_root, path)

    def read_file(self, path):
        """Read a file's content for analysis."""
        abspath = self._resolve_path(path)
        if not os.path.exists(abspath):
            return f"Error: File {path} not found."
        try:
            with open(abspath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {path}: {e}"

    def write_file(self, path, content):
        """Overwrite or create a file."""
        abspath = self._resolve_path(path)
        try:
            # Basic safety: Backup before overwrite
            if os.path.exists(abspath):
                with open(abspath + '.bak', 'w', encoding='utf-8') as b:
                    with open(abspath, 'r', encoding='utf-8') as f:
                        b.write(f.read())
            
            os.makedirs(os.path.dirname(abspath), exist_ok=True)
            with open(abspath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}. Backup created at {path}.bak"
        except Exception as e:
            return f"Error writing to {path}: {e}"

    def edit_file(self, path, find_text, replace_text):
        """Replace a target string in a file."""
        abspath = self._resolve_path(path)
        content = self.read_file(abspath)
        if content.startswith("Error:"): return content
        
        if find_text not in content:
            return f"Error: Could not find exact text match in {path} to replace."
        
        new_content = content.replace(find_text, replace_text)
        return self.write_file(path, new_content)

    def verify_syntax(self, path):
        """Verify Python syntax using the ast module."""
        abspath = self._resolve_path(path)
        if not path.endswith('.py'):
            return "Syntax verification skipped (not a Python file)."
        
        content = self.read_file(abspath)
        try:
            ast.parse(content)
            return "Syntax check passed! ✅"
        except SyntaxError as e:
            return f"Syntax Error in {path}: {e}"

    def handle_architect(self, args):
        """
        Main entry point for instructions.
        Usage: architect [action] [path] [params...]
        Example: architect read desktop.py
        Example: architect edit core/llm_manager.py "old_code" "new_code"
        """
        try:
            parts = re.findall(r'\"(.+?)\"|(\S+)', args)
            parts = [p[0] if p[0] else p[1] for p in parts]
            
            if len(parts) < 3:
                return "Usage: architect [read|write|edit|verify] [path] [args...]"

            action = parts[1].lower()
            path = parts[2]

            if action == 'read':
                return self.read_file(path)
            elif action == 'write' and len(parts) > 3:
                return self.write_file(path, parts[3])
            elif action == 'edit' and len(parts) > 4:
                return self.edit_file(path, parts[3], parts[4])
            elif action == 'verify':
                return self.verify_syntax(path)
            else:
                return f"Unknown architect action: {action}"
        except Exception as e:
            return f"Architect encountered an error: {e}"

def register(dispatcher):
    arch = CodeArchitect()
    dispatcher.register("architect", arch.handle_architect)
    dispatcher.register("modify file", arch.handle_architect)
    dispatcher.register("read code", arch.handle_architect)
    dispatcher.register("check syntax", arch.handle_architect)
