"""
Training Skill for NOVA
Commands to teach Nova new conversational patterns and responses
"""

import re
from core.conversation_trainer import ConversationTrainer

# Initialize trainer
trainer = ConversationTrainer()

def cmd_teach_response(args):
    """
    Teach Nova a new response
    Usage: teach "trigger" to say "response" [with mood "mood"] [in category "category"]
    Example: teach "hello" to say "hi" with mood "happy"
    """
    try:
        # Base pattern for trigger and response
        base_pattern = r'teach\s+["\'](.+?)["\']\s+to\s+say\s+["\'](.+?)["\']'
        match = re.search(base_pattern, args, re.IGNORECASE)
        
        trigger = None
        response = None
        mood = "neutral"
        category = "general"
        
        if match:
            trigger = match.group(1).strip()
            response = match.group(2).strip()
            
            # Look for optional mood
            mood_match = re.search(r'with\s+mood\s+["\'](.+?)["\']', args, re.IGNORECASE)
            if mood_match:
                mood = mood_match.group(1).strip()
                
            # Look for optional category
            cat_match = re.search(r'in\s+category\s+["\'](.+?)["\']', args, re.IGNORECASE)
            if cat_match:
                category = cat_match.group(1).strip()
                
        else:
            # Try alternative format: teach trigger = response
            pattern2 = r'teach\s+(.+?)\s*=\s*(.+)'
            match = re.search(pattern2, args, re.IGNORECASE)
            if match:
                trigger = match.group(1).strip()
                response = match.group(2).strip()

        if trigger and response:
            trainer.teach_response(trigger, response, category=category, mood=mood)
            
            msg = f"Got it! *takes notes* ✍️ I've learned that when you say '{trigger}', I should respond with '{response}'."
            if mood != "neutral":
                msg += f" (Mood: {mood})"
            if category != "general":
                msg += f" [Category: {category}]"
            
            return msg + " Try it out!"
        else:
            return """I'd love to learn! Here's how to teach me with more parameters:
            
 Format: teach "trigger" to say "response" [with mood "mood"] [in category "category"]

Example: teach "good morning" to say "Good morning!" with mood "happy"

Or simple: teach [trigger] = [response]"""
    
    except Exception as e:
        return f"Hmm, I had trouble learning that. Could you rephrase it? Error: {e}"

def cmd_teach_variation(args):
    """
    Add a variation to an existing response
    Usage: add variation "trigger" with "new response"
    """
    try:
        pattern = r'(?:add\s+variation|variation)\s+["\'](.+?)["\']\s+(?:with|as)\s+["\'](.+?)["\']'
        match = re.search(pattern, args, re.IGNORECASE)
        
        if match:
            trigger = match.group(1).strip()
            variation = match.group(2).strip()
            
            if trainer.add_response_variation(trigger, variation):
                return f"Perfect! *smiles* I've added a new way to respond to '{trigger}'. Now I can be more varied!"
            else:
                return f"Hmm, I don't have a base response for '{trigger}' yet. Teach me the main response first!"
        else:
            return """To add a variation:
            
 Format: add variation "trigger phrase" with "alternative response"

Example: add variation "good morning" with "*waves* Morning! Ready for another day?"""
    
    except Exception as e:
        return f"I couldn't add that variation. Error: {e}"

def cmd_teach_conversation(args):
    """
    Teach a complete conversation example
    Usage: learn conversation "user says" then "nova responds"
    """
    try:
        pattern = r'(?:learn\s+conversation|conversation)\s+["\'](.+?)["\']\s+(?:then|->)\s+["\'](.+?)["\']'
        match = re.search(pattern, args, re.IGNORECASE)
        
        if match:
            user_input = match.group(1).strip()
            nova_response = match.group(2).strip()
            
            trainer.teach_conversation_flow(user_input, nova_response)
            return f"*nods* I've learned this conversation pattern! I'll remember how to respond naturally."
        else:
            return """Teach me a conversation flow:
            
 Format: learn conversation "what user says" then "how I should respond"

Example: learn conversation "I'm tired" then "You should rest. Don't overwork yourself."
"""
    
    except Exception as e:
        return f"I couldn't learn that conversation. Error: {e}"

