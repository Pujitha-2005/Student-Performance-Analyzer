from django import template

register = template.Library()

@register.filter
def to_alpha(value):
    """
    Converts an integer to its corresponding uppercase alphabet letter (A=1, B=2, etc.).
    Useful for generating options like A, B, C, D.
    """
    if isinstance(value, int) and value >= 1 and value <= 26:
        return chr(64 + value)  # 64 + 1 = 65 (ASCII for A), 64 + 2 = 66 (ASCII for B)
    return "" # Return empty string for invalid input