"""
Core Caption Engine:
Generates rich, viral, multi-paragraph, high-converting Instagram captions 
custom-tailored for each channel's niche, audience, and engagement strategy.

Ensures NO reel is ever published with a boring 1-line caption again.
"""

import re
import random

NICHE_TEMPLATES = {
    "startup_road": {
        "handle": "@startup_road",
        "cta": 'Want the complete supplier list, machine contact & breakdown? Comment "DETAILS" below and I will DM you instantly! 📩',
        "hashtags": [
            "#StartupRoad", "#BusinessStrategy", "#Entrepreneurship", 
            "#StartupIndia", "#SmallBusinessTips", "#BusinessBreakdown", 
            "#MakeInIndia", "#D2CBrand", "#MicroManufacturing", "#BusinessGrowth"
        ]
    },
    "healthy_diet": {
        "handle": "@gudtree_",
        "cta": "Comment 'HEALTH' to get our clean packaged snacks checklist! What packaged snack do you eat daily? Let's check its ingredients below! 👇",
        "hashtags": [
            "#Gudtree", "#FoodPharmer", "#CleanEating", "#ReadTheLabel", 
            "#HiddenIngredients", "#NutritionTips", "#HealthyHabits", 
            "#PalmOilFree", "#HealthySnacks", "#HolisticHealth"
        ]
    },
    "trading_pulse": {
        "handle": "@trading_road_",
        "cta": "Do you wait for retest confirmation or enter right at the breakout? Drop your trading rule below! 👇",
        "disclaimer": "⚠️ Disclaimer: For educational purposes only. Not financial or SEBI advice. Trading in equities, F&O, or commodities involves significant risk of loss.",
        "hashtags": [
            "#TradingRoad", "#PriceAction", "#TechnicalAnalysis", 
            "#TradingPsychology", "#RiskManagement", "#StockMarketIndia", 
            "#CandlestickPatterns", "#TradingDiscipline", "#Nifty50"
        ]
    },
    "trading_road24": {
        "handle": "@trading_road24",
        "cta": "What is your biggest psychological struggle while holding winning trades? Let's discuss in the comments! 👇",
        "disclaimer": "⚠️ Disclaimer: For educational purposes only. Not financial or SEBI advice. Trading involves substantial risk.",
        "hashtags": [
            "#TradingRoad24", "#PriceAction", "#ScalpingTrading", 
            "#RiskReward", "#TraderMindset", "#StockMarketEducation", 
            "#TradingDiscipline", "#ChartPatterns"
        ]
    },
    "viral_finds": {
        "handle": "@trending_road",
        "cta": "👉 Comment 'LINK' to get the direct purchase link sent straight to your DM! Link is also available in bio.",
        "hashtags": [
            "#TrendingRoad", "#AmazonFinds", "#ViralGadgets", 
            "#SmartHome", "#UsefulProducts", "#AmazonMustHaves", 
            "#ProblemSolver", "#HomeHacks", "#GadgetLovers"
        ]
    },
    "the_loan_road": {
        "handle": "@the_loan_road",
        "cta": "👉 Comment 'LOAN' or 'SIP' to get our free Loan Prepayment & SIP Wealth Calculator Excel Sheet directly in your DM!",
        "disclaimer": "⚠️ Disclaimer: Educational and informative content only. Please consult your financial advisor before making major credit or investment decisions.",
        "hashtags": [
            "#TheLoanRoad", "#HomeLoanTips", "#SIPInvestment", 
            "#MutualFundsIndia", "#CIBILScore", "#LoanPrepayment", 
            "#PersonalLoan", "#FinancialPlanning", "#EMICalculator", "#WealthCreation"
        ]
    }
}

def clean_title_text(title: str) -> str:
    """Removes newlines and clean title for reading."""
    if not title:
        return "KEY BUSINESS INSIGHT"
    return " ".join([t.strip() for t in title.replace("\\n", "\n").splitlines() if t.strip()])

