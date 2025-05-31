import telebot
import json
import os
import uuid
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load Config
with open("bot_config.json") as f:
    config = json.load(f)

TOKEN = config["telegram_bot_token"]
ADMIN_IDS = config["admin_ids"]
CATEGORIES = config["categories"]
DATA_FILE = config["database"]["path"]

bot = telebot.TeleBot(TOKEN)

# Load or initialize data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE) as f:
        data = json.load(f)
else:
    data = {"products": {}, "users": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💳 Gift Cards", callback_data="cat_Gift Cards"),
        InlineKeyboardButton("🧾 Fullz", callback_data="cat_Fullz"),
        InlineKeyboardButton("🧠 BIN Numbers", callback_data="cat_BIN Numbers"),
        InlineKeyboardButton("💼 CCs", callback_data="cat_CCs"),
        InlineKeyboardButton("🔮 Glass", callback_data="cat_Glass"),
        InlineKeyboardButton("💰 Recharge", callback_data="recharge"),
        InlineKeyboardButton("📂 Listings", callback_data="listings"),
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
        InlineKeyboardButton("📜 Rules", callback_data="rules")
    ]
    kb.add(*buttons)
    return kb

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id not in data["users"]:
        data["users"][user_id] = {"balance": 0}
        save_data()
    bot.send_message(message.chat.id,
        f"👋 Welcome to Bread Sauce, @{message.from_user.username or 'user'}\n\n"
        "Use one of the tabs below to start shopping smart 💳\n\n"
        "*Support:* @BreadSauceSupport\n\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *Important:* BTC/LTC recharges are manual. You'll be credited once payment is confirmed.\n\n"
        "🤖 *Note:* Suspicious behavior may trigger bot protection.",
        parse_mode="Markdown", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    cat_name = call.data[4:]
    kb = InlineKeyboardMarkup(row_width=2)
    msg = f"📂 *Products in {cat_name}*:\n\n"
    found = False
    for pid, prod in data["products"].items():
        if prod["category"] == cat_name:
            msg += f"🛒 *{prod['name']}*\nPRICE : ${prod['price']} Purchase 🛒\n\n"
            kb.add(InlineKeyboardButton("🛒 Purchase", callback_data=f"preview_{pid}"))
            found = True
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_menu"))
    if not found:
        bot.edit_message_text("🚫 Nothing in this section right now.",
                              call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("preview_"))
def preview_product(call):
    pid = call.data[8:]
    product = data["products"].get(pid)
    if not product:
        bot.answer_callback_query(call.id, "Product not found.")
        return
    msg = f"Info: {product['name']}\nPRICE : ${product['price']}\n{product['description']}"
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
        InlineKeyboardButton("🚫 Cancel", callback_data=f"cat_{product['category']}")
    )
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                          reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_product(call):
    user_id = str(call.from_user.id)
    pid = call.data[4:]
    user = data["users"].get(user_id, {"balance": 0})
    product = data["products"].get(pid)
    if not product:
        bot.answer_callback_query(call.id, "Product not found.")
        return
    if user["balance"] < product["price"]:
        bot.answer_callback_query(call.id, "❌ Not enough balance.")
        return
    user["balance"] -= product["price"]
    del data["products"][pid]
    save_data()
    bot.edit_message_text(
        f"✅ *Purchase successful!*\n\n*{product['name']}*\n\n`{product['content']}`",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_options(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"pay_{amt}"))
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_menu"))
    bot.edit_message_text("🪙 Choose a recharge amount:", call.message.chat.id,
                          call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def show_wallet(call):
    amt = call.data[4:]
    bot.edit_message_text(
        f"🪙 Send BTC or LTC for ${amt} to:\n\n*your-crypto-wallet-address-here*",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def handle_listings(call):
    msg = "*Available Categories:*\n\n"
    for cat in CATEGORIES:
        msg += f"📁 {cat}\n"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back_menu"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def handle_profile(call):
    uid = str(call.from_user.id)
    bal = data.get("users", {}).get(uid, {}).get("balance", 0)
    msg = (
        f"👤 *Your Bread Sauce Profile:*\n\n"
        f"🆔 ID: `{uid}`\n"
        f"💳 Balance: `${bal}`\n"
        "🛍 Purchase history coming soon..."
    )
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back_menu"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    msg = (
        "📜 *Bread Sauce Policy:*\n"
        "❌ No refunds.\n"
        "🪪 Dead CCs aren't my responsibility.\n"
        "🧠 If you don't know how to use the info, don't shop.\n"
        "🔁 Only 1 CC replacement allowed (must prove failure on a low-end site).\n"
        "🚫 No crybaby support."
    )
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back_menu"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "back_menu")
def back_to_menu(call):
    bot.edit_message_text("🏠 Returning to main menu...", call.message.chat.id,
                          call.message.message_id, reply_markup=main_menu())

@bot.message_handler(commands=["add"])
def admin_add(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        parts = message.text.split(" ", 4)
        _, name, category, price, content = parts
        pid = str(uuid.uuid4())[:8]
        data["products"][pid] = {
            "name": name, "category": category, "price": float(price),
            "content": content, "description": "GOOD FOR APPLE , BEST BUY & GOOGLE PAY"
        }
        save_data()
        bot.reply_to(message, f"✅ Added product {name} (${price}) to {category}.")
    except:
        bot.reply_to(message, "Usage: /add name category price content")

@bot.message_handler(commands=["remove"])
def admin_remove(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    pid = message.text.split(" ", 1)[1]
    if pid in data["products"]:
        del data["products"][pid]
        save_data()
        bot.reply_to(message, "✅ Product removed.")
    else:
        bot.reply_to(message, "⚠️ Product ID not found.")

@bot.message_handler(commands=["credit"])
def admin_credit(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, username, amount = message.text.split()
        for uid, user in data["users"].items():
            if username.lower() in user.get("username", "").lower():
                user["balance"] += float(amount)
                save_data()
                bot.reply_to(message, f"✅ Credited {amount} to {username}.")
                return
        bot.reply_to(message, "⚠️ User not found.")
    except:
        bot.reply_to(message, "Usage: /credit username amount")

bot.polling()