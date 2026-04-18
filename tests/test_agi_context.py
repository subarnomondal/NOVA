import sys
import os
# Add current directory to path
sys.path.append(os.getcwd())

from core.agi_context import agi_context

def test_agi_context():
    print("Testing AGIContext...")
    
    # 1. Test basic storage
    agi_context.set_result({"query": "play music"})
    assert agi_context.shared_query == "play music"
    assert agi_context.chain_data["query"] == "play music"
    print("✅ Basic storage passed")
    
    # 2. Test categorization - Vision
    vision_data = {
        "text": "Hello World",
        "objects": [{"label": "cat", "confidence": 0.9}],
        "metadata": {"timestamp": "2023-10-10"}
    }
    agi_context.set_result(vision_data)
    assert agi_context.visual_data["text"] == "Hello World"
    assert agi_context.get_visual_text() == "Hello World"
    assert agi_context.visual_data["objects"][0]["label"] == "cat"
    print("✅ Vision categorization passed")
    
    # 3. Test categorization - Correction
    correction_data = {
        "correction": "The sky is blue",
        "verified": True,
        "evidence": "Scientific fact"
    }
    agi_context.set_result(correction_data)
    assert agi_context.correction_data["correction"] == "The sky is blue"
    assert agi_context.is_correction_pending() is True
    print("✅ Correction categorization passed")
    
    # 4. Test categorization - NLU
    nlu_data = {
        "intent": "play",
        "entities": {"song": "imagine"},
        "confidence": 0.95
    }
    agi_context.set_result(nlu_data)
    assert agi_context.nlu_metadata["intent"] == "play"
    assert agi_context.get_entities()["song"] == "imagine"
    print("✅ NLU categorization passed")
    
    # 5. Test reset
    agi_context.reset_chain()
    assert agi_context.shared_query is None
    assert agi_context.visual_data == {}
    assert agi_context.correction_data == {}
    assert agi_context.nlu_metadata == {}
    assert agi_context.is_correction_pending() is False
    print("✅ Reset passed")
    
    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    try:
        test_agi_context()
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