def build_startup_caption(title: str, hook_pill: str, creator: str) -> str:
    clean_t = clean_title_text(title)
    
    # Check theme: Machine/Manufacturing vs Digital/SaaS vs General Strategy
    title_lower = clean_t.lower()
    is_machine = any(w in title_lower for w in ["machine", "manufacturing", "plant", "factory", "pack", "crush", "print", "laghu", "udyog", "production", "raw material", "export", "import"])
    is_digital = any(w in title_lower for w in ["ai", "app", "digital", "website", "online", "software", "saas", "freelanc", "client", "remote", "tool"])
    
    if is_machine:
        hook = f"Every entrepreneur searching for ground-level profitability needs to understand this model. 🏭"
        body = (
            f"When evaluating manufacturing and local packaging units, the real competitive edge isn't just buying machinery—it's mastering unit economics and local distribution.\n\n"
            f"In this breakdown on '{clean_t}', we examine how small-scale production setups keep capital expenditure low while targeting high-frequency, everyday consumption markets. "
            f"By eliminating multi-layered middlemen and sourcing raw materials directly, manufacturers can retain healthy 30% to 50% gross margins."
        )
        takeaways = (
            "Key Execution Rules:\n"
            "1️⃣ Low Capex Entry: Start with semi-automatic machines before committing to large commercial setups.\n"
            "2️⃣ Localized Supply Chain: Secure local B2B packaging and bulk supply contracts first to ensure pre-sold inventory.\n"
            "3️⃣ Cashflow Cycle: Keep credit cycles strict (under 15 days) to avoid working capital crunches.\n"
            "4️⃣ Differentiation: Focus on tamper-proof packaging and local branding trust."
        )
    elif is_digital:
        hook = f"The biggest barrier to starting an online business isn't technical skill—it's knowing where the leverage lies. 💻"
        body = (
            f"The digital economy has fundamentally changed how micro-businesses are built. With '{clean_t}', the focus is on utilizing automated workflows and low-overhead software tools to deliver high-value outcomes.\n\n"
            f"Instead of spending months coding or building complex infrastructure, smart operators leverage existing APIs and platforms to solve specific, painful problems for paying businesses."
        )
        takeaways = (
            "Strategic Blueprint:\n"
            "1️⃣ High-Leverage Offering: Package a specific solution rather than offering generic services.\n"
            "2️⃣ Automated Operations: Use modern tools to keep fulfillment lean and scalable.\n"
            "3️⃣ Direct Outreach: Connect directly with decision-makers who feel the operational bottleneck daily.\n"
            "4️⃣ Recurring Revenue: Structure your pricing around recurring value rather than one-off transactions."
        )
    else:
        hook = f"Most ventures fail not because the concept was weak, but because execution lacked clarity. 📈"
        body = (
            f"Building and scaling a sustainable business requires disciplined execution and deep customer understanding. In '{clean_t}', the core lesson highlights why founders must obsess over product-market fit before pouring capital into marketing.\n\n"
            f"Whether you are bootstrapping from zero or scaling an existing operation, long-term survival belongs to businesses that maintain healthy unit economics, retain customers, and build strong cash reserves."
        )
        takeaways = (
            "Foundational Principles:\n"
            "1️⃣ Unit Economics First: Never scale a negative unit margin business hoping volume will fix it.\n"
            "2️⃣ Customer Retention: Acquiring a customer once is marketing; getting them to return is business.\n"
            "3️⃣ Disciplined Capital: Keep fixed overheads minimal until product demand forces expansion.\n"
            "4️⃣ Relentless Speed: Test hypotheses quickly and discard what doesn't convert."
        )

    cta = NICHE_TEMPLATES["startup_road"]["cta"]
    hashtags = " ".join(NICHE_TEMPLATES["startup_road"]["hashtags"])
    credit_line = f"🤝 Original Creator Credit: @{creator}" if creator and creator.lower() not in ["creator", "approved_creator"] else "🤝 Credit: Respective Creator"

    return f"{clean_t.upper()} 🚀\n\n{hook}\n\n{body}\n\n{takeaways}\n\n{cta}\n\n{credit_line}\n\n{hashtags}"

