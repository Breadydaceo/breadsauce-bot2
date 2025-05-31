import telebot
import json
import uuid
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load config
with open("bot_config.json") as config_file:
    config = json.load(config_file)

TOKEN = config["telegram_bot_token"]
ADMIN_IDS = config["admin_ids"]
CATEGORIES = config["categories"]

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# Load or create data file
try:
    with open(config["database"]["path"]) as db_file:
        data = json.load(db_file)
except FileNotFoundError:
    data = {"products": {}, "users": {}}

def save_data():
    with open(config["database"]["path"], "w") as db_file:
        json.dump(data, db_file, indent=2)

# Start command
@bot.message_handler(commands=["start"])
def send_welcome(message):
    username = message.from_user.username or "user"
    welcome = (
        f"👋 Welcome to Bread Sauce, @{username}\n\n"
        "Use the menu below to start shopping smart 💳\n\n"
        "*Support:* @BreadSauceSupport\n\n"
        "Account → Recharge → Listings → Buy\n\n"
        "⚠️ *Important:* BTC/LTC recharges are updated within 10 minutes.\n"
        "🤖 *Note:* Suspicious behavior may trigger bot protection."
    )
    kb = main_menu()
    bot.send_message(message.chat.id, welcome, reply_markup=kb, parse_mode="Markdown")

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

# Show category
@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    cat = call.data[4:]
    msg = f"📂 *{cat} Products*\n\n"
    markup = InlineKeyboardMarkup(row_width=2)
    found = False
    for pid, prod in data["products"].items():
        if prod["category"] == cat:
            msg += f"{prod['name'].upper()}\nPRICE : ${prod['price']} Purchase 🛒\n\n"
            markup.add(
                InlineKeyboardButton("🛒 Purchase", callback_data=f"preview_{pid}")
            )
            found = True
    if not found:
        msg = f"🚫 No products available in {cat}."
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_menu"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# Preview
@bot.callback_query_handler(func=lambda call: call.data.startswith("preview_"))
def show_preview(call):
    pid = call.data.split("_")[1]
    prod = data["products"].get(pid)
    if not prod:
        bot.answer_callback_query(call.id, "Product not found.")
        return
    text = (
        f"Info: {prod['name'].upper()}\n"
        f"PRICE : ${prod['price']}\n"
        f"{prod.get('description', 'No info provided.')}"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
        InlineKeyboardButton("🚫 Cancel", callback_data=f"cat_{prod['category']}")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# Buy
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy(call):
    uid = str(call.from_user.id)
    pid = call.data.split("_")[1]
    prod = data["products"].get(pid)
    if not prod:
        bot.answer_callback_query(call.id, "Product no longer available.")
        return
    user = data["users"].setdefault(uid, {"balance": 0})
    price = float(prod["price"])
    if user["balance"] < price:
        bot.answer_callback_query(call.id, "❌ Insufficient balance.")
        return
    user["balance"] -= price
    data["products"].pop(pid)
    save_data()
    bot.edit_message_text(
        f"✅ Purchase Successful!\n\n{prod['name'].upper()}:\n\n`{prod['content']}`",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# Recharge dummy
@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def handle_recharge(call):
    markup = InlineKeyboardMarkup(row_width=2)
    for amount in [25, 50, 100, 150, 200, 300, 500]:
        markup.add(InlineKeyboardButton(f"${amount}", callback_data=f"paybtc_{amount}"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_menu"))
    bot.edit_message_text("🪙 Choose amount to recharge:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("paybtc_"))
def generate_invoice(call):
    amount = call.data.split("_")[1]
    uid = str(call.from_user.id)
    # INSERT BTC/LTC wallet generation code here via Selly
    bot.send_message(call.message.chat.id, f"🪙 Send ${amount} in BTC or LTC to: `YOUR_WALLET_ADDRESS`", parse_mode="Markdown")

# Profile
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def handle_profile(call):
    uid = str(call.from_user.id)
    bal = data["users"].get(uid, {}).get("balance", 0)
    msg = (
        f"👤 *Profile*\n\n"
        f"🆔 ID: `{uid}`\n"
        f"💳 Balance: `${bal}`"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_menu"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# Listings
@bot.callback_query_handler(func=lambda call: call.data == "listings")
def handle_listings(call):
    txt = "*Available Categories:*\n\n" + "\n".join([f"📁 {c}" for c in CATEGORIES])
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_menu"))
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# Rules
@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Store Policy:*\n"
        "❌ No refunds.\n"
        "🪪 Dead CCs aren’t my responsibility.\n"
        "🧠 If you don’t know how to use the info, don’t shop.\n"
        "🔁 One CC replacement allowed (low-end site proof required).\n"
        "🚫 No crybaby support."
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_menu"))
    bot.edit_message_text(rules, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# Go back to menu
@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    bot.edit_message_text("⬅️ Main Menu", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

# Admin command to credit balance
@bot.message_handler(commands=["credit"])
def admin_credit(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, username, amount = message.text.split()
        amount = float(amount)
        uid = None
        for u, info in data["users"].items():
            if info.get("username") == username or username in [u, info.get("id", "")]:
                uid = u
                break
        if not uid:
            uid = str(message.from_user.id)
        data["users"].setdefault(uid, {"balance": 0})
        data["users"][uid]["balance"] += amount
        save_data()
        bot.reply_to(message, f"✅ Credited {amount} to {username}")
    except Exception as e:
        bot.reply_to(message, "❌ Failed. Use /credit username amount")

bot.polling()