"""
Core Caption Engine:
Generates rich, viral, high-converting Instagram captions 
matching the exact 100k-250k like benchmark format from @startup_road, @gudtree_, and @trading_road_.

Ensures NO reel is ever published with corporate boilerplate, generic essays, or placeholder text.
"""

import re
import random

NICHE_TEMPLATES = {
    "startup_road": {
        "handle": "@startup_road",
        "hashtags": [
            "#StartupRoad", "#FounderMindset", "#BusinessIdeas", 
            "#WealthBuilding", "#Entrepreneurship", "#StartupIndia", "#BusinessCaseStudy"
        ]
    },
    "the_startuproad": {
        "handle": "@the_startuproad",
        "hashtags": [
            "#TheStartupRoad", "#StartupRoad", "#FounderMindset", 
            "#BusinessIdeas", "#WealthBuilding", "#Entrepreneurship", "#StartupIndia"
        ]
    },
    "healthy_diet": {
        "handle": "@gudtree_",
        "hashtags": [
            "#Gudtree", "#FoodPharmer", "#CleanEating", "#ReadTheLabel", 
            "#HiddenIngredients", "#NutritionTips", "#PalmOilFree", "#HealthySnacks"
        ]
    },
    "trading_pulse": {
        "handle": "@trading_road_",
        "disclaimer": "⚠️ Disclaimer: For educational purposes only. Not financial or SEBI advice. Trading involves significant risk of loss.",
        "hashtags": [
            "#TradingRoad", "#PriceAction", "#TechnicalAnalysis", 
            "#TradingPsychology", "#RiskManagement", "#StockMarketIndia", "#CandlestickPatterns"
        ]
    },
    "trading_road24": {
        "handle": "@trading_road24",
        "disclaimer": "⚠️ Disclaimer: For educational purposes only. Not financial or SEBI advice. Trading involves substantial risk.",
        "hashtags": [
            "#TradingRoad24", "#PriceAction", "#ScalpingTrading", 
            "#RiskReward", "#TraderMindset", "#StockMarketEducation", "#ChartPatterns"
        ]
    },
    "viral_finds": {
        "handle": "@trending_road",
        "hashtags": [
            "#TrendingRoad", "#AmazonFinds", "#ViralGadgets", 
            "#SmartHome", "#UsefulProducts", "#AmazonMustHaves", "#ProblemSolver"
        ]
    },
    "the_loan_road": {
        "handle": "@the_loan_road",
        "disclaimer": "⚠️ Disclaimer: Educational and informative content only. Consult your financial advisor before making credit decisions.",
        "hashtags": [
            "#TheLoanRoad", "#HomeLoanTips", "#SIPInvestment", 
            "#MutualFundsIndia", "#CIBILScore", "#LoanPrepayment", "#FinancialPlanning"
        ]
    }
}

def clean_title_text(title: str) -> str:
    """Removes newlines and clean title for reading."""
    if not title:
        return "KEY BUSINESS INSIGHT"
    return " ".join([t.strip() for t in title.replace("\\n", "\n").splitlines() if t.strip()])

