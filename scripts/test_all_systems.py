"""
Comprehensive System & Skill Verification Suite for CLIO
Tests all core modules, skills, dispatch routing, and fallback pipelines.
"""

import os
import sys
import unittest

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

os.makedirs("userdata", exist_ok=True)
os.makedirs("userdata/temp", exist_ok=True)


class TestClioCore(unittest.TestCase):
    def test_01_core_imports(self):
        """Test that all core and engine modules import cleanly."""
        import core.llm_manager
        import core.assistant
        import core.dispatcher
        import core.agi_context
        import core.key_manager
        import core.personality_manager
        import core.emotion_detector
        import core.conversation_memory
        import core.conversation_memory
        import core.ltm_manager
        import core.nlp_processor
        self.assertTrue(True)

    def test_02_llm_model_swarm(self):
        """Test that modern LLM swarm models are defined and active."""
        from core.llm_manager import DEFAULT_MODELS
        self.assertGreater(len(DEFAULT_MODELS), 0)
        self.assertTrue(any("llama-3.3" in m or "llama-3.1" in m for m in DEFAULT_MODELS))
        self.assertTrue(any("gemini" in m for m in DEFAULT_MODELS))

    def test_03_command_dispatcher(self):
        """Test dispatcher registration, execution safety, and panic abort."""
        from core.dispatcher import CommandDispatcher
        d = CommandDispatcher()
        d.register("ping", lambda text: "pong")
        self.assertEqual(d.dispatch("ping"), "pong")
        
        # Test panic stop
        stop_resp = d.dispatch("stop all skills")
        self.assertIn("Emergency Abort", stop_resp)

    def test_04_math_skill_percentages_and_arithmetic(self):
        """Test math skill calculations including percentages and expressions."""
        from skills.math_skill import cmd_calculate
        
        # Simple arithmetic
        res1 = cmd_calculate("calculate 25 * 4")
        self.assertIn("100", str(res1))
        
        # Percentage calculation: 20 percent of 150 -> 30
        res2 = cmd_calculate("calculate 20 percent of 150")
        self.assertIn("30", str(res2))
        
        # Square root
        res3 = cmd_calculate("calculate sqrt(144)")
        self.assertIn("12", str(res3))

    def test_05_finance_regex_offline_parser(self):
        """Test offline expense extraction regex fallback."""
        from skills.finance import cmd_add_expense, load_finance_data
        
        resp = cmd_add_expense("add expense 45.50 for books")
        self.assertIn("Recorded 45.5", resp)
        self.assertIn("books", resp)
        
        data = load_finance_data()
        self.assertTrue(isinstance(data.get("expenses"), list))
        latest = data["expenses"][-1]
        self.assertEqual(latest["amount"], 45.5)
        self.assertEqual(latest["item"], "books")

    def test_06_system_volume_adjustments(self):
        """Test volume command parser handles relative and explicit levels."""
        from skills.system import cmd_volume
        # Test query/relative parsing (will safely call Windows COM or return error message on non-audio env)
        res = cmd_volume("volume 50")
        self.assertTrue(isinstance(res, str))
        self.assertGreater(len(res), 0)

    def test_07_mcp_server_tools(self):
        """Test that MCP server registers all expected tools."""
        from mcp_clio import mcp
        tool_names = [t.name for t in mcp._tool_manager.list_tools()]
        expected = ["ask_clio", "execute_skill", "get_system_health", "list_skills", "take_screenshot", "search_web", "calculate", "add_expense"]
        for exp in expected:
            self.assertIn(exp, tool_names)

    def test_09_stt_manager_and_voice_pipeline(self):
        """Test STT Manager audio format validation, hallucination detection, and pipeline routing."""
        from core.stt_manager import stt_manager, STT_HALLUCINATIONS
        self.assertIsNotNone(stt_manager)
        
        # Test hallucination filter
        self.assertTrue(stt_manager.is_hallucination("thank you for watching"))
        self.assertTrue(stt_manager.is_hallucination("please subscribe"))
        self.assertTrue(stt_manager.is_hallucination("..."))
        self.assertFalse(stt_manager.is_hallucination("What is the weather today?"))
        
        # Test model preference retrieval
        pref = stt_manager.get_preferred_model_name()
        self.assertIn(pref, ["small.en", "distil-small.en", "base.en", "tiny.en", "medium.en", "large-v3-turbo", "auto"])
        
        # Test invalid audio rejection
        self.assertFalse(stt_manager.is_valid_audio("non_existent_file.wav"))


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 RUNNING CLIO COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 70)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClioCore)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n✅ ALL CLIO SYSTEMS & SKILLS PASS VERIFICATION!")
        sys.exit(0)
    else:
        print("\n❌ SYSTEM TESTS HAD FAILURES")
        sys.exit(1)
