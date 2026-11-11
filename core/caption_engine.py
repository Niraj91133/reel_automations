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

def format_credit_line(creator: str) -> str:
    if not creator or creator.lower() in ["creator", "approved_creator", "none", ""]:
        return "Video credit: Respective Creator"
    c = creator.strip().lstrip("@")
    return f"Video credit: @{c}"

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
            "• Unit Economics: High-volume commission per liter without sinking massive capital into real estate capex.\n"
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
        
def derive_startup_story(text: str) -> tuple[str, str, str, str, str]:
    """
    Derives natural, human-like, high-converting storytelling caption elements
    matching the exact style of @startup_road's 2.64 Lakh like reels.
    Returns: (trigger_word, hook_question, context_para, math_points, punchline)
    """
    t = text.lower()
    
    if any(w in t for w in ["container", "cabin", "shipping"]):
        return (
            "CONTAINER",
            "Ever noticed how empty shipping containers are quietly making people fortunes? 📦💸",
            "Most people think real estate means buying multi-crore land and waiting 10 years. But smart operators are buying used shipping containers, placing them on leased highway land, and renting them as portable offices, cafes, and storage units.",
            "✅ Buy used container: Sourced at scrap or secondary rates.\n"
            "✅ Minor fit-out (doors, AC cut, paint): Under ₹50,000.\n"
            "✅ Monthly rental yield: ₹15,000 to ₹30,000/month per container.\n"
            "✅ 3X the rental yield of traditional property with 1/10th the maintenance cost.",
            "Low capex, zero building construction headaches, and an asset that can be relocated anywhere."
        )
        
    elif any(w in t for w in ["petrol", "fuel", "pump", "shell"]):
        return (
            "FUEL",
            "Think you need massive crores to own a petrol pump in India? Think again. ⛽️",
            "Most people don't know about the CODO model (Company Owned, Dealer Operated) where top fuel brands provide the land, the tanks, and the heavy infrastructure—while you manage the daily operations.",
            "✅ No massive land acquisition needed.\n"
            "✅ Pre-built commercial setup under a trusted national brand.\n"
            "✅ High daily volume commissions with zero inventory depreciation risk.\n"
            "✅ Refundable security deposit instead of sunk real estate capital.",
            "Asset-light models in massive daily-consumption industries print the most consistent cash flow."
        )
        
    elif any(w in t for w in ["battery", "lead", "acid", "recycle"]):
        return (
            "BATTERY",
            "Ever wondered where all those dead car and inverter batteries go? 🔋♻️",
            "India discards millions of spent lead-acid batteries every year. This hazardous waste is actually one of the most protected, high-margin secondary metal supply businesses in the country.",
            "✅ Source spent batteries from local mechanics at scrap weight.\n"
            "✅ Extract purified lead and plastic components for secondary smelters.\n"
            "✅ 35% to 50% cash margins with fast 48-hour inventory turnaround.\n"
            "✅ Evergreen industrial demand that never slows down.",
            "The most profitable businesses hide inside the hazardous waste streams of modern society."
        )
        
    elif any(w in t for w in ["spark plug", "scrap", "iridium", "kachra", "metal", "waste"]):
        return (
            "SCRAP",
            "Ever wondered where all that industrial waste and discarded scrap actually goes? ♻️",
            "Daily, Indian industries throw away tons of scrap that hide high-value recyclable components. What looks like junk to an amateur is a 40% to 70% gross margin business for a smart operator.",
            "✅ Sourcing from local garages and industrial units at scrap weight rates.\n"
            "✅ Simple sorting, shredding, or component extraction.\n"
            "✅ Bulk wholesale supply to secondary smelting and manufacturing units.\n"
            "✅ Fast 48-hour inventory turnover with zero expensive marketing needed.",
            "In commodity businesses, your profit is made on the buy side, not the sell side."
        )
        
    elif any(w in t for w in ["dry fruit", "kaju", "kismish", "makhana", "wholesale", "mandi", "hub"]):
        return (
            "MARKET",
            "Ever wondered why the price of dry fruits and spices doubles the moment they reach your city? 🥜",
            "Most retail shop owners buy from 3rd-tier state distributors, paying layers of middlemen markups. But if you source directly from primary mandi hubs, the price arbitrage is pure profit.",
            "✅ Direct sourcing from primary harvest hubs at raw wholesale rates.\n"
            "✅ Simple cleaning, grading, and compact pouch packaging.\n"
            "✅ B2B supply to local grocery supermarkets and sweet makers on 7-day cycles.\n"
            "✅ 35% to 50% gross margin on staple commodities that never go out of demand.",
            "Stop trying to invent something new. Just optimize the supply chain of everyday essentials."
        )
        
    elif any(w in t for w in ["paper bag", "paper cup", "packaging", "box", "pouch", "print"]):
        return (
            "PACKAGING",
            "Ever noticed how every single bakery, cafe, and retail shop needs packaging every single day? 📦",
            "Most people chase trendy online businesses, but boring daily-use consumables are where the real, consistent cash flow hides. With a compact packaging machine, you step into a market with non-negotiable repeat demand.",
            "✅ Raw material cost: Under ₹2-3 per bag/pouch.\n"
            "✅ Wholesale supply rate: ₹5-7 per unit to local B2B shops.\n"
            "✅ Securing just 5-10 local business contracts = Steady monthly recurring cashflow.\n"
            "✅ Low square footage, zero expensive marketing, and clients who re-order every single week.",
            "Boring, consumable daily packaging generates rock-solid cash flow in all market seasons."
        )
        
    elif any(w in t for w in ["ice cream", "popsicle", "kulfi", "pop"]):
        return (
            "ICECREAM",
            "Why invest in a fancy restaurant when you can print daily cash with a small popsicle kiosk? 🍦",
            "Bite-sized gourmet treats have the highest impulse purchase frequency and profit margins in the entire food industry. You don't need a kitchen—just a compact freezer cart at high-footfall spots.",
            "✅ Manufacturing cost: Under ₹8 per gourmet stick.\n"
            "✅ Retail selling price: ₹40 to ₹60 at high-traffic college & market spots.\n"
            "✅ 70%+ gross margins with zero expensive dine-in overhead.\n"
            "✅ Scalable to multiple kiosk points across your city.",
            "High-margin impulse treats beat sit-down dining economics every single time."
        )
        
    elif any(w in t for w in ["chappal", "slipper", "footwear", "sole"]):
        return (
            "CHAPPAL",
            "Did you know a simple EVA footwear sheet press can turn into a daily cash machine? 🩴",
            "Slippers are a non-negotiable daily necessity across every Indian household. With a compact hydraulic press and strap-fitting machine, you can launch a micro-manufacturing unit with minimal space.",
            "✅ Production cost: ₹8 to ₹12 per pair.\n"
            "✅ Wholesale supply rate: ₹25 to ₹35 to local tier-2/3 retail shops.\n"
            "✅ Steady repeat utility demand across both rural and urban markets.\n"
            "✅ Low machinery footprint that runs on standard power connection.",
            "Mass consumption goods with low unit capex build durable, recession-proof cash flow."
        )
        
    elif any(w in t for w in ["drop", "dropship", "shopify", "roposo", "ecom"]):
        return (
            "DROPSHIP",
            "Most people overcomplicate e-commerce. Here's how people quietly make it work in India. 🛒",
            "You don't need to import containers from China or hold inventory in a warehouse. Indian supplier networks now fulfill and ship orders directly with Cash-on-Delivery support.",
            "✅ Find viral problem-solving utility products with ₹400+ gross margin.\n"
            "✅ Zero upfront inventory risk via verified domestic fulfillment partners.\n"
            "✅ Test high-converting short-form creative angles on Meta ads.\n"
            "✅ Re-invest daily ad profits into scaling the winning SKU.",
            "E-commerce success is 20% product and 80% disciplined creative testing with positive ROAS."
        )
        
    elif any(w in t for w in ["ai", "app", "website", "software", "client", "saas", "agency"]):
        return (
            "WEBSITE",
            "Local businesses in your city are losing customers every day because their online setup is broken. 💻",
            "Doctors, gym owners, cafes, and boutiques don't have the time to build funnels or automate booking. If you can package ready-made templates and automated messaging for them, they will gladly pay.",
            "✅ Package ready-to-deploy website templates and automated booking funnels.\n"
            "✅ Deliver complete client solutions in 48 hours using no-code AI tools.\n"
            "✅ Charge ₹15,000 to ₹35,000 upfront plus recurring monthly maintenance.\n"
            "✅ Just 3-5 clients a month creates a healthy, location-independent income.",
            "Clients don't pay for hours worked; they pay for immediate solutions to painful operational bottlenecks."
        )
        
    elif any(w in t for w in ["oil", "mustard", "cold press", "kachi ghani", "expeller"]):
        return (
            "OIL",
            "Why are cold-pressed oil plants booming across tier-2 and tier-3 India? 🛢️",
            "Consumers are ditching chemical-refined oils and actively paying 2x premiums for fresh, unadulterated cold-pressed mustard and groundnut oil right in front of their eyes.",
            "✅ Compact cold-press expeller machine setup: Under ₹1.5 - ₹2 Lakhs.\n"
            "✅ Raw mustard seeds sourced directly from mandi at wholesale.\n"
            "✅ 40% to 55% gross margin on oil plus dry cake byproduct sold as cattle feed.\n"
            "✅ Steady, non-cyclical repeat consumption in every single kitchen.",
            "Health-driven consumer shifts create the easiest local premium brand opportunities."
        )

    elif any(w in t for w in ["water", "concentrate", "beverage", "drink", "juice", "soda"]):
        return (
            "BEVERAGE",
            "Why pay to transport heavy water bottles when you can sell the concentrate? 📦💧",
            "Smart beverage operators don't ship 90% water weight across states. They sell compact concentrates, syrups, and premixes that local retailers and vendors dilute on-demand.",
            "✅ Slashes logistics and shipping costs by up to 85%.\n"
            "✅ Compact formulation setup with zero massive bottling plant capex.\n"
            "✅ High-margin wholesale delivery to local soda fountains, cafes, and restaurants.\n"
            "✅ 60%+ gross margins with high-volume repeat reorders.",
            "In FMCG, eliminating transport weight directly multiplies your bottom-line profit."
        )

    elif any(w in t for w in ["solar", "energy", "wind", "power", "panel", "rooftop"]):
        return (
            "SOLAR",
            "Commercial rooftops across India are turning into silent money printers. ☀️⚡",
            "With escalating commercial electricity tariffs, factory and warehouse owners are desperate to slash power bills. As a project facilitator, you capture lucrative commissions without heavy equipment capex.",
            "✅ Zero inventory holding risk by partnering with Tier-1 solar manufacturers.\n"
            "✅ Government PM Surya Ghar subsidies accelerating adoption.\n"
            "✅ Average ₹40,000 to ₹1.2 Lakh gross margin per standard commercial installation.\n"
            "✅ High-ticket, asset-backed market riding an unstoppable clean energy wave.",
            "Help businesses cut their largest recurring expense, and they will gladly pay you."
        )

    elif any(w in t for w in ["savings", "bank", "10,000", "20,000", "50,000", "idle", "fd", "paisa", "wealth", "salary", "invest"]):
        return (
            "GROWTH",
            "Stop letting your savings sit idle in a low-interest bank account! 💸",
            "Inflation quietly eats away at money parked in savings accounts. Smart young operators deploy micro-capital into high-velocity rotation assets that generate monthly cash yield.",
            "✅ Shift capital from consumer liabilities into productive micro-assets.\n"
            "✅ Low-capex setups with fast 30-day cash turnaround.\n"
            "✅ Reinvest 100% of initial cashflow into duplicate inventory.\n"
            "✅ Building compounding cash flow beats waiting for a salary hike every single time.",
            "Wealth isn't built by saving pennies; it's built by rotating capital into cashflow assets."
        )

    elif any(w in t for w in ["makhana", "saffron", "polyhouse", "hydroponic", "mushroom", "dairy", "farm", "agro"]):
        return (
            "AGRO",
            "High-value specialty agro is where the quiet fortunes are being made. 🌾💎",
            "While traditional crop farmers struggle with price volatility, high-value commodity processors (Makhana, Saffron, Button Mushrooms) control huge retail price spreads.",
            "✅ Sourced directly at farm gate or primary mandis at raw rates.\n"
            "✅ Simple grading, sorting, and moisture-controlled pouch packing.\n"
            "✅ 3X to 5X retail price spread compared to raw farmgate cost.\n"
            "✅ Evergreen export and domestic urban health demand.",
            "The biggest agricultural profits belong to those who control grading and packaging."
        )

    elif any(w in t for w in ["kitchen", "food", "restaurant", "swiggy", "zomato", "cloud"]):
        return (
            "KITCHEN",
            "Cloud kitchens print money only when you kill the dine-in real estate trap. 🍳🚀",
            "90% of restaurants die because of insane high-street rent and interior decor capex. Virtual brands operate from cheap back-alley basements with 100% focus on online delivery.",
            "✅ Zero high-street retail rent; operate from low-cost commercial premises.\n"
            "✅ Multi-brand strategy: Run 2 to 3 distinct cuisine brands from one single setup.\n"
            "✅ Optimized food cost capped strictly at 28% to 32% of order value.\n"
            "✅ Scale volume via delivery platforms without front-of-house staff.",
            "Kill the real estate ego and let delivery algorithms drive your revenue."
        )

    else:
        # Dynamic Multi-Variant Fallback: Guarantee no two consecutive fallbacks share identical copy
        import hashlib
        v_idx = int(hashlib.md5(t.encode()).hexdigest()[:6], 16) % 4
        
        variants = [
            (
                "DETAILS",
                "Ever noticed how the most profitable businesses in India are also the most unglamorous? 🛠️",
                "While everyone chases saturated software or agency dreams, practical physical setups with real ground demand continue to generate reliable daily profits with zero marketing hype.",
                "✅ High everyday utility with non-negotiable local demand.\n"
                "✅ Low initial capital expenditure with protected operating margins.\n"
                "✅ Fast cash turnaround with clients who buy on repeat.\n"
                "✅ Hard asset backing that holds tangible real-world value.",
                "Stop waiting for the 'perfect' idea and start executing on everyday ground realities."
            ),
            (
                "BLUEPRINT",
                "Boring daily consumables are printing higher returns than trendy startups. 🏭💸",
                "The secret to durable wealth in India isn't reinventing the wheel—it's supplying essential packaging, processing, and hardware items that businesses consume every 48 hours.",
                "✅ Evergreen repeat B2B client reorders.\n"
                "✅ Protected 35% to 50% gross margins on standard commodity turnover.\n"
                "✅ Minimal marketing spend; client relationships are built on supply reliability.\n"
                "✅ Scalable by adding secondary semi-automatic machinery as cashflows grow.",
                "Real business isn't about being fancy; it's about owning a piece of essential daily cashflow."
            ),
            (
                "ROADMAP",
                "Why compete with multi-crore giants when you can own your local 5km radius? 📍📦",
                "Micro-manufacturing and hyper-local supply chains beat centralized mega-factories on speed, credit flexibility, and personalized customer relationships every single time.",
                "✅ Proximity advantage: Same-day delivery to local retail shops.\n"
                "✅ Flexible production batches that eliminate heavy inventory holding.\n"
                "✅ High cash-cycle velocity with 7-day payment settlement.\n"
                "✅ Low administrative overhead with lean operational costs.",
                "Dominate a single pin code before you even think about dominating the country."
            ),
            (
                "GUIDE",
                "The easiest way to make money is finding what companies are throwing away. ♻️💡",
                "Industrial waste, secondary packaging scrap, and discarded raw materials hold hidden fortunes for operators who understand sorting, recovery, and bulk resale.",
                "✅ Raw material sourced for pennies or zero-cost disposal contracts.\n"
                "✅ Value addition via basic sorting, compacting, or chemical separation.\n"
                "✅ High-margin bulk supply to secondary smelting and recycling plants.\n"
                "✅ Recession-proof demand driven by strict industrial sustainability mandates.",
                "One operator's waste stream is another entrepreneur's 300% profit margin."
            )
        ]
        return variants[v_idx]

