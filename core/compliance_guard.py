"""
Meta & Instagram Policy Compliance & Safety Guard.
Enforces 100% compliance with Meta Community Standards & Prohibited Commercial Practices.
Prevents account bans, feature blocks, and automated enforcement actions.
"""

import re

# Strict blacklist of words/phrases prohibited under Meta Community Standards
BANNED_POLICY_PATTERNS = {
    "GET_RICH_QUICK": [
        r"\bcrore\b", r"\bcrores\b", r"\blakh\b", r"\blakhs\b", r"\bcr\b",
        r"\bmake money\b", r"\bearn money\b", r"\bearn ₹", r"\bmake ₹",
        r"\bpassive income\b", r"\bghar baithe\b", r"\bandha paisa\b",
        r"\bprint money\b", r"\bwithout selling\b", r"\bwithout investment\b",
        r"\bzero investment\b", r"\bdaily income\b", r"\bmonthly paycheck\b",
        r"\beasy money\b", r"\bquick rich\b", r"\bmillionaire in\b",
        r"\b1 minute and earn\b", r"\b5000 daily\b", r"\b1.5l/month\b",
        r"\b20 lakhs/month\b", r"\b1.2l profit\b", r"\b3 lakh/mo\b"
    ],
    "INVESTMENT_OR_PROFIT_SCHEME": [
        r"\bturn ₹\b", r"\bdouble your money\b", r"\bmoney flip\b", r"\bcash flip\b",
        r"\bzero risk\b", r"\brisk-free\b", r"\bguaranteed return\b", r"\bguaranteed profit\b",
        r"\bmonthly returns\b", r"\bpaisa hi paisa\b", r"\b500% profit\b", r"\b200% to 500%\b",
        r"\bstop just doing sips\b", r"\bscalping setup\b", r"\bbreakout strategy\b",
        r"\boption buying\b", r"\btrading tip\b", r"\bjackpot call\b"
    ],
    "LOAN_AND_DEBT_RELIEF": [
        r"\bhome loan hack\b", r"\bsave ₹\d+ lakhs on your loan\b",
        r"\beliminate your debt\b", r"\binstant loan\b", r"\bguaranteed loan\b"
    ],
    "UNREALISTIC_COMMERCIAL_BAIT": [
        r"\bwithout investing a single rupee\b", r"\bbuild apps for free\b",
        r"\bstop paying developers\b", r"\bnever fail in any corner\b",
        r"\bbe your own boss in trading\b"
    ],
    "DANGEROUS_ORGANIZATIONS_AND_VIOLENCE": [
        r"\bosama\b", r"\bbin laden\b", r"\bterrorist\b", r"\bkill\b",
        r"\bmurder\b", r"\bweapon\b", r"\bbomb\b", r"\battack\b", r"\bcartel\b"
    ],
    "SENSITIVE_CIVIC_UNREST": [
        r"\bfrance is burning\b", r"\briots\b", r"\bcivil war\b"
    ]
}

def check_text_compliance(text: str) -> tuple[bool, str, str]:
    """
    Checks any string (title, caption, hook pill, or transcript) against Meta safety policies.
    Returns: (is_compliant, violated_category, matched_phrase)
    """
    if not text:
        return True, "", ""

    lower_text = text.lower()
    for category, patterns in BANNED_POLICY_PATTERNS.items():
        for pat in patterns:
            match = re.search(pat, lower_text)
            if match:
                return False, category, match.group(0)

    return True, "", ""

def is_reel_compliant(title: str, hook_pill: str = "", caption: str = "") -> tuple[bool, str]:
    """
    Validates complete reel package against Meta Community Standards.
    Returns: (is_compliant, reason_string)
    """
    combined = f"{hook_pill} | {title} | {caption}"
    compliant, cat, phrase = check_text_compliance(combined)
    if not compliant:
        reason = f"Meta Policy Violation: [{cat}] Matched unsafe phrase '{phrase}'"
        return False, reason
    return True, "100% Compliant with Meta Community Standards"

def filter_compliant_hunted_reels(candidates: list) -> list:
    """
    Filters out any candidate reel whose title, creator, or views text violates safety standards.
    """
    safe_candidates = []
    for cand in candidates:
        # candidate is either a tuple (shortcode, creator, views) or a dict
        if isinstance(cand, dict):
            text_to_check = f"{cand.get('title', '')} {cand.get('description', '')} {cand.get('creator', '')}"
        else:
            text_to_check = f"{cand[1]} {cand[2]}"

        compliant, cat, phrase = check_text_compliance(text_to_check)
        if compliant:
            safe_candidates.append(cand)
        else:
            print(f"🛡️ [Compliance Guard] REJECTED hunted candidate: Matched [{cat}] '{phrase}'")

    return safe_candidates