def cmd_training_stats(args):
    """Show training statistics"""
    try:
        summary = trainer.export_training_summary()
        
        stats_text = f""" **Training Statistics**

✅ Total Patterns Learned: {summary['total_patterns']}
 Conversation Examples: {summary['total_examples']}
 Response Templates: {summary['total_templates']}
️ Categories: {', '.join(summary['categories']) if summary['categories'] else 'None yet'}

"""
        
        if summary['most_used_patterns']:
            stats_text += " **Most Used Patterns:**\n"
            for i, pattern in enumerate(summary['most_used_patterns'], 1):
                stats_text += f"{i}. '{pattern['trigger']}' (used {pattern['usage_count']} times)\n"
        
        return stats_text
    
    except Exception as e:
        return f"Error getting stats: {e}"

def cmd_training_suggestions(args):
    """Get suggestions for improving conversation quality"""
    try:
        # Get recent conversations from memory
        from core.conversation_memory import ConversationMemory
        memory = ConversationMemory()
        recent = memory.get_recent_context(10)
        
        suggestions = trainer.get_training_suggestions(recent)
        
        response = " **Training Suggestions:**\n\n"
        for suggestion in suggestions:
            response += f"• {suggestion}\n"
        
        return response
    
    except Exception as e:
        return f"Error analyzing conversations: {e}"

def cmd_analyze_quality(args):
    """Analyze the quality of the last conversation"""
    try:
        from core.conversation_memory import ConversationMemory
        memory = ConversationMemory()
        recent = memory.get_recent_context(1)
        
        if not recent:
            return "No recent conversations to analyze!"
        
        last_conv = recent[-1]
        analysis = trainer.analyze_conversation_quality(
            last_conv.get('user', ''),
            last_conv.get('nova', '')
        )
        
        metrics = analysis['metrics']
        overall_data = analysis['overall_quality']
        overall = overall_data['score'] if isinstance(overall_data, dict) else overall_data
        
        # Create visual quality indicator
        quality_emoji = "" if overall >= 0.8 else "✨" if overall >= 0.6 else "" if overall >= 0.4 else "⚠️"
        
        response = f"""{quality_emoji} **Conversation Quality Analysis**

 Overall Score: {overall:.1%}

**Metrics:**
• Length Appropriateness: {metrics['length_score']:.1%}
• Emotional Engagement: {metrics['emotional_engagement']:.1%}
• Personality Consistency: {metrics['personality_consistency']:.1%}
• Natural Flow: {metrics['natural_flow']:.1%}

"""
        
        # Add recommendations
        if metrics['emotional_engagement'] < 0.5:
            response += " Tip: Add more emotions or engaging elements!\n"
        if metrics['personality_consistency'] < 0.5:
            response += " Tip: Keep Nova's personality consistent across responses!\n"
        if metrics['natural_flow'] < 0.5:
            response += " Tip: Avoid robotic AI phrases, stay natural!\n"
        
        return response
    
    except Exception as e:
        return f"Error analyzing quality: {e}"

def cmd_forget_training(args):
    """Clear training data"""
    try:
        # Safety check
        if "confirm" not in args.lower():
            return """⚠️ This will delete all trained patterns!

To confirm, say: "forget training confirm"

This will clear:
• All taught responses
• Conversation examples
• Response variations"""
        
        trainer.clear_training_data()
        return "️ All training data has been cleared. I'm ready to learn fresh!"
    
    except Exception as e:
        return f"Error clearing training: {e}"

def cmd_export_training(args):
    """Export training summary"""
    try:
        summary = trainer.export_training_summary()
        
        import json, os
        export_text = json.dumps(summary, indent=2, ensure_ascii=False)
        
        os.makedirs("userdata", exist_ok=True)
        # Save to file
        export_file = os.path.join("userdata", "training_export.json")
        with open(export_file, 'w', encoding='utf-8') as f:
            f.write(export_text)
        
        return f"✅ Training data exported to {export_file}!\n\n{export_text[:500]}..."
    
    except Exception as e:
        return f"Error exporting training: {e}"

def register(dispatcher):
    """Register training commands"""
    dispatcher.register("teach", cmd_teach_response)
    dispatcher.register("learn", cmd_teach_response)
    dispatcher.register("add variation", cmd_teach_variation)
    dispatcher.register("variation", cmd_teach_variation)
    dispatcher.register("learn conversation", cmd_teach_conversation)
    dispatcher.register("training stats", cmd_training_stats)
    dispatcher.register("training suggestions", cmd_training_suggestions)
    dispatcher.register("analyze quality", cmd_analyze_quality)
    dispatcher.register("quality check", cmd_analyze_quality)
    dispatcher.register("forget training", cmd_forget_training)
    dispatcher.register("export training", cmd_export_training)