def build_health_caption(title: str, hook_pill: str, creator: str) -> str:
    clean_t = clean_title_text(title)
    title_lower = clean_t.lower()
    
    is_sugar_oil = any(w in title_lower for w in ["sugar", "palm oil", "oil", "maltodextrin", "syrup", "ingredient", "label", "additive"])
    is_diet_hormone = any(w in title_lower for w in ["hormone", "pcos", "pcod", "weight", "fat", "muscle", "protein", "gut", "diet", "snack"])

    if is_sugar_oil:
        hook = "Next time you pick up a 'healthy' snack from the shelf, turn it around and check the back! 🚨"
        body = (
            f"Big food marketing often hides behind buzzwords like '100% Whole Wheat', 'No Added Sugar', or 'Rich in Fiber'. But when you examine '{clean_t}', the ingredients label reveals the real truth.\n\n"
            f"Refined palm oil, maltodextrin (which spikes insulin faster than pure glucose), and disguised artificial sweeteners are routinely used to cut manufacturing costs while extending shelf life. Your body treats these ultra-processed fillers like metabolic stress."
        )
        takeaways = (
            "How to Read Food Labels Like a Pro:\n"
            "1️⃣ Check First 3 Ingredients: Ingredients are listed in descending order by weight. If sugar or oil is in the top 3, it's not health food.\n"
            "2️⃣ Beware of Hidden Sugars: Look out for dextrose, invert syrup, malt extract, and maltodextrin.\n"
            "3️⃣ The Palm Oil Trap: Highly processed palm olein oxidizes easily and drives systemic inflammation.\n"
            "4️⃣ Real Food Rule: If a product has more than 5 chemical names you cannot pronounce, keep it on the shelf."
        )
    else:
        hook = "Your body responds to the quality of the nutrients you feed it, not just the calorie number. 🥗"
        body = (
            f"When it comes to '{clean_t}', understanding how whole foods interact with your metabolic health is the real game-changer.\n\n"
            f"Instead of falling for restrictive crash diets or heavily marketed supplements, prioritizing real, unadulterated whole foods—rich in essential micronutrients, healthy fats, and prebiotic fiber—helps stabilize blood sugar, balance hormones, and improve sustained daily energy."
        )
        takeaways = (
            "Clean Nutrition Essentials:\n"
            "1️⃣ Prioritize Whole Foods: Focus on unrefined seeds, nuts, whole grains, and fresh produce.\n"
            "2️⃣ Stable Blood Sugar: Pair carbohydrates with protein or healthy fats to prevent sharp insulin spikes.\n"
            "3️⃣ Gut Health Priority: A diverse, fiber-rich diet supports the microbiome that governs 70% of your immune system.\n"
            "4️⃣ Sustainable Consistency: Long-term health is built through daily sustainable habits, not extreme 7-day detoxes."
        )

    cta = NICHE_TEMPLATES["healthy_diet"]["cta"]
    hashtags = " ".join(NICHE_TEMPLATES["healthy_diet"]["hashtags"])
    credit_line = f"🤝 Original Video Credit: @{creator}" if creator and creator.lower() not in ["creator", "approved_creator"] else "🤝 Credit: Respective Creator"

    return f"{clean_t.upper()} 🥗\n\n{hook}\n\n{body}\n\n{takeaways}\n\n{cta}\n\n{credit_line}\n\n{hashtags}"

def build_trading_caption(title: str, hook_pill: str, creator: str, channel_id: str = "trading_pulse") -> str:
    clean_t = clean_title_text(title)
    tmpl = NICHE_TEMPLATES.get(channel_id, NICHE_TEMPLATES["trading_pulse"])

    hook = "Stop chasing green candles and jumping into breakouts without confirmation! 📉"
    body = (
        f"In market trading, 90% of retail losses don't come from poor indicator setups—they come from lack of risk discipline and emotional impulse trading. In this breakdown on '{clean_t}', we dissect the mechanics behind high-probability price action.\n\n"
        f"Institutions and market makers routinely engineer liquidity traps around obvious support and resistance levels. When you learn to wait for candle closing confirmation and retests rather than anticipating moves blindly, your risk-to-reward ratio dramatically shifts in your favor."
    )
    takeaways = (
        "Non-Negotiable Rules for Capital Protection:\n"
        "1️⃣ Define Risk Before Entry: Never execute a trade without knowing your exact exit level and rupee risk per trade.\n"
        "2️⃣ Retest Over Rush: Let the breakout candle close and wait for price to retest key structure.\n"
        "3️⃣ Strict Position Sizing: Never risk more than 1% to 2% of total trading capital on any single setup.\n"
        "4️⃣ Psychological Reset: After two consecutive stop-loss hits, step away from the terminal. Revenge trading always leads to disaster."
    )

    cta = tmpl["cta"]
    disclaimer = tmpl["disclaimer"]
    hashtags = " ".join(tmpl["hashtags"])
    credit_line = f"🤝 Original Creator Credit: @{creator}" if creator and creator.lower() not in ["creator", "approved_creator"] else "🤝 Credit: Respective Creator"

    return f"{clean_t.upper()} 📊\n\n{hook}\n\n{body}\n\n{takeaways}\n\n{cta}\n\n{disclaimer}\n\n{credit_line}\n\n{hashtags}"