def derive_startup_trigger(text: str) -> tuple[str, str]:
    """
    Derives high-converting comment-to-DM trigger word and contextual breakdown
    based on the exact subject of the reel.
    """
    t = text.lower()
    
    if any(w in t for w in ["container", "cabin", "shipping"]):
        return "CONTAINER", (
            "• The Asset: Sourcing used shipping containers and converting them into portable offices or storage.\n"
            "• Unit Economics: Renting each unit for ₹15,000 to ₹30,000/month with zero permanent construction capex.\n"
            "• Scaling Edge: Positioning inventory near expanding highway and industrial infrastructure hubs."
        ), "Containers provide 3X the rental yield of traditional property with 1/10th the maintenance cost."
        
    elif any(w in t for w in ["petrol", "fuel", "pump", "shell"]):
        return "FUEL", (
            "• The Model: CODO dealership where the oil company provides land and equipment while you operate.\n"
            "• Unit Economics: High-volume commission per liter without sinking crores into real estate capex.\n"
            "• The Leverage: Operating a high-footfall location under a trusted national brand umbrella."
        ), "Asset-light models in heavy industries hide the real daily cash flow."
        
    elif any(w in t for w in ["battery", "lead", "acid", "recycle"]):
        return "BATTERY", (
            "• Source: Sourcing spent automotive and inverter batteries from local scrap dealers at scrap weight.\n"
            "• Recovery Value: Extracting purified lead and plastic components for secondary smelting factories.\n"
            "• Profit Velocity: Fast inventory turnover with 35% to 50% cash margins on recycled metal."
        ), "The most profitable businesses hide inside the hazardous waste streams of modern society."
        
    elif any(w in t for w in ["spark plug", "scrap", "iridium", "kachra", "metal", "waste"]):
        return "SCRAP", (
            "• Source: Collecting discarded spark plugs and industrial waste from mechanic garages for pennies.\n"
            "• Mechanism: Extracting high-value precious metals (Iridium and Platinum) from electrode tips.\n"
            "• Economics: Bulk processing converts automotive waste into high-margin industrial raw materials."
        ), "One industry's discarded trash is another operator's 500% profit margin."
        
    elif any(w in t for w in ["dry fruit", "kaju", "kismish", "makhana", "wholesale", "mandi", "hub"]):
        return "MARKET", (
            "• Source: Bypassing multi-layered state distributors and buying directly from primary production hubs.\n"
            "• Pricing Arbitrage: Sourcing at raw mandi rates doubles gross margins compared to regional wholesale.\n"
            "• Distribution: Supplying pre-packaged retail pouches to local B2B grocery chains on 7-day credit."
        ), "In commodity businesses, your profit is made on the buy side, not the sell side."
        
    elif any(w in t for w in ["paper bag", "paper cup", "packaging", "box", "pouch", "print"]):
        return "PACKAGING", (
            "• Setup: Compact semi-automatic packaging/printing machine requiring minimal square footage.\n"
            "• Market Demand: Plastic bans create non-negotiable repeat demand from bakeries, cafes, and retailers.\n"
            "• Cashflow Cycle: Securing 5 to 10 local B2B client contracts guarantees 100% pre-sold monthly inventory."
        ), "Boring, consumable daily packaging generates rock-solid cash flow in all market seasons."
        
    elif any(w in t for w in ["ice cream", "popsicle", "kulfi", "pop"]):
        return "ICECREAM", (
            "• Product Innovation: Bite-sized gourmet popsicles and sticks with premium visual presentation.\n"
            "• Cost Breakdown: Manufacturing cost under ₹8 per unit, retailing at ₹40 to ₹60 at high-footfall spots.\n"
            "• Distribution: Low-footprint kiosk carts and cloud freezer points with zero restaurant capex."
        ), "High-margin impulse treats beat sit-down dining economics every single time."
        
    elif any(w in t for w in ["chappal", "slipper", "footwear", "sole"]):
        return "CHAPPAL", (
            "• Production: Sheet cutting and strap fitting with a low-cost manual/hydraulic sole press.\n"
            "• Unit Cost: Production cost of ₹8 to ₹12 per pair, wholesaling at ₹25 to ₹35 to local tier-2/3 retail.\n"
            "• Scale Mechanism: Consistent repeat utility item with evergreen rural and urban demand."
        ), "Mass consumption goods with low unit capex build durable, recession-proof cash flow."
        
    elif any(w in t for w in ["drop", "dropship", "shopify", "roposo", "ecom"]):
        return "DROPSHIP", (
            "• Product Selection: Identifying viral problem-solving utility products with healthy ₹400+ markup.\n"
            "• Operational Lean: Zero upfront inventory risk by leveraging Indian supplier fulfillment networks.\n"
            "• Customer Acquisition: High-converting short-form creative angles running on optimized Meta ads."
        ), "E-commerce success is 20% product and 80% disciplined ad testing with positive ROAS."
        
    elif any(w in t for w in ["ai", "app", "website", "software", "client", "saas", "agency"]):
        return "WEBSITE", (
            "• The Offer: Packaging automated workflows and instant website templates for paying local businesses.\n"
            "• Execution Speed: Deploying no-code AI tools to complete client deliverables in 48 hours instead of weeks.\n"
            "• Pricing Structure: Charging ₹15k-₹35k upfront plus recurring monthly hosting and maintenance retainer."
        ), "Clients don't pay for hours worked; they pay for immediate solutions to painful operational bottlenecks."
        
    else:
        return "DETAILS", (
            "• The Core Asset: Targeting a high-demand, low-supply physical business model with protected margins.\n"
            "• Unit Economics: Keeping initial capital expenditure under ₹50,000 while maintaining 40%+ gross margins.\n"
            "• Execution Velocity: Securing pre-sold B2B supply agreements before committing to commercial scale."
        ), "True wealth is built by rotating capital into cash-flowing operations, not sitting on idle cash."

