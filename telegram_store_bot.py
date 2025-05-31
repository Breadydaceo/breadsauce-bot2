import telebot
import json
import requests
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
ADMIN_IDS = ["7388528456"]
SELLY_API_KEY = "ozJSANrGszds47fwWCo1nveeZHujSwGq_WCMs26EXZGP9m4zXssZfexZNd7TS549"
RETURN_URL = "https://breadydaceo.selly.store"
DB_PATH = "bot_db.json"

bot = telebot.TeleBot(TOKEN)

if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump({"products": {}, "users": {}, "recharges": []}, f)

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
    user_id = str(message.from_user.id)
    username = message.from_user.username or "user"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()
    text = (
        f"👋 Welcome to *Bread Sauce*, @{username}\n\n"
        "Use the menu below to shop smart 💳\n\n"
        "*Support:* @BreadSauceSupport\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ BTC/LTC recharges update within 10 mins.\n"
        "🤖 Suspicious behavior may trigger bot protection."
    )
    bot.send_message(message.chat.id, text, reply_markup=build_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    cat_name = call.data[4:]
    products = [p for p in data["products"].values() if p["category"] == cat_name]
    if not products:
        bot.edit_message_text("🚫 Nothing in this section right now.", call.message.chat.id, call.message.message_id)
        return
    for p in products:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{p['id']}"),
            InlineKeyboardButton("🚫 Cancel", callback_data="cancel")
        )
        bot.send_message(call.message.chat.id,
            f"*🛍 {p['name']}*\n💲 *Price:* ${p['price']}\n🆔 ID: `{p['id']}`",
            parse_mode="Markdown", reply_markup=kb
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy(call):
    product_id = call.data[4:]
    user_id = str(call.from_user.id)
    if product_id not in data["products"]:
        bot.answer_callback_query(call.id, "❌ Product not found.")
        return
    product = data["products"][product_id]
    if data["users"][user_id]["balance"] < product["price"]:
        bot.answer_callback_query(call.id, "❌ Insufficient balance.", show_alert=True)
        return
    data["users"][user_id]["balance"] -= product["price"]
    del data["products"][product_id]
    save_data()
    bot.edit_message_text(f"✅ *Purchased!* Here’s your info:\n\n`{product['info']}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_back(call):
    bot.edit_message_text("🔙 Back to main menu:", call.message.chat.id, call.message.message_id, reply_markup=build_menu())

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    uid = str(call.from_user.id)
    user = data["users"].get(uid, {"username": "unknown", "balance": 0})
    msg = (
        f"👤 *Your Profile*\n\n"
        f"🪪 *User:* @{user['username']}\n"
        f"💰 *Balance:* ${user['balance']:.2f}"
    )
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="cancel"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Store Rules:*\n"
        "❌ No refunds.\n"
        "🧠 Know what you’re buying.\n"
        "🛡️ Replacements only with proof (low-end only).\n"
        "🔁 1 replacement per customer.\n"
        "🤖 Bot monitors suspicious activity."
    )
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="cancel"))
    bot.edit_message_text(rules, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    text = ""
    for p in data["products"].values():
        text += f"🛍️ {p['name']} — ${p['price']} — ID: `{p['id']}`\n"
    text = text or "📦 No listings available."
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="cancel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_prompt(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"choosecrypto_{amt}"))
    bot.edit_message_text("💰 *Choose recharge amount:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("choosecrypto_"))
def choose_crypto(call):
    amount = call.data.split("_")[1]
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("₿ Bitcoin", callback_data=f"recharge_btc_{amount}"),
        InlineKeyboardButton("Ł Litecoin", callback_data=f"recharge_ltc_{amount}")
    )
    bot.edit_message_text("💱 *Choose crypto:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_btc_") or call.data.startswith("recharge_ltc_"))
def generate_invoice(call):
    parts = call.data.split("_")
    coin, amount = parts[1], parts[2]
    user_id = str(call.from_user.id)
    payload = {
        "title": f"Recharge {user_id}",
        "value": float(amount),
        "currency": coin,
        "return_url": RETURN_URL
    }
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    res = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if res.status_code == 200:
        invoice = res.json().get("payment_redirection_url", "Unavailable")
        data["recharges"].append({"user_id": user_id, "amount": amount, "coin": coin})
        save_data()
        bot.edit_message_text(f"🪙 Send {coin.upper()} here:\n\n{invoice}", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "⚠️ Invoice generation failed.", show_alert=True)

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
        bot.reply_to(message, "❌ Usage: /credit USER_ID AMOUNT")

@bot.message_handler(commands=["add"])
def add_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, pid, name, price, category, info = message.text.split("|")
        data["products"][pid] = {
            "id": pid.strip(),
            "name": name.strip(),
            "price": float(price),
            "category": category.strip(),
            "info": info.strip()
        }
        save_data()
        bot.reply_to(message, f"✅ Added {name} to {category}")
    except:
        bot.reply_to(message, "❌ Usage: /add |id|name|price|category|info")

@bot.message_handler(commands=["remove"])
def remove_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, pid = message.text.split()
        del data["products"][pid]
        save_data()
        bot.reply_to(message, f"✅ Removed product {pid}")
    except:
        bot.reply_to(message, "❌ Usage: /remove product_id")

@bot.message_handler(commands=["recharges"])
def view_recharges(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    msg = "*Recharge Logs:*\n\n"
    for r in data["recharges"]:
        msg += f"🆔 {r['user_id']} — {r['amount']} {r['coin'].upper()}\n"
    bot.reply_to(message, msg or "No recharges yet.", parse_mode="Markdown")

bot.polling()