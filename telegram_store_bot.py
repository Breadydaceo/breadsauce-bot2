import telebot
import json
import os
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
ADMIN_IDS = ["7388528456"]
SELLY_API_KEY = "Nz9mvDhUj_u1ESbbj_acvHPdWiah6zxVr7YfA2pJ66eg16kB4ZQrTN7KT_8-e_4n"
RETURN_URL = "https://breadydaceo.selly.store"
DB_PATH = "bot_db.json"

bot = telebot.TeleBot(TOKEN)

if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump({"products": {}, "users": {}}, f)

with open(DB_PATH) as f:
    data = json.load(f)

def save_data():
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

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
    msg = (
        f"👋 Welcome back to *Bread Sauce*, @{username}\n\n"
        "Use the tabs below to start shopping smart 💳\n\n"
        "📞 *Support:* @BreadSauceSupport\n\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *BTC/LTC recharges update manually within 10 minutes.*\n"
        "🤖 Suspicious activity may trigger bot protection."
    )
    bot.send_message(message.chat.id, msg, reply_markup=build_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    category = call.data.split("_", 1)[1]
    found = False
    for pid, prod in data["products"].items():
        if prod["category"] == category:
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
                InlineKeyboardButton("🚫 Cancel", callback_data="cancel")
            )
            text = f"🛍 *{prod['name']}*\n💲 *Price:* ${prod['price']}"
            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="Markdown")
            found = True
    if not found:
        bot.send_message(call.message.chat.id, "🚫 Nothing in this section right now.")
    back_button(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy(call):
    pid = call.data.split("_", 1)[1]
    uid = str(call.from_user.id)
    user = data["users"].get(uid, {})
    prod = data["products"].get(pid)
    if not prod:
        bot.answer_callback_query(call.id, "⚠️ Product not found.")
        return
    if user.get("balance", 0) < prod["price"]:
        bot.send_message(call.message.chat.id, "❌ Not enough balance.")
        return
    data["users"][uid]["balance"] -= prod["price"]
    save_data()
    bot.send_message(call.message.chat.id, f"✅ *Purchase successful!*\n\n🔓 {prod['content']}", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel(call):
    bot.send_message(call.message.chat.id, "🔙 Back to main menu:", reply_markup=build_menu())

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile(call):
    uid = str(call.from_user.id)
    user = data["users"].get(uid, {})
    msg = (
        f"👤 *Your Profile*\n\n"
        f"🪪 User: @{user.get('username', 'unknown')}\n"
        f"💰 Balance: ${user.get('balance', 0):.2f}"
    )
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    back_button(call)

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def rules(call):
    msg = (
        "📜 *Store Rules:*\n"
        "❌ No refunds.\n"
        "🧠 Know what you're buying.\n"
        "🔁 One CC replacement with proof (low-end only).\n"
        "🤖 Bot monitors suspicious activity."
    )
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    back_button(call)

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def listings(call):
    msg = "*📂 All Products:*\n\n"
    for pid, p in data["products"].items():
        msg += f"🛍 {p['name']} - ${p['price']} (ID: `{pid}`)\n"
    bot.send_message(call.message.chat.id, msg or "📦 No listings available.", parse_mode="Markdown")
    back_button(call)

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def choose_crypto(call):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("₿ Bitcoin", callback_data="crypto_BTC"),
        InlineKeyboardButton("Ł Litecoin", callback_data="crypto_LTC")
    )
    bot.edit_message_text("💰 *Choose payment type:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("crypto_"))
def choose_amount(call):
    crypto = call.data.split("_")[1]
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"recharge_{crypto}_{amt}"))
    bot.edit_message_text("💵 *Choose recharge amount:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def gen_invoice(call):
    _, currency, amount = call.data.split("_")
    uid = str(call.from_user.id)
    payload = {
        "title": f"Bread Sauce Recharge",
        "value": float(amount),
        "currency": currency.lower(),
        "white_label": True,
        "return_url": RETURN_URL
    }
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://selly.io/api/v2/payment_requests", json=payload, headers=headers)
    if response.status_code == 200:
        url = response.json().get("payment_redirection_url")
        bot.send_message(call.message.chat.id, f"🪙 *Send your payment here:*\n\n{url}", parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "⚠️ Invoice generation failed. Try again later.")

# Admin: Credit
@bot.message_handler(commands=["credit"])
def credit_user(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, uid, amt = message.text.split()
        uid = str(uid)
        amt = float(amt)
        data["users"].setdefault(uid, {"username": "user", "balance": 0})
        data["users"][uid]["balance"] += amt
        save_data()
        bot.reply_to(message, f"✅ Credited ${amt:.2f} to {uid}")
    except:
        bot.reply_to(message, "Usage: /credit USER_ID AMOUNT")

# Admin: Add Product
@bot.message_handler(commands=["add"])
def add_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, pid, name, price, category, content = message.text.split("|")
        data["products"][pid] = {
            "id": pid,
            "name": name.strip(),
            "price": float(price),
            "category": category.strip(),
            "content": content.strip()
        }
        save_data()
        bot.reply_to(message, f"✅ Added product {name} to {category}")
    except:
        bot.reply_to(message, "Usage: /add |id|name|price|category|content")

# Admin: Remove Product
@bot.message_handler(commands=["remove"])
def remove_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, pid = message.text.split()
        if pid in data["products"]:
            del data["products"][pid]
            save_data()
            bot.reply_to(message, f"🗑 Removed product ID {pid}")
        else:
            bot.reply_to(message, "⚠️ Product ID not found.")
    except:
        bot.reply_to(message, "Usage: /remove PRODUCT_ID")

def back_button(call):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back to Menu", callback_data="cancel"))
    bot.send_message(call.message.chat.id, "⬅️", reply_markup=kb)

bot.polling()