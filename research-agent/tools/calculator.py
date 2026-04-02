from langchain.tools import tool
import math
import re

@tool
def calculator(expression: str) -> str:
    """Perform arithmetic calculations. Input must be a math expression like 
    '100 * 1.5' or '28.7 / 3.7' or 'sqrt(144)'. Always use this for any numeric calculation."""
    try:
        # For calculator safety: only allow these characters before eval
        if not re.match(r'^[0-9+\-*/().\s,mathsqrpowlogflorceilroundabsin]+$', expression):
            return "Error: unsafe expression"
            
        # Replace "sqrt(" with "math.sqrt(" before eval for safety
        safe_expr = expression.replace("sqrt(", "math.sqrt(")
        
        # Only allow math functions, no built-ins for safety
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        
        # Using eval with safe builtins and math functions
        result = eval(safe_expr, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception:
        return "Error: could not evaluate expression. Try a simpler form like '28.7 / 3.7'"
