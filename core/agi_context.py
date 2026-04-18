import typing as t

class AGIContext:
    _instance: t.Optional['AGIContext'] = None
    
    last_action_result: t.Any = None
    chain_data: t.Dict[str, t.Any] = {}
    execution_history: t.List[t.Any] = []
    current_mood: str = "neutral"
    shared_query: t.Optional[str] = None
    visual_data: t.Dict[str, t.Any] = {}
    correction_data: t.Dict[str, t.Any] = {}
    nlu_metadata: t.Dict[str, t.Any] = {}
    
    def __new__(cls) -> 'AGIContext':
        if cls._instance is None:
            cls._instance = super(AGIContext, cls).__new__(cls)
            cls._instance._reset()
        return cls._instance
    
    def _reset(self):
        self.last_action_result = None
        self.chain_data = {}
        self.execution_history = []
        self.current_mood = "neutral"
        self.shared_query = None
        
        # New specialized fields
        self.visual_data = {}      # OCR, objects, metadata
        self.correction_data = {}  # User-provided facts
        self.nlu_metadata = {}     # Intents, entities

    def set_result(self, data):
        """Categorize and store result data for the chain."""
        self.last_action_result = data
        if not isinstance(data, dict):
            return

        # 1. Update shared query common fields
        if "query" in data: self.shared_query = data["query"]
        elif "artist" in data: self.shared_query = data["artist"]
        
        # 2. Categorize data into specialized fields
        
        # Vision related
        if any(k in data for k in ["text", "objects", "metadata"]):
            self.visual_data.update({k: data[k] for k in ["text", "objects", "metadata"] if k in data})
            
        # Correction related
        if any(k in data for k in ["correction", "verified", "evidence"]):
            self.correction_data.update({k: data[k] for k in ["correction", "verified", "evidence"] if k in data})
            
        # NLU related
        if any(k in data for k in ["intent", "entities", "confidence"]):
            self.nlu_metadata.update({k: data[k] for k in ["intent", "entities", "confidence"] if k in data})

        # Deep merge into general chain_data
        self.chain_data.update(data)

    def get_query(self, fallback=None):
        return self.shared_query or fallback
        
    def get_visual_text(self):
        """Helper to get OCR text from last vision process."""
        return self.visual_data.get("text")
        
    def get_entities(self):
        """Helper to get extracted entities."""
        return self.nlu_metadata.get("entities", {})
        
    def is_correction_pending(self):
        """Check if last action was a correction."""
        return bool(self.correction_data.get("correction"))

    def reset_chain(self):
        self._reset()

# Singleton Instance
agi_context = AGIContext()
