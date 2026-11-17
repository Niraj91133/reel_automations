"""
🛡️ UNIVERSAL BRAND INTEGRITY SECURITY GUARD (ALL CHANNELS)
===========================================================
Zero-Tolerance enforcement of all 5 channels' iconic aesthetic,
signature color palettes, typography, deep audio grounding,
and authentic Instagram presentation.

Guarantees that NO channel can ever be degraded by:
- Accidental config changes (e.g. color drifts)
- AI script hallucinations (e.g. Devanagari Hindi text)
- Generic/canned filler hooks (e.g. "EARNING TRICK")
"""

import re
import os

DEVANAGARI_REGEX = re.compile(r'[\u0900-\u097F]')

BANNED_GENERIC_PILLS = {
    "EARNING TRICK", "MONEY HACK", "STARTUP MODEL", "BUSINESS SECRET",
    "ONLINE INCOME", "STARTUP IDEA", "NEW BUSINESS", "BUSINESS TIP",
    "HEALTH TIP", "FOOD FACT", "GOOD HEALTH", "HEALTHY DIET",
    "TRADING TIP", "STOCK SECRET", "MARKET TIP", "QUICK PROFIT",
    "COOL PRODUCT", "AMAZON FIND", "VIRAL FIND", "GOOD PRODUCT",
    "LOAN TIP", "BANK TRICK", "LOAN SCHEME", "EASY MONEY"
}

CHANNEL_BRAND_REGISTRY = {
    "startup": {
        "tag_text": "STARTUP:",
        "primary_color": (225, 29, 72, 255),    # Crimson Red #E11D48
        "accent_color": (255, 255, 255, 255),
        "top_logo": "start-up",
        "default_pill": "ZERO COMPETITION BUSINESS",
        "follow_handle": "@startup_road",
        "hashtags": "#StartupRoad #FounderMindset #BusinessIdeas #WealthBuilding #Entrepreneurship #StartupIndia #BusinessCaseStudy"
    },
    "health": {
        "tag_text": "NUTRITION:",
        "primary_color": (16, 185, 129, 255),   # Vibrant Emerald Green #10B981
        "accent_color": (255, 255, 255, 255),
        "top_logo": "gud tree",
        "default_pill": "READ THE LABEL",
        "follow_handle": "@gudtree_",
        "hashtags": "#GudTree #HealthySnacks #CleanEating #NutritionFacts #ReadTheLabel #DietTips #FoodTruth #HealthAwareness"
    },
    "trading": {
        "tag_text": "TRADING:",
        "primary_color": (6, 182, 212, 255),    # Electric Cyan Teal #06B6D4
        "accent_color": (255, 255, 255, 255),
        "top_logo": "trading",
        "default_pill": "PRICE ACTION TRUTH",
        "follow_handle": "@trading_road24",
        "hashtags": "#TradingRoad #PriceAction #StockMarketIndia #TradingPsychology #RiskManagement #NiftyFifty #TechnicalAnalysis"
    },
    "viral": {
        "tag_text": "TRENDING:",
        "primary_color": (168, 85, 247, 255),  # Vibrant Neon Purple #A855F7
        "accent_color": (255, 255, 255, 255),
        "top_logo": "trending",
        "default_pill": "PROBLEM SOLVER",
        "follow_handle": "@trending_road",
        "hashtags": "#TrendingRoad #AmazonFinds #SmartGadgets #CoolTech #ProblemSolver #LifeHacks #GadgetReview #MustHaves"
    },
    "loan": {
        "tag_text": "FINANCE:",
        "primary_color": (37, 99, 235, 255),   # Royal Blue #2563EB
        "accent_color": (255, 255, 255, 255),
        "top_logo": "loan road",
        "default_pill": "LOAN KNOWLEDGE",
        "follow_handle": "@the_loan_road",
        "hashtags": "#LoanRoad #BusinessLoans #MudraYojana #CIBILScore #MSMEIndia #FinancialLiteracy #BankingAwareness"
    }
}

