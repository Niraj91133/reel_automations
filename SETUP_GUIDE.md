# 🚀 4-Account Instagram Automation: Setup & Operations Guide

Yeh architecture **100% Zero-Contamination** pe design ki gayi hai. Kisi bhi account ka token, database, ya temporary file doosre account se clash nahi karegi.

---

## 📁 1. Config Files (Yahan apni Keys & Tokens Daalo)

Sabhi configuration files `configs/` folder ke andar hain:

| Account / Niche | Config File | Niche Topic | Default Style |
| :--- | :--- | :--- | :--- |
| **1. Startup Road** | `configs/startup_road.json` | Business, Startups & Hustle | Red & Black Podcast Badge |
| **2. Healthy Diet & Snacks** | `configs/healthy_diet.json` | Packaged snacks, clean diet, ingredients | Emerald Green Clean Badge |
| **3. Trading Pulse** | `configs/trading_pulse.json` | Price action, charts, risk management | Cyan & Dark Navy Market Badge |
| **4. Viral Finds** | `configs/viral_finds.json` | Smart gadgets, Amazon finds, problem-solvers | Purple & Neon Star E-Com Badge |

### 🔑 Keys Kaise Daalna Hai:
Har `.json` file me `credentials` section milega:
```json
"credentials": {
  "gemini_api_key": "APNA_GEMINI_API_KEY_YAHAN_PASTE_KARO",
  "instagram_account_id": "APNA_IG_BUSINESS_ACCOUNT_ID",
  "page_access_token": "APNA_META_PAGE_ACCESS_TOKEN",
  "telegram_bot_token": "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A",
  "telegram_chat_id": "APNA_TELEGRAM_CHANNEL_YA_CHAT_ID"
}
```

---

## ⚡ 2. 4 Gemini API Keys (100% Free Setup)

1. [Google AI Studio](https://aistudio.google.com/) pe jao.
2. Tum 4 alag-alag Google accounts se login karke **4 Free Gemini API Keys** generate kar sakte ho.
3. Har key ko uske respective JSON file (`startup_road.json`, `healthy_diet.json`, `trading_pulse.json`, `viral_finds.json`) me daal do.
4. **Iska fayda:** Har account ka 1500 Requests/day quota alag rahega aur ₹0 kharch hoga!

---

## 📢 3. Telegram Channels Setup (Approval & Previews)

1. Telegram me 4 alag-alag Private Channels ya Groups banao:
   * `#Startup-Road-Queue`
   * `#Healthy-Bites-Queue`
   * `#Trading-Pulse-Queue`
   * `#Viral-Finds-Queue`
2. Apne Bot (`@startup_road_bot` ya Master Bot) ko charon channels me **Admin** banao.
3. Channel ka Chat ID (e.g. `-100xxxxxxxxxx`) respective config file me `telegram_chat_id` me paste kar do.
   *(Agar channel nahi banana chahte, toh apna personal Chat ID `711598335` hi rehne do — bot tag ke sath bhejega)*.

---

## 📱 4. One Facebook Account -> 4 Instagram Accounts (Meta Setup)

Meta Business Suite me:
1. Apne Facebook account me 4 Pages banao (Startup Road, Healthy Bites, Trading Pulse, Viral Finds).
2. Har Page ko uske respective **Instagram Professional/Creator** account se connect karo.
3. [Graph API Explorer](https://developers.facebook.com/tools/explorer/) se ya System User se Page Access Token generate karo with permissions:
   * `instagram_basic`
   * `instagram_content_publish`
   * `pages_show_list`
   * `pages_read_engagement`
4. Meta ki 25-posts/day limit har Instagram account ke liye **completely separate** hai!

---

## 🎬 5. Run Kaise Karein?

### Option A: Master Controller (Telegram Bot + 24/7 Scheduler)
Double-click karo:
```text
START_MASTER_CONTROLLER.bat
```
* Ye background me har 30 minute pe agle account ka reel schedule karega.
* Telegram pe aakar commands de sakte ho:
  * `/status` -> Sabhi 4 accounts ka live status & today's post count dekho
  * `/run startup_road 1` -> Startup Road ka 1 reel banao aur post karo
  * `/run healthy_diet 1` -> Healthy Diet ka 1 reel banao
  * `/run trading_pulse 1` -> Trading ka 1 reel banao
  * `/run viral_finds 1` -> Viral Finds ka 1 reel banao
  * `/run all` -> Charon accounts ka 1-1 reel banao
  * `/schedule off` / `/schedule on` -> Scheduler ko pause ya start karo

### Option B: Single Channel Run (CLI ya Batch)
Double-click karo:
```text
RUN_SINGLE_CHANNEL.bat
```
Prompt aayega `1, 2, 3 ya 4` select karne ka, aur wo particular channel turant process ho jayega!

---

## 🛡️ 6. Zero-Contamination Guarantees

* **File Storage:** Har channel ka apna isolated folder hai: `workspaces/startup_road/`, `workspaces/healthy_diet/`, etc.
* **UUID Rendering:** Har video render hone ke liye unique UUID use karti hai (`final_f8a91c.mp4`), isliye simultaneous rendering me kabhi file overwrite nahi hoti.
* **Database:** Har channel ki apni isolated SQLite database hai with WAL mode (`databases/startup_road_history.db`, etc.), kabhi database locked error nahi aayega.
* **Crash Proof:** Agar koi ek channel fail hota hai, toh doosre 3 channels pe 0.1% bhi asar nahi padega.
