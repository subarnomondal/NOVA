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
        """Vision analysis is deferred to Gemini."""
        return ["API-Only Vision Enabled"]