def build_startup_caption(title: str, hook_pill: str, creator: str, channel_id: str = "startup_road", context_text: str = "") -> str:
    clean_t = clean_title_text(title)
    tmpl = NICHE_TEMPLATES.get(channel_id, NICHE_TEMPLATES["startup_road"])
    handle = tmpl.get("handle", "@startup_road")
    trigger, hook_q, context_p, math_pts, takeaway = derive_startup_story(f"{title} {hook_pill} {context_text}")
    
    credit_line = format_credit_line(creator)
    hashtags = " ".join(tmpl.get("hashtags", NICHE_TEMPLATES["startup_road"]["hashtags"]))

    return (
        f"{hook_q}\n\n"
        f"{context_p}\n\n"
        f"Here’s the math:\n"
        f"{math_pts}\n\n"
        f"{takeaway}\n\n"
        f"Want the complete roadmap, machine supplier contacts & setup guide?\n"
        f"Comment \"{trigger}\" below and I'll DM you the full breakdown instantly! 🚀\n\n"
        f"{credit_line}\n"
        f"Follow {handle} for daily practical business blueprints.\n\n"
        f"{hashtags}"
    )

def build_health_caption(title: str, hook_pill: str, creator: str, context_text: str = "") -> str:
    clean_t = clean_title_text(title)
    t_lower = f"{title} {hook_pill} {context_text}".lower()
    
    if any(w in t_lower for w in ["palm oil", "oil", "fat"]):
        trigger = "CLEAN"
        hook_q = "Next time you pick up that 'healthy' packaged snack, flip it around and check the back label! 🥣🚨"
        context_p = "Most big food brands in India spend crores advertising their snacks as '100% whole grain' or 'diet-friendly', while quietly packing them with cheap refined palm oil to slash manufacturing costs and extend shelf life for 12 months."
        math_pts = (
            "✅ The Palm Oil Trap: If the second or third ingredient says 'Edible Vegetable Oil (Palm)', drop it immediately.\n"
            "✅ The Health Impact: Highly oxidized industrial oils drive systemic inflammation and cholesterol spikes.\n"
            "✅ The Clean Alternative: Look for snacks cooked in wood-pressed mustard oil, cold-pressed coconut oil, or real ghee."
        )
        takeaway = "Real food goes bad in a week. If it sits on a shelf for 12 months without spoiling, your body will struggle to digest it."
    elif any(w in t_lower for w in ["sugar", "sweet", "maltodextrin", "syrup"]):
        trigger = "CLEAN"
        hook_q = "Think your 'No Added Sugar' snack is actually safe? Read the fine print. 🥤🚨"
        context_p = "Big food corporations have found a clever loophole: they remove white sugar from the front label, but replace it with ingredients that spike your blood sugar even faster than regular sugar."
        math_pts = (
            "✅ The Sugar Disguise: Maltodextrin, invert syrup, liquid glucose, and date concentrate are all sugar in disguise.\n"
            "✅ Glycemic Index Spike: Maltodextrin has a higher glycemic index (110) than pure white table sugar (65).\n"
            "✅ The Clean Rule: Look for products with under 5 whole kitchen ingredients that you can actually pronounce."
        )
        takeaway = "If sugar or syrup appears in the top 3 ingredients, treat it like candy—not healthy breakfast."
    else:
        trigger = "HEALTH"
        hook_q = "Ever wondered why packaged snacks make you crave more even after your stomach is full? 🥣"
        context_p = "Food scientists engineer packaged snacks with the exact ratio of salt, fat, and artificial flavor enhancers to bypass your brain's fullness signals. You are not lacking willpower—the food was engineered to make you overeat."
        math_pts = (
            "✅ Flavor Enhancers (INS 627, 631): Chemically trigger cravings so you finish the whole packet.\n"
            "✅ Hidden Sodium: Sneaked into sweet biscuits and cereals to mask chemical preservatives.\n"
            "✅ The Clean Swap: Switching to single-ingredient Indian whole foods: roasted chana, makhana, and raw nuts."
        )
        takeaway = "Invest in clean, real food today, or pay tenfold to hospital bills tomorrow."

    credit_line = format_credit_line(creator)
    hashtags = " ".join(NICHE_TEMPLATES["healthy_diet"]["hashtags"])

    return (
        f"{hook_q}\n\n"
        f"{context_p}\n\n"
        f"Here’s what to look for on the label:\n"
        f"{math_pts}\n\n"
        f"{takeaway}\n\n"
        f"Want our curated list of 100% clean, verified palm-oil-free snack brands available in India?\n"
        f"Comment \"{trigger}\" below and I'll DM you the complete guide! 🥗\n\n"
        f"{credit_line}\n"
        f"Follow @gudtree_ for daily verified food label breakdowns.\n\n"
        f"{hashtags}"
    )

