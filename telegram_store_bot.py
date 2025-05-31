import telebot
import json
import requests
import os
import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
ADMIN_ID = "7388528456"
DB_PATH = "bot_db.json"
RECHARGE_LOG = "recharges.json"

bot = telebot.TeleBot(TOKEN)

if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump({"products": {}, "users": {}}, f)

with open(DB_PATH) as f:
    data = json.load(f)

def save_data():
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def log_recharge(user_id, username, amount):
    if not os.path.exists(RECHARGE_LOG):
        with open(RECHARGE_LOG, "w") as f:
            json.dump([], f)

    with open(RECHARGE_LOG) as f:
        logs = json.load(f)

    logs.append({
        "user_id": user_id,
        "username": username,
        "amount": amount,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    with open(RECHARGE_LOG, "w") as f:
        json.dump(logs, f, indent=2)

def build_menu():
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
    return kb

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "user"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()
    welcome = (
        f"👋 Welcome back to *Bread Sauce*, @{username}\n\n"
        "Use the menu below to start shopping smart 💳\n\n"
        "📞 *Support:* @BreadSauceSupport\n\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *BTC recharges are updated manually within 10 minutes.*\n"
        "🤖 Suspicious activity may trigger bot protection."
    )
    bot.send_message(message.chat.id, welcome, reply_markup=build_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_prompt(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"recharge_{amt}"))
    bot.edit_message_text("💰 *Choose recharge amount:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def generate_invoice(call):
    amount = float(call.data.split("_", 1)[1])
    user_id = str(call.from_user.id)
    username = call.from_user.username or "unknown"
    log_recharge(user_id, username, amount)

    bot.answer_callback_query(call.id, "✅ Recharge request logged. Please send your payment manually to admin.", show_alert=True)
    bot.edit_message_text(f"🪙 *Manual recharge of ${amount} logged.*\n\nAn admin will credit your balance shortly.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=["credit"])
def credit_user(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    try:
        _, uid, amount = message.text.split()
        uid = str(uid)
        amount = float(amount)
        if uid in data["users"]:
            data["users"][uid]["balance"] += amount
            save_data()
            bot.reply_to(message, f"✅ Credited ${amount} to {uid}")
        else:
            bot.reply_to(message, "⚠️ User not found.")
    except:
        bot.reply_to(message, "❌ Usage: /credit USER_ID AMOUNT")

@bot.message_handler(commands=["add"])
def add_product(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    try:
        _, pid, name, price, category = message.text.split("|")
        data["products"][pid] = {
            "id": pid.strip(),
            "name": name.strip(),
            "price": float(price.strip()),
            "category": category.strip()
        }
        save_data()
        bot.reply_to(message, f"✅ Added {name} to {category}")
    except:
        bot.reply_to(message, "❌ Usage: /add |id|name|price|category")

@bot.message_handler(commands=["remove"])
def remove_product(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    try:
        _, pid = message.text.split()
        if pid in data["products"]:
            del data["products"][pid]
            save_data()
            bot.reply_to(message, f"🗑️ Removed product {pid}")
        else:
            bot.reply_to(message, "⚠️ Product not found.")
    except:
        bot.reply_to(message, "❌ Usage: /remove PRODUCT_ID")

@bot.message_handler(commands=["recharges"])
def view_recharges(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    if not os.path.exists(RECHARGE_LOG):
        bot.reply_to(message, "📂 No recharges logged yet.")
        return

    with open(RECHARGE_LOG) as f:
        logs = json.load(f)

    if not logs:
        bot.reply_to(message, "📂 No recharges logged yet.")
        return

    msg = "*📜 Recent Recharges:*\n\n"
    for entry in logs[-10:]:
        msg += f"• {entry['username']} ({entry['user_id']}) — ${entry['amount']} at {entry['timestamp']}\n"

    bot.reply_to(message, msg, parse_mode="Markdown")

bot.polling()