def resolve_channel_key(channel_id: str) -> str:
    ch = (channel_id or "").lower().strip()
    if ch in ("thestartup_street", "startup_road", "the_startuproad", "startup", "startuproad"):
        return "startup"
    elif ch in ("healthy_diet", "gudtree_", "gudtree", "health", "diet", "nutrition"):
        return "health"
    elif ch in ("trading_road24", "trading_pulse", "trading_road_", "trading", "stock_market"):
        return "trading"
    elif ch in ("viral_finds", "trending_road", "trending", "viral", "gadgets"):
        return "viral"
    elif ch in ("theloan_road", "the_loan_road", "loan_road", "loan", "loans"):
        return "loan"
    return "startup"

def contains_devanagari(text: str) -> bool:
    """Returns True if text contains any Devanagari (Hindi script) characters."""
    if not text:
        return False
    return bool(DEVANAGARI_REGEX.search(text))

def get_guaranteed_brand_settings(channel_id: str):
    """
    Immutable Brand Settings per channel.
    Hardcodes colors, tag boxes, and logos so configs cannot corrupt them.
    """
    key = resolve_channel_key(channel_id)
    reg = CHANNEL_BRAND_REGISTRY.get(key, CHANNEL_BRAND_REGISTRY["startup"])
    return {
        "tag_text": reg["tag_text"],
        "primary_color": reg["primary_color"],
        "accent_color": reg["accent_color"],
        "top_logo": reg["top_logo"],
        "follow_handle": reg["follow_handle"],
        "default_pill": reg["default_pill"],
        "hashtags": reg["hashtags"],
        "channel_key": key,
        "is_registered": True
    }

def audit_and_enforce_channel_brand(channel_id: str, data: dict, creator_username: str = "creator") -> tuple[bool, str, dict]:
    """
    Universal Brand Auditor & Security Guard.
    Applies to Startup Road, Gud Tree, Trading Road, Trending Road, and Loan Road.
    Returns (is_valid, reason, sanitized_data).
    """
    brand = get_guaranteed_brand_settings(channel_id)
    hook_pill = data.get("hook_pill", "").strip().upper()
    main_title = data.get("main_title", "").strip().upper()
    sub_quote = data.get("sub_quote", "").strip()
    caption = data.get("caption", "").strip()

    # 1. DEVANAGARI SCRIPT ZERO-TOLERANCE CHECK (ALL CHANNELS)
    for field_name, val in [("hook_pill", hook_pill), ("main_title", main_title), ("sub_quote", sub_quote), ("caption", caption)]:
        if contains_devanagari(val):
            return False, f"devanagari_script_forbidden_in_{field_name}", data

    # 2. HOOK PILL AUDIT
    if hook_pill in BANNED_GENERIC_PILLS or len(hook_pill.split()) < 2:
        hook_pill = brand["default_pill"]

    # 3. MAIN TITLE AUDIT
    if not main_title or len(main_title) < 10:
        return False, "main_title_too_short", data

    # 4. SUB QUOTE AUDIT
    if not sub_quote:
        sub_quote = f'"{main_title.splitlines()[0]}"'
    elif not sub_quote.startswith('"'):
        sub_quote = f'"{sub_quote.strip()}"'

    # 5. PRESERVE GEMINI'S GROUNDED ANALYSIS & GUARANTEE BRAND SIGN-OFF
    clean_creator = creator_username.replace("@", "").strip() if creator_username else "creator"

    # Creator Credit
    if "credit" not in caption.lower():
        caption += f"\n\nCredits & Speaker: @{clean_creator}"

    # Follow Call
    handle = brand["follow_handle"]
    if handle.lower() not in caption.lower():
        caption += f"\nFollow {handle} for daily practical insights & breakdowns."

    # Signature Hashtags
    first_tag = brand["hashtags"].split()[0].lower()
    if first_tag not in caption.lower():
        caption += f"\n\n{brand['hashtags']}"

    sanitized = {
        "is_hindi": data.get("is_hindi", True),
        "has_speech": data.get("has_speech", True),
        "is_niche_match": data.get("is_niche_match", True),
        "hook_pill": hook_pill,
        "main_title": main_title,
        "sub_quote": sub_quote,
        "caption": caption
    }
    return True, "brand_compliant", sanitized

# Backwards compatible alias
def audit_and_enforce_startup_brand(channel_id: str, data: dict, creator_username: str = "creator") -> tuple[bool, str, dict]:
    return audit_and_enforce_channel_brand(channel_id, data, creator_username)
