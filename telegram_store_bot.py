import telebot
import json
import requests
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load config
with open("bot_config.json") as config_file:
    config = json.load(config_file)

TOKEN = config["telegram_bot_token"]
ADMIN_IDS = config["admin_ids"]
CATEGORIES = config["categories"]
SELLY_API_KEY = config["selly_api_key"]
DATABASE_PATH = config["database"]["path"]

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# Load or initialize database
if os.path.exists(DATABASE_PATH):
    with open(DATABASE_PATH) as db_file:
        data = json.load(db_file)
else:
    data = {"products": {}, "users": {}}

def save_data():
    with open(DATABASE_PATH, "w") as db_file:
        json.dump(data, db_file, indent=2)

# Welcome Message
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "User"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()

    welcome_text = (
        f"👋 Welcome back to *Bread Sauce*, @{username}\n"
        "Use the menu below to explore and purchase.\n\n"
        "📞 *Support:* @BreadSauceSupport\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ BTC Recharges will be credited manually.\n"
        "🤖 Suspicious behavior may trigger bot lock."
    )

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💳 Gift Cards", callback_data="cat_Gift Cards"),
        InlineKeyboardButton("🪪 Fullz", callback_data="cat_Fullz"),
        InlineKeyboardButton("🧠 BIN Numbers", callback_data="cat_BIN Numbers"),
        InlineKeyboardButton("💼 CCs", callback_data="cat_CCs"),
        InlineKeyboardButton("🔮 Glass", callback_data="cat_Glass"),
        InlineKeyboardButton("💰 Recharge", callback_data="recharge"),
        InlineKeyboardButton("📂 Listings", callback_data="listings"),
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
        InlineKeyboardButton("📜 Rules", callback_data="rules")
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=kb, parse_mode="Markdown")

# Show product category
@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_products(call):
    category = call.data.split("_", 1)[1]
    products = [p for p in data["products"].values() if p["category"] == category]
    if not products:
        bot.answer_callback_query(call.id, f"No {category} listed.", show_alert=True)
        return

    for prod in products:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{prod['id']}"),
            InlineKeyboardButton("🚫 Cancel", callback_data="cancel"),
            InlineKeyboardButton("🔙 Back", callback_data="main")
        )
        prod_text = f"🛍️ *{prod['name']}*\n💸 *Price:* {prod['price']} BTC"
        bot.send_message(call.message.chat.id, prod_text, reply_markup=kb, parse_mode="Markdown")

# Buy Product
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_product(call):
    user_id = str(call.from_user.id)
    product_id = call.data.split("_", 1)[1]
    user = data["users"].get(user_id)
    product = data["products"].get(product_id)

    if not product:
        bot.answer_callback_query(call.id, "❌ Product not found.", show_alert=True)
        return

    if user["balance"] < float(product["price"]):
        bot.answer_callback_query(call.id, "❌ Insufficient balance.", show_alert=True)
        return

    user["balance"] -= float(product["price"])
    info = product.get("info", "No info available.")

    del data["products"][product_id]
    save_data()

    bot.edit_message_text(
        f"✅ *Purchase Complete!*\n\n📦 *{product['name']}*\n💳 *Info:* `{info}`",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# Recharge Menu
@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def show_recharge_options(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"recharge_{amt}"))
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="main"))
    bot.edit_message_text("💳 *Select amount to recharge:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# Generate Invoice
@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def generate_invoice(call):
    amount = call.data.split("_")[1]
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": f"Bread Sauce Recharge - ${amount}",
        "white_label": True,
        "currency": "USD",
        "value": float(amount),
        "payment_gateway": "bitcoin"
    }
    response = requests.post("https://api.selly.io/v2/payment_requests", headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        url = data.get("payment_redirection_url", "N/A")
        bot.edit_message_text(f"🧾 *Pay using this BTC invoice link:*\n\n🔗 {url}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        print("Invoice error:", response.text)
        bot.answer_callback_query(call.id, "❌ Failed to create invoice.", show_alert=True)

# Profile
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user_id = str(call.from_user.id)
    user = data["users"].get(user_id, {"username": "Unknown", "balance": 0})
    bot.edit_message_text(
        f"👤 *User:* @{user['username']}\n💰 *Balance:* {user['balance']:.8f} BTC",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# Rules
@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules_text = (
        "📜 *Store Rules:*\n\n"
        "1. ❌ No refunds. All sales final.\n"
        "2. 🧠 Know what you’re buying.\n"
        "3. 🛡️ Replacements only with proof (low-end fails).\n"
        "4. 🔁 One replacement per customer.\n"
        "5. 🤖 Bot protection is active.\n\n"
        "📞 *Support:* @BreadSauceSupport"
    )
    bot.edit_message_text(rules_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# Listings
@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    listings = {}
    for p in data["products"].values():
        listings.setdefault(p["category"], []).append(p)
    
    if not listings:
        bot.edit_message_text("📦 No listings available.", call.message.chat.id, call.message.message_id)
        return

    text = ""
    for cat, items in listings.items():
        text += f"*{cat}:*\n"
        for item in items:
            text += f"🛍 {item['name']} - {item['price']} BTC\n"
        text += "\n"

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# Cancel or Back
@bot.callback_query_handler(func=lambda call: call.data in ["cancel", "main"])
def cancel_back(call):
    send_welcome(call.message)

bot.polling()