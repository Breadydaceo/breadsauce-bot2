import telebot
import json
import requests
import uuid
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configuration
TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
SELLY_API_KEY = "ozJSANrGszds47fwWCo1nveeZHujSwGq_WCMs26EXZGP9m4zXssZfexZNd7TS549"
RETURN_URL = "https://breadydaceo.selly.store"
DATABASE_PATH = "bot_data.json"
ADMIN_IDS = ["your_admin_id_here"]

bot = telebot.TeleBot(TOKEN)

# Load or initialize data
try:
    with open(DATABASE_PATH) as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"products": {}, "users": {}}

def save_data():
    with open(DATABASE_PATH, "w") as f:
        json.dump(data, f, indent=2)

@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "User"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💳 Gift Cards", callback_data="cat_Gift Cards"),
        InlineKeyboardButton("🪪 Fullz", callback_data="cat_Fullz"),
        InlineKeyboardButton("🧠 BIN Numbers", callback_data="cat_BIN Numbers"),
        InlineKeyboardButton("💴 CCs", callback_data="cat_CCs"),
        InlineKeyboardButton("🔮 Glass", callback_data="cat_Glass"),
        InlineKeyboardButton("💰 Recharge", callback_data="recharge"),
        InlineKeyboardButton("📂 Listings", callback_data="listings"),
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
        InlineKeyboardButton("📜 Rules", callback_data="rules")
    )
    bot.send_message(message.chat.id, f"👋 Welcome to *Bread Sauce*, @{username}", reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    category = call.data.split("_", 1)[1]
    found = False
    for pid, product in data["products"].items():
        if product["category"].lower() == category.lower():
            found = True
            kb = InlineKeyboardMarkup(row_width=3)
            kb.add(
                InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
                InlineKeyboardButton("🚫 Cancel", callback_data="cancel"),
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            )
            msg = f"*📍 {product['name']}*
💵 *Price:* {product['price']} BTC"
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            break
    if not found:
        bot.answer_callback_query(call.id, "No products available in this category.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "main_menu" or call.data == "cancel")
def go_back(call):
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy(call):
    user_id = str(call.from_user.id)
    pid = call.data.split("_", 1)[1]
    if pid not in data["products"]:
        bot.answer_callback_query(call.id, "❌ Product not found.", show_alert=True)
        return
    product = data["products"][pid]
    user = data["users"].get(user_id)
    if user["balance"] < float(product["price"]):
        bot.answer_callback_query(call.id, "❌ Insufficient balance.", show_alert=True)
        return
    data["users"][user_id]["balance"] -= float(product["price"])
    product_info = product.get("info", "No details provided.")
    del data["products"][pid]
    save_data()
    msg = f"✅ *Purchase Complete!*

📦 *{product['name']}*
💳 *Info:* `{product_info}`"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user = data["users"].get(str(call.from_user.id), {"username": "Unknown", "balance": 0})
    text = f"👤 *Your Profile*

🪪 *User:* @{user['username']}
💰 *Balance:* {user['balance']:.8f} BTC"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def show_recharge_options(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amount in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"💵 ${amount}", callback_data=f"recharge_{amount}"))
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
    bot.edit_message_text("💰 *Choose Recharge Amount:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def create_invoice(call):
    amount = call.data.split("_")[1]
    user_id = str(call.from_user.id)
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": f"Recharge {amount} for {user_id}",
        "currency": "USD",
        "value": amount,
        "return_url": RETURN_URL,
        "payment_gateway": "crypto",
        "white_label": True,
        "metadata": {"user_id": user_id}
    }
    response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if response.status_code == 200:
        invoice_url = response.json().get("payment_redirection_url", "https://google.com")
        bot.edit_message_text(f"🧾 *Pay Here:*
{invoice_url}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "❌ Failed to generate invoice.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Store Rules:*

"
        "1. ❌ No refunds
"
        "2. 🧠 Know what you’re buying
"
        "3. 🚨 One replacement w/ proof
"
        "4. 🔒 No leaking info
"
        "5. 🤖 Suspicious activity auto-detected

"
        "📞 Support: @BreadSauceSupport"
    )
    bot.edit_message_text(rules, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    listings = {}
    for pid, prod in data["products"].items():
        listings.setdefault(prod["category"], []).append(prod)
    msg = ""
    for cat, items in listings.items():
        msg += f"*{cat}*
"
        for item in items:
            msg += f"📍 {item['name']} - 💵 {item['price']} BTC
"
        msg += "
"
    bot.edit_message_text(msg or "📦 No listings currently.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=["credit"])
def credit_balance(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized.")
        return
    try:
        _, user_id, amount = message.text.split()
        amount = float(amount)
        data["users"].setdefault(user_id, {"username": "Unknown", "balance": 0})
        data["users"][user_id]["balance"] += amount
        save_data()
        bot.reply_to(message, f"✅ Credited {amount} BTC to user {user_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}
Usage: /credit <user_id> <amount>")

@bot.message_handler(commands=["add"])
def add_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized.")
        return
    try:
        _, category, name, price, info = message.text.split(" ", 4)
        pid = str(uuid.uuid4())[:8]
        data["products"][pid] = {
            "category": category,
            "name": name,
            "price": float(price),
            "info": info
        }
        save_data()
        bot.reply_to(message, f"✅ Added {name} to {category}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}
Usage: /add <category> <name> <price> <info>")

bot.polling()