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
SELLY_API_KEY = config["selly_api_key"]
DATABASE_PATH = config["database"]["path"]

bot = telebot.TeleBot(TOKEN)
try:
    with open(DATABASE_PATH) as db_file:
        data = json.load(db_file)
except FileNotFoundError:
    data = {"products": {}, "users": {}}

def save_data():
    with open(DATABASE_PATH, "w") as db_file:
        json.dump(data, db_file, indent=2)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "User"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()

    welcome = (
        f"👋 Welcome to *Bread Sauce*, @{username}\n"
        "💳 Start shopping smart.\n\n"
        "📞 Support: @BreadSauceSupport\n"
        "Account → Recharge → Listings → Buy\n"
        "⚠️ BTC recharges update within 10 mins.\n"
        "🤖 Suspicious behavior may trigger bot lock."
    )
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💳 Gift Cards", callback_data="cat_Gift Cards"),
        InlineKeyboardButton("🪪 Fullz", callback_data="cat_Fullz"),
        InlineKeyboardButton("🧠 BIN Numbers", callback_data="cat_BIN Numbers"),
        InlineKeyboardButton("💼 CCs", callback_data="cat_CCs"),
        InlineKeyboardButton("🔮 Glass", callback_data="cat_Glass"),
        InlineKeyboardButton("💰 Recharge", callback_data="recharge"),
        InlineKeyboardButton("📂 Listings", callback_data="listings"),
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
        InlineKeyboardButton("📜 Rules", callback_data="rules")
    ]
    kb.add(*buttons)
    bot.send_message(message.chat.id, welcome, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_products(call):
    category = call.data.split("_", 1)[1]
    product_list = []
    for pid, prod in data["products"].items():
        if prod["category"].lower() == category.lower():
            kb = InlineKeyboardMarkup(row_width=3)
            kb.add(
                InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
                InlineKeyboardButton("🚫 Cancel", callback_data="cancel"),
                InlineKeyboardButton("⬅️ Back", callback_data="listings")
            )
            text = f"*🛍 {prod['name']}*\n💸 *Price:* {prod['price']} BTC"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return
    bot.answer_callback_query(call.id, "No products available.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_back(call):
    send_welcome(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_product(call):
    user_id = str(call.from_user.id)
    pid = call.data.split("_", 1)[1]
    if pid not in data["products"]:
        bot.answer_callback_query(call.id, "❌ Product not found.", show_alert=True)
        return
    product = data["products"][pid]
    balance = data["users"].get(user_id, {}).get("balance", 0)
    if balance < float(product["price"]):
        bot.answer_callback_query(call.id, "❌ Insufficient balance.", show_alert=True)
        return
    data["users"][user_id]["balance"] -= float(product["price"])
    product_info = product.get("info", "No info available.")
    del data["products"][pid]
    save_data()
    bot.edit_message_text(
        f"✅ *Purchase Complete!*\n\n📦 *{product['name']}*\n💳 *Info:* `{product_info}`",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user_id = str(call.from_user.id)
    user = data["users"].get(user_id, {"username": "Unknown", "balance": 0})
    balance = user["balance"]
    text = f"👤 *Your Profile*\n\n🪪 *User:* @{user['username']}\n💰 *Balance:* {balance:.8f} BTC"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_menu(call):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("₿ Bitcoin", callback_data="recharge_btc"),
        InlineKeyboardButton("🪙 Litecoin", callback_data="recharge_ltc"),
        InlineKeyboardButton("🔙 Back", callback_data="main_menu")
    )
    bot.edit_message_text("💳 *Choose your payment method:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def generate_invoice(call):
    coin = call.data.split("_", 1)[1]
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": "Recharge",
        "white_label": True,
        "currency": "USD",
        "value": "50.00",
        "payment_gateway": coin,
        "return_url": "https://yoursite.com/return",
        "metadata": {
            "custom_id": call.from_user.id
        }
    }
    response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if response.status_code == 200:
        invoice = response.json()
        invoice_url = invoice.get("payment_redirection_url", "No URL returned.")
        bot.edit_message_text(f"💸 *Pay using this link:*\n{invoice_url}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "❌ Could not generate invoice.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules_msg = (
        "📜 *Store Rules:*\n\n"
        "1. ❌ No refunds. All sales final.\n"
        "2. 🧠 Know what you’re buying.\n"
        "3. 🛡️ Replacements only with proof (low-end fails).\n"
        "4. 🔁 One replacement per customer.\n"
        "5. 🤖 Suspicious behavior may trigger lock.\n\n"
        "📞 *Support:* @BreadSauceSupport"
    )
    bot.edit_message_text(rules_msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    summaries = {}
    for pid, prod in data["products"].items():
        summaries.setdefault(prod["category"], []).append(prod)
    message = ""
    for cat, items in summaries.items():
        message += f"*{cat} Products:*\n"
        for prod in items:
            message += f"🛍️ {prod['name']}\n💸 Price: {prod['price']} BTC\n\n"
    bot.edit_message_text(message or "📦 No listings available.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=["credit"])
def credit_user(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ Unauthorized.")
        return
    try:
        _, user_id, amount = message.text.split()
        user = data["users"].get(user_id)
        if not user:
            bot.reply_to(message, "❌ User not found.")
            return
        user["balance"] += float(amount)
        save_data()
        bot.reply_to(message, f"✅ Credited {amount} BTC to {user['username']}")
    except:
        bot.reply_to(message, "⚠️ Usage: /credit <user_id> <amount>")

@bot.message_handler(commands=["add"])
def add_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ Unauthorized.")
        return
    try:
        _, category, name, price, info = message.text.split("|", 4)
        pid = str(len(data["products"]) + 1)
        data["products"][pid] = {
            "category": category.strip(),
            "name": name.strip(),
            "price": price.strip(),
            "info": info.strip()
        }
        save_data()
        bot.reply_to(message, f"✅ Added product {name.strip()}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

bot.polling()
