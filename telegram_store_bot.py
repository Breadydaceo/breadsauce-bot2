import telebot
import json
import requests
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load config
with open("bot_config.json") as config_file:
    config = json.load(config_file)

TOKEN = config["telegram_bot_token"]
ADMIN_IDS = config["admin_ids"]
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


def build_main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💳 Gift Cards", callback_data="cat_Gift Cards"),
        InlineKeyboardButton("🪪 Fullz", callback_data="cat_Fullz"),
        InlineKeyboardButton("🧠 BIN Numbers", callback_data="cat_BIN Numbers"),
        InlineKeyboardButton("💼 CCs", callback_data="cat_CCs"),
        InlineKeyboardButton("🔮 Glass", callback_data="cat_Glass"),
        InlineKeyboardButton("💰 Recharge", callback_data="recharge_menu"),
        InlineKeyboardButton("📂 Listings", callback_data="listings"),
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
        InlineKeyboardButton("📜 Rules", callback_data="rules")
    ]
    kb.add(*buttons)
    return kb


@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "User"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()

    welcome_msg = (
        f"👋 Welcome back to *Bread Sauce*, @{username}\n\n"
        "Tap below to start shopping smart 💳\n\n"
        "📞 *Support:* @BreadSauceSupport\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *BTC recharges are updated within 10 minutes.*\n"
        "Your balance will be credited manually.\n\n"
        "🤖 *Note:* Suspicious behavior may trigger bot lock."
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=build_main_menu(), parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category_products(call):
    category = call.data.split("_", 1)[1]
    user_id = str(call.from_user.id)

    for pid, prod in data["products"].items():
        if prod["category"].lower() == category.lower():
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(
                InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
                InlineKeyboardButton("🚫 Cancel", callback_data="cancel"),
                InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
            )
            text = f"*🛍 {prod['name']}*\n💸 *Price:* {prod['price']} BTC"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return
    bot.answer_callback_query(call.id, "No products available.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == "cancel" or call.data == "back_to_menu")
def go_back_to_menu(call):
    bot.edit_message_text("🔙 Back to menu:", call.message.chat.id, call.message.message_id, reply_markup=build_main_menu(), parse_mode="Markdown")


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
    del data["products"][pid]  # Auto-expire
    save_data()

    bot.edit_message_text(
        f"✅ *Purchase Complete!*\n\n📦 *{product['name']}*\n💳 *Info:* `{product_info}`",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )


@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user_id = str(call.from_user.id)
    user = data["users"].get(user_id, {"username": "Unknown", "balance": 0})
    balance = user["balance"]
    text = f"👤 *Your Profile*\n\n🪪 *User:* @{user['username']}\n💰 *Balance:* {balance:.8f} BTC"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "recharge_menu")
def recharge_menu(call):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("₿ $25 BTC", callback_data="recharge_btc_25"),
        InlineKeyboardButton("₿ $50 BTC", callback_data="recharge_btc_50"),
        InlineKeyboardButton("₿ $100 BTC", callback_data="recharge_btc_100"),
        InlineKeyboardButton("🪙 $25 LTC", callback_data="recharge_ltc_25"),
        InlineKeyboardButton("🪙 $50 LTC", callback_data="recharge_ltc_50"),
        InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
    )
    bot.edit_message_text("💳 *Choose your recharge method and amount:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def generate_invoice(call):
    parts = call.data.split("_")
    coin = parts[1]
    value = int(parts[2])

    payload = {
        "title": "Bread Sauce Recharge",
        "currency": "USD",
        "value": value,
        "payment_gateway": coin,
        "white_label": True
    }

    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)

    if response.status_code == 200:
        invoice = response.json()
        invoice_url = invoice.get("payment_redirection_url", "No URL returned.")
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_menu"))
        bot.edit_message_text(
            f"💸 *Invoice Generated:* Send the payment to complete your recharge.\n\n🔗 {invoice_url}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=kb
        )
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

    bot.edit_message_text(message or "📦 No listings available.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")


bot.polling()