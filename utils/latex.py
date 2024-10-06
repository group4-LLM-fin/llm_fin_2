import re

def is_latex(text):
    """
    Check if a string contains LaTeX content.
    Returns True if LaTeX symbols/commands are detected, otherwise False.
    """
    # Regular expression to detect common LaTeX commands or delimiters
    latex_patterns = [
        r"\\[a-zA-Z]+",    # LaTeX commands starting with backslash (e.g., \frac, \text)
        r"\$",             # Dollar signs used to denote inline LaTeX
        r"\{|\}",          # Curly braces used for grouping in LaTeX
        r"\^|_",           # Superscript or subscript symbols
    ]
    
    # Combine all patterns into one regular expression
    combined_pattern = "|".join(latex_patterns)
    
    # Search the text for any LaTeX pattern
    if re.search(combined_pattern, text):
        return True
    return False
