import os
import sys

# Ensure project root is in sys.path for local module resolution
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
import warnings
import logging
import io

# Force UTF-8 for Windows console/piping
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Silence Hugging Face Hub noise (Symlinks, Telemetry, Offline mode)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# Silence Transformers logging
try:
    from transformers import logging as transformers_logging
    transformers_logging.set_verbosity_error()
except ImportError:
    pass

# Silence general Hub logging
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

# Silence specific library warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*renamed to ddgs.*")
