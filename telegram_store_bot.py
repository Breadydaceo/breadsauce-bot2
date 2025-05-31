import telebot
import json
import os
import time
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
ADMIN_ID = "7388528456"
SELLY_API_KEY = "Nz9mvDhUj_u1ESbbj_acvHPdWiah6zxVr7YfA2pJ66eg16kB4ZQrTN7KT_8-e_4n"
RETURN_URL = "https://breadydaceo.selly.store"
DB_PATH = "bot_db.json"
RECHARGE_LOG = "recharges.json"

bot = telebot.TeleBot(TOKEN)

if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump({"products": {}, "users": {}}, f)

if not os.path.exists(RECHARGE_LOG):
    with open(RECHARGE_LOG, "w") as f:
        json.dump([], f)

with open(DB_PATH) as f:
    data = json.load(f)

def save_data():
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def log_recharge(user_id, username, amount):
    with open(RECHARGE_LOG) as f:
        logs = json.load(f)
    logs.append({"user_id": user_id, "username": username, "amount": amount, "timestamp": int(time.time())})
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
    uid = str(message.from_user.id)
    username = message.from_user.username or "user"
    data["users"].setdefault(uid, {"username": username, "balance": 0})
    save_data()
    text = (
        f"👋 Welcome back to *Bread Sauce*, @{username}\n\n"
        "Use the tabs below to start shopping smart 💳\n\n"
        "📞 *Support:* @BreadSauceSupport\n\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ BTC recharges are manually updated.\n"
        "🤖 Suspicious behavior may trigger bot protection."
    )
    bot.send_message(message.chat.id, text, reply_markup=build_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    cat = call.data.split("_", 1)[1]
    found = False
    for pid, prod in data["products"].items():
        if prod["category"] == cat:
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
                InlineKeyboardButton("🚫 Cancel", callback_data="cancel")
            )
            text = f"*{prod['name']}*\n💲 *Price:* ${prod['price']}\n🆔 ID: `{pid}`"
            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="Markdown")
            found = True
    if not found:
        bot.send_message(call.message.chat.id, "🚫 Nothing in this section right now.")
    bot.send_message(call.message.chat.id, "🔙 Back to main menu:", reply_markup=build_menu())

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def handle_profile(call):
    uid = str(call.from_user.id)
    user = data["users"].get(uid, {})
    bal = user.get("balance", 0)
    username = user.get("username", "user")
    msg = f"👤 *Profile*\n\n🪪 *User:* @{username}\n💰 *Balance:* ${bal:.2f}"
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    bot.send_message(call.message.chat.id, "🔙 Back to main menu:", reply_markup=build_menu())

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Store Rules:*\n"
        "❌ No refunds\n"
        "🧠 Know what you're buying\n"
        "🔁 One replacement max (low-end proof only)\n"
        "🛡️ No crybaby support"
    )
    bot.send_message(call.message.chat.id, rules, parse_mode="Markdown")
    bot.send_message(call.message.chat.id, "🔙 Back to main menu:", reply_markup=build_menu())

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def handle_listings(call):
    listings = "*🛍️ All Listings:*\n\n"
    for pid, prod in data["products"].items():
        listings += f"{prod['name']} — ${prod['price']} (ID: `{pid}`)\n"
    bot.send_message(call.message.chat.id, listings, parse_mode="Markdown")
    bot.send_message(call.message.chat.id, "🔙 Back to main menu:", reply_markup=build_menu())

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_options(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"recharge_{amt}"))
    bot.send_message(call.message.chat.id, "💰 *Choose amount to recharge:*", reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def create_invoice(call):
    amount = call.data.split("_")[1]
    uid = str(call.from_user.id)
    uname = call.from_user.username or "user"
    payload = {
        "title": f"Bread Sauce Recharge - {uid}",
        "value": float(amount),
        "currency": "BTC",
        "return_url": RETURN_URL,
        "white_label": True
    }
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if response.status_code == 200:
        invoice_url = response.json().get("payment_redirection_url")
        log_recharge(uid, uname, float(amount))
        bot.send_message(call.message.chat.id, f"🪙 *Send BTC here:*\n{invoice_url}", parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "⚠️ Invoice could not be generated. Try again later.")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_back(call):
    bot.send_message(call.message.chat.id, "🔙 Back to main menu:", reply_markup=build_menu())

@bot.message_handler(commands=["add"])
def add_product(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    try:
        parts = message.text.split("|")
        if len(parts) != 6:
            raise Exception("Invalid format")
        _, pid, name, price, category, info = parts
        data["products"][pid.strip()] = {
            "id": pid.strip(),
            "name": name.strip(),
            "price": float(price.strip()),
            "category": category.strip(),
            "info": info.strip()
        }
        save_data()
        bot.reply_to(message, f"✅ Added `{name.strip()}` to *{category.strip()}*", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Usage: `/add |id|name|price|category|info`", parse_mode="Markdown")

@bot.message_handler(commands=["remove"])
def remove_product(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    try:
        _, pid = message.text.split()
        if pid in data["products"]:
            del data["products"][pid]
            save_data()
            bot.reply_to(message, f"🗑 Removed product `{pid}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Product not found.")
    except:
        bot.reply_to(message, "❌ Usage: `/remove ID`")

@bot.message_handler(commands=["credit"])
def credit_user(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    try:
        _, uid, amount = message.text.split()
        if uid in data["users"]:
            data["users"][uid]["balance"] += float(amount)
            save_data()
            bot.reply_to(message, f"✅ Credited ${amount} to `{uid}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ User not found.")
    except:
        bot.reply_to(message, "❌ Usage: `/credit USER_ID AMOUNT`")

@bot.message_handler(commands=["recharges"])
def view_recharges(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    with open(RECHARGE_LOG) as f:
        logs = json.load(f)
    if not logs:
        bot.reply_to(message, "📭 No recharges logged.")
        return
    out = "*📋 Recharge Log:*\n\n"
    for entry in logs[-10:]:
        out += f"👤 `{entry['username']}` — ${entry['amount']} at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry['timestamp']))}\n"
    bot.reply_to(message, out, parse_mode="Markdown")

bot.polling()