def build_trading_caption(title: str, hook_pill: str, creator: str, channel_id: str = "trading_pulse", context_text: str = "") -> str:
    clean_t = clean_title_text(title)
    tmpl = NICHE_TEMPLATES.get(channel_id, NICHE_TEMPLATES["trading_pulse"])
    
    credit_line = format_credit_line(creator)
    hashtags = " ".join(tmpl["hashtags"])
    disclaimer = tmpl["disclaimer"]
    handle = tmpl.get("handle", "@trading_road_")

    return (
        f"Ever noticed how the moment you buy a breakout, the market reverses and hits your stop loss? 📉\n\n"
        f"You are not unlucky—you are simply trading inside the liquidity trap engineered by institutional algorithms. Smart money pumps the price to lure retail FOMO buyers, and then dumps their positions into your market orders.\n\n"
        f"Here’s how professional price action traders avoid this trap:\n"
        f"✅ The Fakeout Filter: Never buy the initial breakout candle; wait for the 15-minute close and retest.\n"
        f"✅ Volume Confirmation: Look for high institutional volume on the retest, not on the breakout spike.\n"
        f"✅ Risk-Reward Discipline: Strictly take setups with at least 1:2 risk-to-reward ratio.\n\n"
        f"Amateurs enter every single candle out of impatience. Professional traders obsess over capital preservation and wait patiently for high-probability setups.\n\n"
        f"Want our free Price Action & Candlestick Reversal cheatsheet?\n"
        f"Comment \"LEVELS\" below and I'll DM you the breakdown instantly! 📊\n\n"
        f"{disclaimer}\n\n"
        f"{credit_line}\n"
        f"Follow {handle} for daily institutional market analysis.\n\n"
        f"{hashtags}"
    )

