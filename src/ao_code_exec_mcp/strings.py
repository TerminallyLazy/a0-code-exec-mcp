"""
String utilities - Ported from Agent Zero
Text truncation and manipulation functions
"""


def truncate_text(text: str, length: int, at_end: bool = True, replacement: str = "...") -> str:
    """
    Truncate text to specified length with replacement string.
    Ported from Agent Zero's strings.py
    """
    orig_length = len(text)
    if orig_length <= length:
        return text

    if at_end:
        return text[:length] + replacement
    else:
        return replacement + text[-length:]


def truncate_text_by_ratio(
    text: str, threshold: int, replacement: str = "...", ratio: float = 0.5
) -> str:
    """
    Truncate text with replacement at a specified ratio position.
    Ported from Agent Zero's strings.py
    """
    threshold = int(threshold)
    if not threshold or len(text) <= threshold:
        return text

    ratio = max(0.0, min(1.0, float(ratio)))
    available_space = threshold - len(replacement)

    if available_space <= 0:
        return replacement[:threshold]

    if ratio == 0.0:
        return replacement + text[-available_space:]
    elif ratio == 1.0:
        return text[:available_space] + replacement
    else:
        start_len = int(available_space * ratio)
        end_len = available_space - start_len
        return text[:start_len] + replacement + text[-end_len:]