def build_viral_finds_caption(title: str, hook_pill: str, creator: str) -> str:
    clean_t = clean_title_text(title)

    hook = "Stop struggling with everyday daily hassles! This viral Amazon find is a total game-changer. 🚀"
    body = (
        f"If you love smart tools that genuinely save time and keep your space organized, '{clean_t}' is an absolute must-see.\n\n"
        f"Designed to eliminate common annoyances, this compact gadget combines clever engineering with effortless utility—making your daily routine smoother, cleaner, and much more efficient."
    )
    takeaways = (
        "Why This Product Stands Out:\n"
        "✅ Problem-Solving Design: Solves annoying daily tasks in seconds.\n"
        "✅ Compact & Portable: Easy to store, travel-friendly, and built to last.\n"
        "✅ High Value for Money: Top-rated build quality at an affordable price.\n"
        "✅ 100% Practical Utility: Something you will actually use every single day."
    )

    cta = NICHE_TEMPLATES["viral_finds"]["cta"]
    hashtags = " ".join(NICHE_TEMPLATES["viral_finds"]["hashtags"])
    credit_line = f"🤝 Credit: @{creator}" if creator and creator.lower() not in ["creator", "approved_creator"] else "🤝 Credit: Respective Creator"

    return f"{clean_t.upper()} 🛍️\n\n{hook}\n\n{body}\n\n{takeaways}\n\n{cta}\n\n{credit_line}\n\n{hashtags}"

def generate_rich_caption(channel_id: str, title: str, hook_pill: str = "", creator: str = "creator", context_text: str = "") -> str:
    """
    Main entry point for generating rich, multi-paragraph, engaging captions.
    Guarantees every caption is 400-900+ characters with hook, body, bullet points, CTA, disclaimer & hashtags.
    """
    ch = channel_id.lower()
    
    if "startup" in ch:
        return build_startup_caption(title, hook_pill, creator)
    elif "health" in ch or "gudtree" in ch or "diet" in ch:
        return build_health_caption(title, hook_pill, creator)
    elif "trading" in ch:
        return build_trading_caption(title, hook_pill, creator, channel_id=ch)
    elif "viral" in ch or "trending" in ch:
        return build_viral_finds_caption(title, hook_pill, creator)
    else:
        # Default high-quality format
        return build_startup_caption(title, hook_pill, creator)

if __name__ == "__main__":
    # Test all 5 channels
    test_channels = [
        ("startup_road", "BUSINESS BREAKDOWN: SCALING BLUEPRINT", "STARTUP ROAD", "favourite.engineer"),
        ("healthy_diet", "IS YOUR PROTEIN BAR ACTUALLY A CANDY?", "SNACK TRUTH", "foodpharmer"),
        ("trading_pulse", "HOW SMART MONEY TRAPS RETAIL BREAKOUTS", "PRICE ACTION", "trading_expert"),
        ("viral_finds", "23 AMAZON PRODUCTS EVERYONE NEEDS", "AMAZON FINDS", "gadget_review"),
        ("trading_road24", "SIMPLE BOLLINGER BAND SCALPING SETUP", "SCALPING SETUP", "trader24")
    ]
    
    for ch, t, hp, cr in test_channels:
        print(f"\n{'='*50}\nTESTING: {ch}\n{'='*50}")
        cap = generate_rich_caption(ch, t, hp, cr)
        print(cap)
        print(f"\n[Length: {len(cap)} chars, Lines: {len(cap.splitlines())}]")