def build_startup_caption(title: str, hook_pill: str, creator: str, context_text: str = "") -> str:
    clean_t = clean_title_text(title)
    trigger, breakdown, takeaway = derive_startup_trigger(f"{title} {hook_pill} {context_text}")
    
    # Contrarian Line 1 Hooks
    t_lower = clean_t.lower()
    if "stop" in t_lower or "quit" in t_lower or "don't" in t_lower:
        hook_line = f"{clean_t} 🚫 👇"
    elif any(w in t_lower for w in ["₹", "crore", "lakh", "money", "profit"]):
        hook_line = f"{clean_t}! 💸 👇"
    else:
        hook_line = f"The hidden business model inside {clean_t}! 🚀 👇"

    credit_line = f"Credits & Speaker: @{creator}" if creator and creator.lower() not in ["creator", "approved_creator"] else "Credits: Respective Creator"
    hashtags = " ".join(NICHE_TEMPLATES["startup_road"]["hashtags"])

    return (
        f"{hook_line}\n\n"
        f"📌 The Founder Breakdown:\n"
        f"{breakdown}\n\n"
        f"💡 Golden Takeaway: {takeaway}\n\n"
        f"👇 Want the step-by-step PDF roadmap & supplier list?\n"
        f"Comment \"{trigger}\" below and I'll DM you the breakdown instantly! 📩\n\n"
        f"{credit_line}\n"
        f"Follow @startup_road for daily founder playbooks & business insights.\n\n"
        f"{hashtags}"
    )

def build_health_caption(title: str, hook_pill: str, creator: str, context_text: str = "") -> str:
    clean_t = clean_title_text(title)
    t_lower = f"{title} {hook_pill} {context_text}".lower()
    
    if any(w in t_lower for w in ["palm oil", "oil", "fat"]):
        trigger = "LABEL"
        breakdown = (
            "• Deceptive Front: Packaged as 'Heart Healthy' or '100% Whole Grain'.\n"
            "• The Reality: Cheap refined palm olein used to slash manufacturing costs and extend shelf life.\n"
            "• The Impact: Highly oxidized industrial oils drive systemic inflammation and arterial stress."
        )
        takeaway = "Real food does not require industrial preservatives to stay edible on a shelf for 12 months."
    elif any(w in t_lower for w in ["sugar", "sweet", "maltodextrin", "syrup"]):
        trigger = "CLEAN"
        breakdown = (
            "• Marketing Trick: Claims 'No Added White Sugar' on the front label.\n"
            "• Ingredient Check: Invert syrup, maltodextrin, and fruit concentrates deliver a massive glycemic shock.\n"
            "• Metabolic Result: Spikes insulin faster than table sugar while tricking your brain into craving more."
        )
        takeaway = "If sugar or syrup appears in the top 3 ingredients, treat it like candy, not nutrition."
    else:
        trigger = "SNACK"
        breakdown = (
            "• The Trap: Processed snacks loaded with emulsifiers, synthetic flavors, and hidden sodium.\n"
            "• Label Check: Chemical additives and numbered preservatives masquerading as natural ingredients.\n"
            "• Clean Pivot: Switching to single-ingredient whole foods: roasted chana, makhana, and raw nuts."
        )
        takeaway = "Invest in real food today, or pay tenfold to big pharma tomorrow."

    credit_line = f"Credits & Speaker: @{creator}" if creator and creator.lower() not in ["creator", "approved_creator"] else "Credits: Respective Creator"
    hashtags = " ".join(NICHE_TEMPLATES["healthy_diet"]["hashtags"])

    return (
        f"Next time you pick up this 'healthy' snack, check the label! 🚨 👇\n\n"
        f"📌 The Ingredient Breakdown:\n"
        f"{breakdown}\n\n"
        f"💡 Golden Rule: {takeaway}\n\n"
        f"👇 Want our verified Clean Packaged Snacks & Guilt-Free Food Guide?\n"
        f"Comment \"{trigger}\" below and I'll DM you the complete list! 📩\n\n"
        f"{credit_line}\n"
        f"Follow @gudtree_ for daily verified food label breakdowns.\n\n"
        f"{hashtags}"
    )

