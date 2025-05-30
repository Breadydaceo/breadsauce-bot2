import telebot
import json
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load configuration
with open("bot_config.json") as f:
    config = json.load(f)

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


def main_menu_markup():
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
    return kb


@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "User"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()

    welcome = (
        f"👋 Welcome back to *Bread Sauce*, @{username}\n\n"
        "Tap below to start shopping smart 💳\n\n"
        "📞 *Support:* @BreadSauceSupport\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *BTC recharges are updated within 10 minutes.*\n"
        "Your balance will be credited manually.\n\n"
        "🤖 *Note:* Suspicious behavior may trigger bot lock."
    )
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu_markup(), parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_products(call):
    category = call.data.split("_", 1)[1]
    matched = [p for p in data["products"].items() if p[1]["category"].lower() == category.lower()]
    if not matched:
        bot.answer_callback_query(call.id, "No products available.", show_alert=True)
        return

    for pid, prod in matched:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
            InlineKeyboardButton("🔙 Back", callback_data="back_main")
        )
        text = f"*🛍 {prod['name']}*\n💸 *Price:* {prod['price']} BTC"
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def go_back_main(call):
    bot.edit_message_text("⬅️ Returning to main menu...", call.message.chat.id, call.message.message_id, reply_markup=main_menu_markup(), parse_mode="Markdown")


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
    info = product.get("info", "No info available.")
    bot.send_message(call.message.chat.id, f"✅ *Purchase Complete!*\n\n📦 *{product['name']}*\n💳 *Info:* `{info}`", parse_mode="Markdown")

    # Remove from inventory
    del data["products"][pid]
    save_data()


@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user_id = str(call.from_user.id)
    user = data["users"].get(user_id, {"username": "Unknown", "balance": 0})
    text = f"👤 *Your Profile*\n\n🪪 *User:* @{user['username']}\n💰 *Balance:* {user['balance']:.8f} BTC"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")


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

    msg = ""
    for cat, items in summaries.items():
        msg += f"*{cat} Products:*\n"
        for prod in items:
            msg += f"🛍️ {prod['name']}\n💸 Price: {prod['price']} BTC\n\n"

    bot.edit_message_text(msg or "📦 No listings available.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_menu(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amount in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amount}", callback_data=f"recharge_{amount}"))
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_main"))
    bot.edit_message_text("💳 *Select amount to recharge:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def generate_invoice(call):
    user_id = str(call.from_user.id)
    amount = float(call.data.split("_")[1])

    payload = {
        "title": "Bread Sauce Recharge",
        "currency": "USD",
        "value": amount,
        "white_label": True
    }

    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if r.status_code == 200:
        link = r.json().get("payment_redirection_url", "Unavailable")
        bot.send_message(call.message.chat.id, f"💸 *Send BTC here:*\n\n{link}", parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "❌ Failed to create invoice.", show_alert=True)


# === Admin-Only Command Example ===
@bot.message_handler(commands=["credit"])
def credit_user(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "⛔️ Unauthorized")
        return

    try:
        _, uid, amount = message.text.split()
        amount = float(amount)
        data["users"].setdefault(uid, {"username": "Unknown", "balance": 0})
        data["users"][uid]["balance"] += amount
        save_data()
        bot.reply_to(message, f"✅ Credited {amount} BTC to user {uid}")
    except Exception:
        bot.reply_to(message, "❌ Usage: /credit USER_ID AMOUNT")


bot.polling()