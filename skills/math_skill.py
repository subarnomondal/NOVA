"""
Math Skill for Nova
Handles basic arithmetic and calculation requests safely.
"""
import re
import random

def cmd_calculate(args):
    """Usage: calculate 5 + 5, what is 2 times 3"""
    try:
        # Pre-cleaning: Remove "calculate", "solve", "what is", "math"
        expression = args.lower()
        expression = expression.replace("calculate", "").replace("solve", "").replace("what is", "").replace("math", "").strip()
        

        
        # Custom Unit Conversion: "90 degrees" -> "math.radians(90)"
        expression = re.sub(r'(\d+(?:\.\d+)?)\s*degrees?', r'math.radians(\1)', expression, flags=re.IGNORECASE)

        # ASR/Speech Correction Map
        # Note: Order matters! Longer phrases first to avoid partial replacements.
        replacements = {
            "square root": "math.sqrt", 
            "root": "math.sqrt",
            "sqrt": "math.sqrt",
            # Trig
            "sine": "math.sin",
            "sin": "math.sin",
            "cosine": "math.cos",
            "cos": "math.cos",
            "tangent": "math.tan",
            "tan": "math.tan",
            # Logs/Other
            "log": "math.log10",
            "ln": "math.log",
            "factorial": "math.factorial",
            # Constants - Use word boundaries in regex
            "pi": "math.pi",
            "euler": "math.e",
            # Cleanups (Units/Stopwords)
            "radians": "",
            "radian": "",
            "plus": "+",
            "add": "+",
            "minus": "-",
            "subtract": "-",
            "times": "*",
            "multiply": "*",
            "multiplied by": "*",
            "divided by": "/",
            "divide": "/",
            "over": "/",
            "power of": "**",
            "squared": "**2",
            "cubed": "**3",
            "to": "",
            "of": "",
            # Symbols
            "π": "math.pi",
            "√": "math.sqrt",
            "^": "**",
            "×": "*",
            "÷": "/",
            "−": "-",
            "the": "",
            "what is": "",
            "what's": ""
        }
        
        # Sort keys by length (descending) to match 'square root' before 'root'
        sorted_keys = sorted(replacements.keys(), key=len, reverse=True)
        
        for word in sorted_keys:
            op = replacements[word]
            # Use regex with word boundaries for words, but literal for symbols
            if word.isalpha():
                 pattern = r'(?<!math\.)\b' + re.escape(word) + r'\b'
            else:
                 pattern = re.escape(word)
            
            expression = re.sub(pattern, op, expression, flags=re.IGNORECASE)
        
        # fix: wrap sqrt argument in parens if missing (e.g. "math.sqrt 9" -> "math.sqrt(9)")
        # Supports: sqrt, sin, cos, tan, log, log10, factorial, degrees, radians
        # Also supports nested calls like: math.sin math.radians(90) -> math.sin(math.radians(90))
        expression = re.sub(r'(math\.[a-z0-9]+)\s+(\d+(?:\.\d+)?)', r'\1(\2)', expression)
        expression = re.sub(r'(math\.[a-z0-9]+)\s+(math\.[a-z0-9]+\([^\)]+\))', r'\1(\2)', expression)
        
        # Safety Check: Allow only numbers, operators, parentheses, decimal points, and 'math.sqrt'
        # We need to import math for sqrt to work
        import math
        
        # Validation Regex (Allow digits, operators, parens, dots, spaces)
        
        # Updated to remove all math functions for validation
        check_expr = expression.replace("**", "")
        allowed_funcs = [
            "math.sqrt", "math.sin", "math.cos", "math.tan", 
            "math.log10", "math.log", "math.factorial", 
            "math.degrees", "math.radians", "math.pi", "math.e",
            "math.gamma", "math.hypot", "math.ceil", "math.floor",
            "math.abs", "math.pow"
        ]
        for func in allowed_funcs:
            check_expr = check_expr.replace(func, "")
        
        if not re.match(r'^[\d\s\+\-\*\/\.\(\)a-z_]*$', check_expr):
            # Fallback: If it's not a math equation, return None so other skills (like generic LLM) can handle it
             return None
        
        # Evaluation
        # We use a restricted dictionary allowing only 'math' module usage if needed, though simpleeval is better if available.
        # Here we trust the regex filter.
        result = eval(expression, {"__builtins__": None, "math": math})
        
        # Formatting result (remove .0 if integer)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
            
        responses = [
            f"That's easy! The answer is {result}! ✨",
            f"According to my calculations... it's {result}! 🤓",
            f"Math wizard mode activated! It's {result}! 🪄",
            f"Let me solve that... done! The result is {result}! (◕‿◕✿)"
        ]
        return random.choice(responses)
        
    except Exception as e:
        print(f"Math Error: {e}")
        return "Oops! I couldn't solve that equation. Maybe check your syntax? 😵‍💫"

def register(dispatcher):
    dispatcher.register("calculate", cmd_calculate)
    dispatcher.register("solve", cmd_calculate)
    dispatcher.register("math", cmd_calculate)
    dispatcher.register("what is", cmd_calculate)
