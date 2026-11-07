"""
Compliance Guard Facade routing directly into Meta Iron Shield.
"""
from core.iron_shield import (
    is_reel_100pct_safe,
    check_text_lexical_compliance,
    check_semantic_policy_with_ai,
    CircuitBreaker,
    VelocityGovernor,
    get_safe_evergreen_replacement,
    BANNED_DANGER_ZONES
)

# Backwards compatible alias
def is_reel_compliant(title: str, hook_pill: str = "", caption: str = "", gemini_api_key: str = None) -> tuple[bool, str]:
    return is_reel_100pct_safe(title, hook_pill, caption, gemini_api_key)

def check_text_compliance(text: str) -> tuple[bool, str, str]:
    return check_text_lexical_compliance(text)

def filter_compliant_hunted_reels(candidates: list) -> list:
    safe = []
    for c in candidates:
        if isinstance(c, dict):
            txt = f"{c.get('title', '')} {c.get('description', '')}"
        else:
            txt = f"{c[1]} {c[2]}"
        is_ok, cat, phrase = check_text_lexical_compliance(txt)
        if is_ok:
            safe.append(c)
        else:
            print(f"🛡️ [Iron Shield] Candidate dropped: [{cat}] '{phrase}'")
    return safe
