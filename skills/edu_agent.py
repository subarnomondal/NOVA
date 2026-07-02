import os
import datetime

def cmd_lesson_plan(args):
    """Usage: create lesson plan for <topic>"""
    query = args.replace("create lesson plan for", "").replace("lesson plan", "").strip()
    if not query: return "What topic should I create a lesson plan for? "
    
    print(f" Generating Lesson Plan: {query}")
    try:
        from core.llm_manager import llm_manager
        system_prompt = (
            "You are a professional teacher. Create a structured lesson plan including: "
            "Objectives, Materials, Introduction, Core Activity, and Conclusion. "
            "Keep it professional and academic."
        )
        plan = llm_manager.generate(f"Create a lesson plan for: {query}", system_prompt=system_prompt)
        return plan if plan else "I couldn't generate the plan right now."
    except Exception as e:
        return f"Lesson Planning Error: {e}"

def cmd_study_helper(args):
    """General academic help logic."""
    if "flashcard" in args.lower():
        return "I can help you generate flashcards! Just give me a topic and I'll write them out for you. "
    if "gpa" in args.lower():
        return "I can calculate your GPA! Just list your grades and credits like: GPA A 4, B 3... "
    return "I'm your Academic Assistant! I can help with lesson plans, flashcards, GPA math, and citations. "

def cmd_citation_generator(args):
    """Autonomously formats citations."""
    query = args.replace("format citation", "").replace("cite", "").strip()
    if not query: return "Provide the source details you want me to cite! (e.g. cite Book Title by Author) "
    
    try:
        from core.llm_manager import llm_manager
        style = "APA"
        if "mla" in args.lower(): style = "MLA"
        
        prompt = f"Format this source in {style} style: {query}. Output ONLY the citation."
        citation = llm_manager.generate(prompt, raw_gen=True)
        if not citation:
            return "I'm sorry, I couldn't generate that citation right now. Please try again later."
            
        return f"Here is your {style} citation:\n\n{citation.strip()}"
    except Exception as e:
        return f"Citation Error: {e}"

def register(dispatcher):
    dispatcher.register("lesson plan", cmd_lesson_plan)
    dispatcher.register("create lesson plan", cmd_lesson_plan)
    dispatcher.register("study helper", cmd_study_helper)
    dispatcher.register("academic help", cmd_study_helper)
    dispatcher.register("cite", cmd_citation_generator)
    dispatcher.register("format citation", cmd_citation_generator)
