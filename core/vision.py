"""
Vision Module for NOVA
Uses Torchvision (MobileNetV3) to classify images and return object labels.
Serves as the "Eye" for the Multimodal system.
"""

import threading
import os
import json
import urllib.request

class ImageAnalyzer:
    def __init__(self):
        self.model = None
        self.weights = None
        self.preprocess = None
        self.device = "cpu"
        self.is_ready = False
        
        # Lazy loading initiated by first call
        self._load_lock = threading.Lock()
    
    def _load_model(self):
        # Local Vision models are removed for performance.
        # Vision requests are now handled by Gemini or skipped if unneeded.
        self.is_ready = True
        print("✅ Vision System: Ready (API-Only Mode)")

    def analyze(self, image_path, top_k=3):
        """Vision analysis is deferred to Gemini/LLM API."""
        try:
            from core.llm_manager import llm_manager
            
            prompt = "Analyze this image and return a list of the 5 most important objects or activities you see. Format as a simple comma-separated list. No preamble."
            
            # Use raw_gen=True to get clean output
            result = llm_manager.generate(
                prompt,
                max_tokens=50,
                temperature=0.2,
                image_path=image_path,
                raw_gen=True
            )
            
            if result:
                # Clean and split
                labels = [label.strip().replace(".", "") for label in result.split(",")]
                return labels[:top_k]
            
            return ["Vision Analysis Failed"]
        except Exception as e:
            print(f"❌ API Vision Error: {e}")
            return ["API Error"]

