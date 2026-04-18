
import os
import shutil
from skills.document_analysis import document_analyzer
from core.llm_manager import llm_manager

class CARWorkflow:
    """
    CAR (Copy-Analyze-Rebuild) Workflow Skill
    A unified feature for processing files and updating the system brain.
    """
    def __init__(self, dispatcher=None):
        self.dispatcher = dispatcher

    def execute_car(self, args):
        """
        Main CAR entry point.
        Usage: car "source_path" [dest_path]
        """
        # 1. Parse Args
        import re
        path_match = re.search(r'car\s+["\'](.+?)["\']', args, re.IGNORECASE)
        if not path_match:
            # Try simple split
            parts = args.replace("car", "").strip().split()
            if not parts:
                return "Please provide a file to process! Usage: car \"path/to/file\""
            src = parts[0]
        else:
            src = path_match.group(1)

        if not os.path.exists(src):
            return f"❌ Source file not found: {src}"

        # 2. STEP: COPY
        # For CAR, we ensure the file is in a 'processed' or 'training' directory
        # Or just acknowledge its presence. 
        # For now, let's copy to a temporary training buffer if it's a JSONL/CSV
        dest_dir = os.path.join("userdata", "datasets", "car_buffer")
        if not os.path.exists(dest_dir): os.makedirs(dest_dir)
        
        filename = os.path.basename(src)
        target_path = os.path.join(dest_dir, filename)
        shutil.copy2(src, target_path)
        copy_status = f"✅ Step 1: Copied to {target_path}"

        # 3. STEP: ANALYZE
        # We use the document_analyzer to get the gist
        print(f"🧠 Step 2: Analyzing {filename}...")
        analysis = document_analyzer.analyze_file(target_path, mode="analyze")
        
        # 4. STEP: REBUILD
        # This depends on file type. If it's training data, we might trigger a training or reload.
        # For now, we'll reload the LLM stats and check for new adapters/models.
        print(f"🔄 Step 3: Rebuilding system context...")
        llm_manager.load_model() # Reload/Verify main model
        if hasattr(llm_manager, 'load_scratch_model'):
            llm_manager.load_scratch_model() # Reload scratch model if it exists
        
        rebuild_status = "✅ Step 3: System context rebuilt and LLM reloaded."

        return f"""🚀 **CAR Workflow Complete!**
        
{copy_status}
📊 **Analysis Result:**
{analysis}
{rebuild_status}
"""

def register(dispatcher):
    car = CARWorkflow(dispatcher)
    dispatcher.register("car", car.execute_car)
    dispatcher.register("copy analyze rebuild", car.execute_car)
    dispatcher.register("process file", car.execute_car)
