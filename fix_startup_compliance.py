import json, glob, os
import sys

sys.path.insert(0, 'reel_automations-main')
from core.compliance_guard import is_reel_compliant

safe_titles = [
    ("BUSINESS BREAKDOWN: THE SECRET TO SCALING", "STARTUP STRATEGY", "Practical insights on building a sustainable business. What is your take on this model?"),
    ("THE LOCAL MANUFACTURING BLUEPRINT", "BUSINESS INSIGHT", "Every entrepreneur should understand supply chains and production. Share your thoughts!"),
    ("OFFLINE VS ONLINE: THE PROFITABILITY TRUTH", "STARTUP SECRET", "Analyzing realistic unit economics and overheads. How would you approach this?"),
    ("HIDDEN HIGH-MARGIN B2B NICHES", "SMART BUSINESS", "Why unsexy businesses often generate the strongest cash flow. Worth exploring!"),
    ("ESSENTIAL RULES FOR MODERN ENTREPRENEURS", "STARTUP LESSON", "Execution beats ideation every single time. Save this for reference.")
]

q = 'C:/reel_cache/startup_road/tomorrow_reels'
meta_files = sorted(glob.glob(os.path.join(q, 'ready_*.json')))

for i, mf in enumerate(meta_files):
    if i < len(safe_titles):
        title, hook, caption = safe_titles[i]
        with open(mf, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['title'] = title
        data['hook_pill'] = hook
        data['caption'] = caption + "\n\n#entrepreneurship #businessgrowth #startuptips #businessstrategy"
        with open(mf, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        is_safe, reason = is_reel_compliant(title, hook, data['caption'])
        print(f"Updated {os.path.basename(mf)} -> Safe={is_safe} ({title})")

