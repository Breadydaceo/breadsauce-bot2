
import telebot
import json
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load config
with open("bot_config.json") as config_file:
    config = json.load(config_file)

TOKEN = config["telegram_bot_token"]
ADMIN_IDS = config["admin_ids"]
CATEGORIES = config["categories"]
COINBASE_API_KEY = config["coinbase_api_key"]

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

try:
    with open(config["database"]["path"]) as db_file:
        data = json.load(db_file)
except FileNotFoundError:
    data = {"products": {}, "users": {}}

def save_data():
    with open(config["database"]["path"], "w") as db_file:
        json.dump(data, db_file, indent=2)

# Start command
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "user"
    welcome = (
        f"👋 Welcome back to Bread Sauce, @{username}

"
        "Use one of the tabs below to start shopping smart 💳

"
        "*Support:* @BreadSauceSupport

"
        "`Account → Recharge → Listings → Buy`

"
        "⚠️ *Important:* BTC recharges are updated within 10 minutes.
"
        "Your balance will be added automatically."
    )
    kb = InlineKeyboardMarkup(row_width=2)
    menu_buttons = [
        InlineKeyboardButton("💳 Gift Cards", callback_data="cat_Gift Cards"),
        InlineKeyboardButton("🧾 Fullz", callback_data="cat_Fullz"),
        InlineKeyboardButton("🧠 BIN Numbers", callback_data="cat_BIN Numbers"),
        InlineKeyboardButton("💼 CCs", callback_data="cat_CCs"),
        InlineKeyboardButton("🔮 Glass", callback_data="cat_Glass"),
        InlineKeyboardButton("💰 Recharge", callback_data="recharge"),
        InlineKeyboardButton("📂 Listings", callback_data="listings"),
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
        InlineKeyboardButton("📜 Rules", callback_data="rules")
    ]
    kb.add(*menu_buttons)
    bot.send_message(message.chat.id, welcome, reply_markup=kb, parse_mode="Markdown")

# Category listing
@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    cat_name = call.data[4:]
    msg = f"📂 *Products in {cat_name}*:

"
    found = False
    for pid, prod in data.get("products", {}).items():
        if prod["category"] == cat_name:
            msg += f"🔹 *{prod['name']}* — `{prod['price']} BTC`
ID: `{pid}`

"
            found = True
    if not found:
        msg += "🚫 Nothing in this section right now."
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

# Coinbase BTC Recharge
@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def handle_recharge(call):
    user_id = str(call.from_user.id)
    payload = {
        "name": "Bread Sauce BTC Recharge",
        "description": f"Recharge for user {user_id}",
        "local_price": {
            "amount": "10.00",
            "currency": "USD"
        },
        "pricing_type": "fixed_price",
        "metadata": {
            "user_id": user_id
        }
    }
    headers = {
        "Content-Type": "application/json",
        "X-CC-Api-Key": COINBASE_API_KEY,
        "X-CC-Version": "2018-03-22"
    }
    response = requests.post("https://api.commerce.coinbase.com/charges", json=payload, headers=headers)
    if response.status_code == 201:
        hosted_url = response.json()["data"]["hosted_url"]
        bot.send_message(call.message.chat.id, f"🪙 Click below to complete your BTC payment:

{hosted_url}")
    else:
        bot.send_message(call.message.chat.id, "⚠️ Could not create invoice. Try again later.")

# Listings
@bot.callback_query_handler(func=lambda call: call.data == "listings")
def handle_listings(call):
    categories_list = "*Available Categories:*

"
    for cat in CATEGORIES:
        categories_list += f"📁 {cat}
"
    bot.send_message(call.message.chat.id, categories_list, parse_mode="Markdown")

# Profile
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def handle_profile(call):
    uid = str(call.from_user.id)
    bal = data.get(uid, {}).get("balance", 0)
    msg = (
        f"👤 *Your Bread Sauce Profile:*

"
        f"🆔 ID: `{uid}`
"
        f"💳 Balance: `{bal} BTC`
"
        "🛍 Purchase history coming soon..."
    )
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

# Rules
@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Bread Sauce Policy:*
"
        "❌ No refunds.
"
        "🪪 Dead CCs aren't my responsibility.
"
        "🧠 If you don't know how to use the info, don't shop.
"
        "🔁 Only 1 CC replacement allowed (must prove failure on a low-end site).
"
        "🚫 No crybaby support."
    )
    bot.send_message(call.message.chat.id, rules, parse_mode="Markdown")

bot.polling()
