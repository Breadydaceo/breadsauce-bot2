import telebot
import json
import requests
import uuid
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
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💳 Gift Cards", callback_data="cat_Gift Cards"),
        InlineKeyboardButton("🧾 Fullz", callback_data="cat_Fullz"),
        InlineKeyboardButton("🧠 BIN Numbers", callback_data="cat_BIN Numbers"),
        InlineKeyboardButton("💴 CCs", callback_data="cat_CCs"),
        InlineKeyboardButton("🔮 Glass", callback_data="cat_Glass"),
        InlineKeyboardButton("💰 Recharge", callback_data="recharge"),
        InlineKeyboardButton("📂 Listings", callback_data="listings"),
        InlineKeyboardButton("🧑‍💻 Profile", callback_data="profile"),
        InlineKeyboardButton("📜 Rules", callback_data="rules")
    )
    bot.send_message(message.chat.id, f"👋 Welcome to *Bread Sauce*, @{username}", reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_products(call):
    category = call.data.split("_", 1)[1]
    for pid, prod in data["products"].items():
        if prod["category"].lower() == category.lower():
            kb = InlineKeyboardMarkup(row_width=3)
            kb.add(
                InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
                InlineKeyboardButton("🚫 Cancel", callback_data="cancel"),
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            )
            text = f"*🛍 {prod['name']}*
💸 *Price:* {prod['price']} BTC"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return
    bot.answer_callback_query(call.id, "No products available.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def main_menu(call):
    send_welcome(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_back(call):
    send_welcome(call.message)

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
        f"✅ *Purchase Complete!*

📦 *{product['name']}*
💳 *Info:* `{product_info}`",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user_id = str(call.from_user.id)
    user = data["users"].get(user_id, {"username": "Unknown", "balance": 0})
    balance = user["balance"]
    text = f"🧑‍💻 *Your Profile*

🧾 *User:* @{user['username']}
💰 *Balance:* {balance:.8f} BTC"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_menu(call):
    kb = InlineKeyboardMarkup(row_width=2)
    amounts = [25, 50, 100, 150, 200, 300, 500]
    for amt in amounts:
        kb.add(
            InlineKeyboardButton(f"₿ ${amt} BTC", callback_data=f"recharge_btc_{amt}"),
            InlineKeyboardButton(f"🌑 ${amt} LTC", callback_data=f"recharge_ltc_{amt}")
        )
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    bot.edit_message_text("🪙 *Choose your recharge method and amount:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def create_invoice(call):
    _, coin, amount = call.data.split("_")
    user_id = str(call.from_user.id)
    payload = {
        "title": f"Recharge for {user_id}",
        "white_label": True,
        "currency": "USD",
        "value": float(amount),
        "payment_gateway": coin,
        "metadata": {"user_id": user_id}
    }
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if response.status_code == 200:
        url = response.json().get("payment_redirection_url")
        bot.edit_message_text(
            f"💸 *Payment Invoice Generated:*

🔗 {url}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(call.id, "❌ Could not generate invoice.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules_msg = (
        "📜 *Store Rules:*

"
        "1. ❌ No refunds. All sales final.
"
        "2. 🧠 Know what you’re buying.
"
        "3. 🛡️ Replacements only with proof (low-end fails).
"
        "4. 🔁 One replacement per customer.
"
        "5. 🤖 Bot detects suspicious activity.

"
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
        message += f"*{cat} Products:*
"
        for prod in items:
            message += f"🛍️ {prod['name']}
💸 Price: {prod['price']} BTC

"
    bot.edit_message_text(message or "📦 No listings available.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=["credit"])
def credit_user_balance(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    try:
        _, user_id, amount = message.text.split()
        user = data["users"].get(user_id)
        if not user:
            bot.reply_to(message, f"❌ No user found with ID {user_id}")
            return
        amount = float(amount)
        user["balance"] += amount
        save_data()
        bot.reply_to(message, f"✅ Credited {amount:.8f} BTC to @{user['username']}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}
Usage: /credit <user_id> <amount>")

@bot.message_handler(commands=["add"])
def admin_add_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    try:
        _, category, name, price, info = message.text.split(" ", 4)
        product_id = str(uuid.uuid4())[:8]
        data["products"][product_id] = {
            "category": category,
            "name": name,
            "price": float(price),
            "info": info
        }
        save_data()
        bot.reply_to(message, f"✅ Product '{name}' added under '{category}' for {price} BTC.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}
Usage: /add <category> <name> <price> <info>")

bot.polling()
