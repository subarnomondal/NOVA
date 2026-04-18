
import sys
import os

def debug_import(module_name, from_module=None, import_name=None):
    print(f"DEBUG: Importing {module_name}...")
    try:
        if from_module:
            exec(f"from {from_module} import {import_name}")
        else:
            exec(f"import {module_name}")
        print(f"DEBUG: {module_name} OK.")
    except Exception as e:
        print(f"DEBUG: {module_name} FAILED: {e}")

debug_import("core.assistant", "core.assistant", "Nova")
debug_import("core.conversation_memory", "core.conversation_memory", "ConversationMemory")
debug_import("core.nlp_processor", "core.nlp_processor", "NLUProcessor")
debug_import("core.hitl_system", "core.hitl_system", "HITLSystem")
debug_import("core.domain_knowledge", "core.domain_knowledge", "DomainKnowledge")
debug_import("core.user_profile", "core.user_profile", "UserProfile")
debug_import("core.drl_system", "core.drl_system", "DRLSystem")
debug_import("core.response_optimizer", "core.response_optimizer", "ResponseOptimizer")
debug_import("core.personality_manager", "core.personality_manager", "PersonalityManager")
debug_import("core.analytics", "core.analytics", "AnalyticsEngine")
debug_import("core.vision", "core.vision", "ImageAnalyzer")
debug_import("core.emotion_detector", "core.emotion_detector", "emotion_detector")
debug_import("core.ml_predictor", "core.ml_predictor", "MLPredictor")