def build_trading_caption(title: str, hook_pill: str, creator: str, channel_id: str = "trading_pulse", context_text: str = "") -> str:
    clean_t = clean_title_text(title)
    tmpl = NICHE_TEMPLATES.get(channel_id, NICHE_TEMPLATES["trading_pulse"])
    
    credit_line = f"Credits & Speaker: @{creator}" if creator and creator.lower() not in ["creator", "approved_creator"] else "Credits: Respective Creator"
    hashtags = " ".join(tmpl["hashtags"])
    disclaimer = tmpl["disclaimer"]

    return (
        f"Stop buying breakouts right into institutional resistance! 📉 👇\n\n"
        f"📌 The Price Action Breakdown:\n"
        f"• The Retail Trap: Chasing green momentum candles where smart money engineers liquidity exits.\n"
        f"• The Confirmation Rule: Wait for the 15-minute candle to close and retest support before entry.\n"
        f"• Risk Discipline: Strictly risk no more than 1% of total trading capital per setup.\n\n"
        f"💡 Golden Takeaway: Amateurs obsess over potential profits; professional traders obsess over downside risk.\n\n"
        f"👇 Want our free Price Action & Risk Management Cheat Sheet?\n"
        f"Comment \"LEVELS\" below and I'll DM you the breakdown! 📩\n\n"
        f"{disclaimer}\n\n"
        f"{credit_line}\n"
        f"Follow @trading_road_ for daily institutional market analysis.\n\n"
        f"{hashtags}"
    )

def build_loan_caption(title: str, hook_pill: str, creator: str, context_text: str = "") -> str:
    clean_t = clean_title_text(title)
    credit_line = f"Credits & Speaker: @{creator}" if creator and creator.lower() not in ["creator", "approved_creator"] else "Credits: Respective Creator"
    hashtags = " ".join(NICHE_TEMPLATES["the_loan_road"]["hashtags"])
    disclaimer = NICHE_TEMPLATES["the_loan_road"]["disclaimer"]

    return (
        f"The 20-year home loan interest trap that banks never talk about! 💰 👇\n\n"
        f"📌 The Compounding Math Breakdown:\n"
        f"• The Bank Trap: On a ₹50 Lakh 20-year loan at 8.5%, you pay over ₹54 Lakhs in interest alone.\n"
        f"• The 1 Extra EMI Hack: Paying just 1 extra EMI every single year slashes your tenure by over 4.5 years.\n"
        f"• The SIP Counter-Balance: Starting a 10% SIP alongside your EMI recovers 100% of the loan interest paid.\n\n"
        f"💡 Golden Rule: Compound interest is terrifying when you pay it; it's life-changing when you earn it.\n\n"
        f"👇 Want our free Home Loan Prepayment & SIP Wealth Calculator Excel Sheet?\n"
        f"Comment \"CALCULATOR\" below and I'll DM you the sheet instantly! 📩\n\n"
        f"{disclaimer}\n\n"
        f"{credit_line}\n"
        f"Follow @the_loan_road for daily loan hacks & wealth compounding blueprints.\n\n"
        f"{hashtags}"
    )

def build_viral_finds_caption(title: str, hook_pill: str, creator: str, context_text: str = "") -> str:
    clean_t = clean_title_text(title)
    credit_line = f"Credits & Speaker: @{creator}" if creator and creator.lower() not in ["creator", "approved_creator"] else "Credits: Respective Creator"
    hashtags = " ".join(NICHE_TEMPLATES["viral_finds"]["hashtags"])

    return (
        f"Stop struggling with everyday annoyances! This ₹499 gadget is a game-changer. 🚀 👇\n\n"
        f"📌 Why This Product Solves It All:\n"
        f"• The Problem: Eliminates cluttered cords and messy spaces in seconds.\n"
        f"• Compact Design: Pocket-sized, durable build, and travel-friendly utility.\n"
        f"• Pure Value: Under ₹499 on sale with 100% practical daily use.\n\n"
        f"👉 Want the direct purchase link with discount?\n"
        f"Comment \"LINK\" below and I'll send the direct link to your DM! 🔗\n\n"
        f"{credit_line}\n"
        f"Follow @trending_road for daily problem-solving gadgets.\n\n"
        f"{hashtags}"
    )

def generate_rich_caption(channel_id: str, title: str, hook_pill: str = "", creator: str = "creator", context_text: str = "") -> str:
    """
    Main entry point for generating rich, multi-paragraph, engaging captions.
    Guarantees every caption follows the exact 100k-250k like viral architecture.
    """
    ch = channel_id.lower()
    
    if "loan" in ch:
        return build_loan_caption(title, hook_pill, creator, context_text)
    elif "health" in ch or "gudtree" in ch or "diet" in ch:
        return build_health_caption(title, hook_pill, creator, context_text)
    elif "trading" in ch:
        return build_trading_caption(title, hook_pill, creator, channel_id=ch, context_text=context_text)
    elif "viral" in ch or "trending" in ch:
        return build_viral_finds_caption(title, hook_pill, creator, context_text)
    else:
        return build_startup_caption(title, hook_pill, creator, context_text)
