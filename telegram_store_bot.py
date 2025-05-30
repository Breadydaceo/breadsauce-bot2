import telebot
import json
import requests
import uuid
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot Configuration
TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
ADMIN_IDS = ["123456789"]  # Replace with your Telegram ID(s)
SELLY_API_KEY = "ozJSANrGszds47fwWCo1nveeZHujSwGq_WCMs26EXZGP9m4zXssZfexZNd7TS549"
RETURN_URL = "https://breadydaceo.selly.store"
DATABASE_PATH = "bot_db.json"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# Load or initialize data
try:
    with open(DATABASE_PATH) as db:
        data = json.load(db)
except FileNotFoundError:
    data = {"products": {}, "users": {}}

def save_data():
    with open(DATABASE_PATH, "w") as db:
        json.dump(data, db, indent=2)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "User"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎁 Gift Cards", callback_data="cat_Gift Cards"),
        InlineKeyboardButton("🪪 Fullz", callback_data="cat_Fullz"),
        InlineKeyboardButton("🧠 BIN Numbers", callback_data="cat_BIN Numbers"),
        InlineKeyboardButton("💳 CCs", callback_data="cat_CCs"),
        InlineKeyboardButton("🔮 Glass", callback_data="cat_Glass"),
        InlineKeyboardButton("💰 Recharge", callback_data="recharge"),
        InlineKeyboardButton("📂 Listings", callback_data="listings"),
        InlineKeyboardButton("🧑 Profile", callback_data="profile"),
        InlineKeyboardButton("📜 Rules", callback_data="rules")
    )
    bot.send_message(message.chat.id, f"👋 Welcome to *Bread Sauce*, @{username}", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_products(call):
    category = call.data.split("_", 1)[1]
    for pid, product in data["products"].items():
        if product["category"].lower() == category.lower():
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
                InlineKeyboardButton("🚫 Cancel", callback_data="cancel"),
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            )
            msg = f"*🎯 {product['name']}*
💸 *Price:* {product['price']} BTC"
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb)
            return
    bot.answer_callback_query(call.id, "No products found in this category.", show_alert=True)

# --- Product Listings Handler ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_products(call):
    category = call.data.split("_", 1)[1]
    products = [p for p in data["products"].items() if p[1]["category"].lower() == category.lower()]
    if not products:
        bot.answer_callback_query(call.id, "❌ No products available.", show_alert=True)
        return
    for pid, prod in products:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
            InlineKeyboardButton("🔙 Back", callback_data="main_menu")
        )
        text = f"*🎁 {prod['name']}*
💵 *Price:* {prod['price']} BTC"
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="Markdown")

# --- Recharge Menu Handler ---
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

# --- Invoice Creation via Selly ---
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
        "return_url": "https://breadydaceo.selly.store",
        "metadata": {"user_id": user_id}
    }
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if response.status_code == 200:
        url = response.json().get("payment_redirection_url")
        bot.edit_message_text(f"💳 *Payment Invoice Generated:*
🔗 {url}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "❌ Could not generate invoice.", show_alert=True)

# --- Show User Profile ---
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user_id = str(call.from_user.id)
    user = data["users"].get(user_id, {"username": "Unknown", "balance": 0})
    balance = user["balance"]
    text = f"🧤 *Your Profile*
👤 *User:* @{user['username']}
💰 *Balance:* {balance:.8f} BTC"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# --- Admin: Credit Balance ---
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

# --- Admin: Add Product ---
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
        bot.reply_to(message, f"❌ Error: {e}\nUsage: /add <category> <name> <price> <info>")

bot.infinity_polling()