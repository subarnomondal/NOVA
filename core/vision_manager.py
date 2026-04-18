
import os
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import shutil
import time
import pyautogui
from datetime import datetime

class VisionManager:
    def __init__(self):
        # Tesseract default path on Windows
        self.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if HAS_TESSERACT:
            if os.path.exists(self.tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            else:
                print("⚠️ Tesseract executable not found at default location.")
                # We don't disable HAS_TESSERACT here because it might be in PATH, 
                # but it's good to warn.
        else:
            print("⚠️ Pytesseract module not found. OCR will be disabled.")
            
        self.temp_dir = os.path.join("userdata", "temp", "vision")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        # Local vision models are removed. We depend on Gemini API.
        print(f"✅ Vision System Initialization Complete (API-Only Mode)")
            
    def _clean_text(self, text):
        return " ".join(text.split()).strip()

    def capture_screen(self):
        """Captures the primary screen and returns the file path."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.temp_dir, filename)
            
            # Ensure temp dir exists
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir)
                
            pyautogui.screenshot(filepath)
            print(f"📸 Screen captured: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Screen capture failed: {e}")
            return None

    def encode_image_base64(self, image_path):
        """Convert image to base64 string for API transmission."""
        try:
            import base64
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ Base64 encoding failed: {e}")
            return None

    def extract_metadata(self, image_path):
        """Extract EXIF metadata from image."""
        try:
            img = Image.open(image_path)
            # Fix: Use getexif() instead of _getexif() for modern PIL or check both
            exif_data = img.getexif() if hasattr(img, 'getexif') else img._getexif() # type: ignore
            
            if not exif_data:
                return {}
            
            metadata = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                
                # Extract key metadata
                if tag == "DateTime":
                    metadata["timestamp"] = str(value)
                elif tag == "Make":
                    metadata["camera_make"] = str(value)
                elif tag == "Model":
                    metadata["camera_model"] = str(value)
                elif tag == "GPSInfo":
                    gps_data = {}
                    for gps_tag_id in value:
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = value[gps_tag_id]
                    # Fix: Ensure metadata value is string or serializable
                    metadata["gps"] = str(gps_data)
                    
            return metadata
        except:
            return {}

    def classify_image(self, image_path, top_k=5):
        """Image classification deferred to Gemini API."""
        return []

    def process_image(self, image_path, cleanup=True):
        """
        Comprehensive image analysis: OCR + Classification + Metadata
        """
        if not os.path.exists(image_path):
            return "❌ Error: Image file not found."
            
        try:
            print(f"👁️ Analyzing image: {image_path}")
            
            # 1. Extract Metadata
            metadata = self.extract_metadata(image_path)
            
            # 2. Classify Visual Content
            predictions = self.classify_image(image_path, top_k=3)
            
            # 3. OCR Text Extraction
            text = ""
            img = None
            if HAS_TESSERACT:
                try:
                    img = Image.open(image_path)
                    text = pytesseract.image_to_string(img)
                except Exception as e:
                    print(f"⚠️ OCR Failed: {e}")
            
            clean_text = self._clean_text(text)
            if 'img' in locals() and hasattr(img, 'close'): 
                img.close()
            
            # Build comprehensive analysis
            analysis = {
                "text": clean_text if clean_text else None,
                "objects": predictions,
                "metadata": metadata
            }
            
            if cleanup:
                self.cleanup_file(image_path)
                
            return analysis
            
        except Exception as e:
            return {"error": f"Vision Error: {str(e)}"}

    def format_analysis(self, analysis):
        """Format analysis dict into human-readable text."""
        if isinstance(analysis, str):
            return analysis
            
        if "error" in analysis:
            return analysis["error"]
            
        result = []
        
        # Visual Content
        if analysis.get("objects"):
            top_obj = analysis["objects"][0]
            result.append(f"🖼️ I see: {top_obj['label']} ({top_obj['confidence']*100:.1f}% confident)")
            
            # Detect categories
            all_labels = [obj['label'].lower() for obj in analysis["objects"]]
            
            # Animals
            animal_keywords = ['dog', 'cat', 'bird', 'horse', 'elephant', 'tiger', 'lion', 'bear', 'fish', 'snake']
            animals = [l for l in all_labels if any(a in l for a in animal_keywords)]
            if animals:
                result.append(f"🐾 Animals detected: {', '.join(animals[:2])}")
            
            # Places/Scenes
            place_keywords = ['beach', 'mountain', 'forest', 'city', 'building', 'street', 'park', 'lake', 'ocean']
            places = [l for l in all_labels if any(p in l for p in place_keywords)]
            if places:
                result.append(f"📍 Scene: {', '.join(places[:2])}")
        
        # Text Content
        if analysis.get("text"):
            result.append(f"📝 Text found: {analysis['text'][:100]}...")
        
        # Metadata
        meta = analysis.get("metadata", {})
        if meta.get("timestamp"):
            result.append(f"📅 Taken: {meta['timestamp']}")
        if meta.get("camera_model"):
            result.append(f"📷 Camera: {meta['camera_model']}")
        if meta.get("gps"):
            result.append(f"🌍 Location data available")
            
        return "\n".join(result) if result else "I analyzed the image but couldn't extract much information."

    def cleanup_file(self, file_path):
        """
        Securely deletes the temp file.
        """
        try:
            # Wait a bit to ensure handle is released
            time.sleep(0.5) 
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Cleaned up temp image: {file_path}")
        except Exception as e:
            print(f"⚠️ Failed to delete {file_path}: {e}")

    def manage_temp_storage(self):
        """
        Auto-cleans the entire temp folder on startup.
        """
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)
            print("🧹 Vision temp storage cleared.")

# Global singleton
vision_manager = VisionManager()

if __name__ == "__main__":
    # Test
    print("Vision Manager Initialized.")
