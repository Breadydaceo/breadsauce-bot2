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
bot.remove_webhook()

try:
    with open(DATABASE_PATH) as db_file:
        data = json.load(db_file)
except FileNotFoundError:
    data = {"products": {}, "users": {}}


def save_data():
    with open(DATABASE_PATH, "w") as db_file:
        json.dump(data, db_file, indent=2)


def get_main_menu(username):
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
    return welcome, kb


@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "User"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()

    welcome_text, menu_kb = get_main_menu(username)
    bot.send_message(message.chat.id, welcome_text, reply_markup=menu_kb, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_back(call):
    user_id = str(call.from_user.id)
    username = data["users"].get(user_id, {}).get("username", "User")
    welcome_text, menu_kb = get_main_menu(username)
    bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, reply_markup=menu_kb, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_products(call):
    category = call.data.split("_", 1)[1]

    for pid, prod in data["products"].items():
        if prod["category"].lower() == category.lower():
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
                InlineKeyboardButton("🚫 Cancel", callback_data="cancel")
            )
            text = f"*🛍 {prod['name']}*\n💸 *Price:* {prod['price']} BTC"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return
    bot.answer_callback_query(call.id, "No products available.", show_alert=True)


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
        InlineKeyboardButton("🔙 Back", callback_data="cancel")
    )
    bot.edit_message_text("💳 *Choose your payment method:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def generate_invoice(call):
    coin = call.data.split("_", 1)[1]

    payload = {
        "title": "Bread Sauce Recharge",
        "white_label": True,
        "currency": "USD",
        "value": 50.00,
        "payment_gateway": coin
    }

    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)

    if response.status_code == 200:
        invoice = response.json()
        url = invoice.get("payment_redirection_url", "No URL")
        bot.edit_message_text(
            f"💸 *Payment Invoice Generated:*\nSend the payment to complete recharge.\n\n🔗 {url}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(call.id, "❌ Failed to generate invoice.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules_msg = (
        "📜 *Store Rules:*\n\n"
        "1. ❌ No refunds. All sales final.\n"
        "2. 🧠 Know what you’re buying.\n"
        "3. 🛡️ Replacements only with proof (low-end fails).\n"
        "4. 🔁 One replacement per customer.\n"
        "5. 🤖 Bot detects suspicious activity.\n\n"
        "📞 *Support:* @BreadSauceSupport"
    )
    bot.edit_message_text(rules_msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    summaries = {}
    for prod in data["products"].values():
        summaries.setdefault(prod["category"], []).append(prod)

    message = ""
    for cat, items in summaries.items():
        message += f"*{cat} Products:*\n"
        for prod in items:
            message += f"🛍️ {prod['name']}\n💸 Price: {prod['price']} BTC\n\n"

    if not message:
        message = "📦 No listings available."
    bot.edit_message_text(message, call.message.chat.id, call.message.message_id, parse_mode="Markdown")


bot.polling()