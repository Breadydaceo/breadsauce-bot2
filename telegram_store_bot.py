
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
SELLY_API_KEY = config["nowpayments_api_key"]
DATABASE_PATH = config["database"]["path"]

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

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
        f"👋 Welcome back to *Bread Sauce*, @{username}\n"
        "Tap below to start shopping smart 💳\n\n"
        "📞 *Support:* @BreadSauceSupport\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *BTC recharges are updated within 10 minutes.*\n"
        "Your balance will be credited manually.\n\n"
        "🤖 *Note:* Suspicious behavior may trigger bot lock."
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
    user_id = str(call.from_user.id)
    products_found = False

    for pid, prod in data["products"].items():
        if prod["category"].lower() == category.lower():
            products_found = True
            kb = InlineKeyboardMarkup(row_width=3)
            kb.add(
                InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
                InlineKeyboardButton("🚫 Cancel", callback_data="cancel"),
                InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
            )
            text = f"*🛍 {prod['name']}*\n💸 *Price:* {prod['price']} BTC"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return
    if not products_found:
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
    kb = InlineKeyboardMarkup(row_width=3)
    amounts = [25, 50, 100, 150, 200, 300, 500]
    buttons = [InlineKeyboardButton(f"₿ ${amt} BTC", callback_data=f"recharge_btc_{amt}") for amt in amounts]
    kb.add(*buttons)
    kb.add(InlineKeyboardButton("⬅️ Back", callback_data="main_menu"))
    bot.edit_message_text("🧾 *Choose your recharge method and amount:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_btc_"))
def create_invoice(call):
    try:
        amount = float(call.data.split("_")[-1])
        payload = {
            "title": "Bread Sauce Recharge",
            "white_label": True,
            "currency": "USD",
            "value": amount,
            "payment_gateway": "bitcoin"
        }
        headers = {
            "Authorization": f"Bearer {SELLY_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
        invoice = response.json()
        url = invoice.get("payment_redirection_url")
        if url:
            bot.edit_message_text(
                f"💸 *Invoice Created:*\n\nSend payment using the link below.\n\n🔗 {url}",
                call.message.chat.id, call.message.message_id, parse_mode="Markdown"
            )
        else:
            raise Exception("No invoice URL returned")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Could not generate invoice.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    text = (
        "📜 *Store Rules:*\n\n"
        "1. ❌ No refunds. All sales final.\n"
        "2. 🧠 Know what you’re buying.\n"
        "3. 🛡 Replacements only with proof (low-end fails).\n"
        "4. 🔁 One replacement per customer.\n"
        "5. 🤖 Bot detects suspicious activity.\n\n"
        "📞 *Support:* @BreadSauceSupport"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    summaries = {}
    for pid, prod in data["products"].items():
        summaries.setdefault(prod["category"], []).append(prod)

    message = ""
    for cat, items in summaries.items():
        message += f"*{cat} Products:*\n"
        for prod in items:
            message += f"🛍 {prod['name']}\n💸 Price: {prod['price']} BTC\n\n"

    bot.edit_message_text(message or "📦 No listings available.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# Admin-only: manually credit user
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
        bot.reply_to(message, f"❌ Usage: /credit <user_id> <amount>")

# Admin-only: add product
@bot.message_handler(commands=["addproduct"])
def add_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to add products.")
        return
    try:
        _, category, name, price, info = message.text.split("|")
        pid = str(len(data["products"]) + 1)
        data["products"][pid] = {
            "category": category.strip(),
            "name": name.strip(),
            "price": float(price.strip()),
            "info": info.strip()
        }
        save_data()
        bot.reply_to(message, f"✅ Product '{name.strip()}' added.")
    except Exception:
        bot.reply_to(message, "❌ Format: /addproduct | category | name | price | info")

# Admin-only: remove product
@bot.message_handler(commands=["removeproduct"])
def remove_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to remove products.")
        return
    try:
        _, pid = message.text.split()
        if pid in data["products"]:
            del data["products"][pid]
            save_data()
            bot.reply_to(message, f"✅ Product ID {pid} removed.")
        else:
            bot.reply_to(message, f"❌ Product ID {pid} not found.")
    except Exception:
        bot.reply_to(message, "❌ Usage: /removeproduct <product_id>")

bot.polling()
