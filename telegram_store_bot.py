import telebot
import json
import requests
import uuid
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Config
TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
SELLY_API_KEY = "ozJSANrGszds47fwWCo1nveeZHujSwGq_WCMs26EXZGP9m4zXssZfexZNd7TS549"
RETURN_URL = "https://breadydaceo.selly.store"
ADMIN_IDS = ["8032000000"]  # Replace with your actual admin ID
DATABASE_PATH = "db.json"

bot = telebot.TeleBot(TOKEN)

try:
    with open(DATABASE_PATH, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"users": {}, "products": {}}

def save_data():
    with open(DATABASE_PATH, "w") as f:
        json.dump(data, f, indent=2)

@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.from_user.id)
    username = message.from_user.username or "User"
    if uid not in data["users"]:
        data["users"][uid] = {"username": username, "balance": 0}
        save_data()
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🪙 Recharge", callback_data="recharge"),
        InlineKeyboardButton("📦 Listings", callback_data="listings"),
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
        InlineKeyboardButton("📜 Rules", callback_data="rules")
    )
    bot.send_message(message.chat.id, f"👋 Welcome to *Bread Sauce*, @{username}", reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "listings")
def listings(call):
    if not data["products"]:
        bot.answer_callback_query(call.id, "No products available.")
        return
    for pid, prod in data["products"].items():
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
            InlineKeyboardButton("🔙 Back", callback_data="main_menu")
        )
        msg = f"*🎁 {prod['name']}*
💸 *Price:* {prod['price']} BTC"
        bot.send_message(call.message.chat.id, msg, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy(call):
    pid = call.data.split("_", 1)[1]
    uid = str(call.from_user.id)
    user = data["users"].get(uid)
    prod = data["products"].get(pid)
    if not prod or not user:
        bot.answer_callback_query(call.id, "❌ Invalid product or user.")
        return
    if user["balance"] < float(prod["price"]):
        bot.answer_callback_query(call.id, "❌ Insufficient balance.")
        return
    user["balance"] -= float(prod["price"])
    bot.send_message(call.message.chat.id, f"✅ *Purchase Complete!*

📦 *{prod['name']}*
🧾 *Info:* `{prod.get('info', 'N/A')}`", parse_mode="Markdown")
    del data["products"][pid]
    save_data()

@bot.callback_query_handler(func=lambda c: c.data == "recharge")
def recharge(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100]:
        kb.add(
            InlineKeyboardButton(f"₿ ${amt} BTC", callback_data=f"pay_btc_{amt}"),
            InlineKeyboardButton(f"🌑 ${amt} LTC", callback_data=f"pay_ltc_{amt}")
        )
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    bot.edit_message_text("🪙 *Choose your payment method:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_"))
def generate_invoice(call):
    _, coin, amount = call.data.split("_")
    uid = str(call.from_user.id)
    payload = {
        "title": f"Recharge for {uid}",
        "white_label": True,
        "currency": "USD",
        "value": float(amount),
        "payment_gateway": coin,
        "return_url": RETURN_URL,
        "metadata": {"user_id": uid}
    }
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    r = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if r.status_code == 200:
        url = r.json().get("payment_redirection_url")
        bot.send_message(call.message.chat.id, f"🧾 *Pay Now:* [Click here to pay]({url})", parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "❌ Failed to create invoice.")

@bot.callback_query_handler(func=lambda c: c.data == "profile")
def profile(call):
    uid = str(call.from_user.id)
    user = data["users"].get(uid, {"username": "Unknown", "balance": 0})
    msg = f"👤 *User:* @{user['username']}
💰 *Balance:* {user['balance']:.8f} BTC"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "rules")
def rules(call):
    text = (
        "📜 *Store Rules:*

"
        "1. ❌ No refunds. All sales final.
"
        "2. 🧠 Know what you're buying.
"
        "3. 🛡️ Replacements only with proof.
"
        "4. 🔐 One per user.
"
        "5. 🤖 Bot activity is logged."
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "main_menu")
def back(call):
    start(call.message)

@bot.message_handler(commands=["credit"])
def credit(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return bot.reply_to(message, "❌ Not authorized.")
    try:
        _, uid, amt = message.text.split()
        user = data["users"].get(uid)
        if user:
            user["balance"] += float(amt)
            save_data()
            bot.reply_to(message, f"✅ Credited {amt} BTC to @{user['username']}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=["add"])
def add(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return bot.reply_to(message, "❌ Not authorized.")
    try:
        _, cat, name, price, info = message.text.split(" ", 4)
        pid = str(uuid.uuid4())[:8]
        data["products"][pid] = {"category": cat, "name": name, "price": float(price), "info": info}
        save_data()
        bot.reply_to(message, f"✅ Product *{name}* added.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

bot.infinity_polling()