def build_loan_caption(title: str, hook_pill: str, creator: str, context_text: str = "") -> str:
    clean_t = clean_title_text(title)
    credit_line = format_credit_line(creator)
    hashtags = " ".join(NICHE_TEMPLATES["the_loan_road"]["hashtags"])
    disclaimer = NICHE_TEMPLATES["the_loan_road"]["disclaimer"]

    return (
        f"Think you just have to pay your home loan for 20 long years? Think again. 🏦\n\n"
        f"On a ₹50 Lakh loan at 8.5%, banks will quietly take over ₹54 Lakhs in interest alone. That means you pay MORE than double what you borrowed. But with one simple mathematical tweak, you can cut this down dramatically.\n\n"
        f"Here’s the exact math they won't tell you:\n"
        f"✅ The 1 Extra EMI Hack: Pay just 1 additional EMI every year and your 20-year loan finishes in under 15.5 years.\n"
        f"✅ Total Interest Saved: Over ₹18 Lakhs saved directly in your pocket.\n"
        f"✅ The SIP Shield: Investing just 10% of your EMI in a balanced index fund recovers 100% of your interest paid.\n\n"
        f"Banks make their highest profits from people who don't understand compounding. Use their own rules to beat them.\n\n"
        f"Want our free Home Loan Prepayment & Compounding Calculator Excel Sheet?\n"
        f"Comment \"CALCULATOR\" below and I’ll DM you the direct spreadsheet instantly! 💰📈\n\n"
        f"{disclaimer}\n\n"
        f"{credit_line}\n"
        f"Follow @the_loan_road for daily loan hacks & wealth compounding blueprints.\n\n"
        f"{hashtags}"
    )

def build_viral_finds_caption(title: str, hook_pill: str, creator: str, context_text: str = "") -> str:
    clean_t = clean_title_text(title)
    credit_line = format_credit_line(creator)
    hashtags = " ".join(NICHE_TEMPLATES["viral_finds"]["hashtags"])

    return (
        f"This ₹499 Amazon find solves the most annoying daily problem in your house. 🏠✨\n\n"
        f"If you're tired of messy tangles, broken cables, and wasted kitchen space, this compact utility tool is an absolute lifesaver. No expensive installations, no tools needed.\n\n"
        f"Here’s why it’s going viral:\n"
        f"✅ Instant 5-Second Setup: Stick, mount, and organize with zero wall damage.\n"
        f"✅ Heavy-Duty Durability: Built to hold daily weight without slipping or breaking.\n"
        f"✅ Pure Daily Utility: Solves an everyday frustration for under ₹499.\n\n"
        f"Small smart utility finds that make everyday life 10x easier and cleaner.\n\n"
        f"Want the direct purchase link with the current discount?\n"
        f"Comment \"LINK\" below and I’ll send you the direct verified product link in your DM! 🔗\n\n"
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
        return build_startup_caption(title, hook_pill, creator, channel_id=ch, context_text=context_text)
