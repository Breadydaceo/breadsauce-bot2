import telebot
import json
import requests
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot setup
TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
ADMIN_IDS = ["7388528456"]
SELLY_API_KEY = "ozJSANrGszds47fwWCo1nveeZHujSwGq_WCMs26EXZGP9m4zXssZfexZNd7TS549"
RETURN_URL = "https://breadydaceo.selly.store"
DB_PATH = "bot_db.json"

bot = telebot.TeleBot(TOKEN)

if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump({"products": {}, "users": {}, "recharge_requests": []}, f)

with open(DB_PATH) as f:
    data = json.load(f)

def save_data():
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def main_menu():
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
        f"👋 Welcome to *Bread Sauce*, @{username}!\n\n"
        "Use the buttons below to explore.\n\n"
        "*Support:* @BreadSauceSupport\n"
        "💡 `Account → Recharge → Listings → Buy`\n\n"
        "⚠️ BTC/LTC recharges are updated manually.\n"
        "🤖 Suspicious activity may be blocked."
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=main_menu())

def back_button():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main"))
    return kb

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def category_view(call):
    cat = call.data.split("_", 1)[1]
    products = [p for p in data["products"].values() if p["category"] == cat]
    if not products:
        bot.edit_message_text("🚫 Nothing in this category yet.", call.message.chat.id, call.message.message_id, reply_markup=back_button())
        return
    for p in products:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{p['id']}"),
            InlineKeyboardButton("🚫 Cancel", callback_data="back_main")
        )
        msg = f"*🛍 {p['name']}*\n💰 *Price:* ${p['price']:.2f}"
        bot.send_message(call.message.chat.id, msg, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile(call):
    uid = str(call.from_user.id)
    user = data["users"].get(uid, {"username": "unknown", "balance": 0})
    msg = (
        f"👤 *Your Profile*\n\n"
        f"🪪 *User:* @{user['username']}\n"
        f"💳 *Balance:* ${user['balance']:.2f}"
    )
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_button())

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def rules(call):
    rules = (
        "📜 *Store Rules:*\n"
        "❌ No refunds.\n"
        "🧠 Know what you’re buying.\n"
        "🔁 1 CC replacement allowed with proof (low-end only).\n"
        "🚫 No crybaby support.\n"
        "🤖 Suspicious bots will be blocked."
    )
    bot.edit_message_text(rules, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_button())

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def listings(call):
    if not data["products"]:
        bot.edit_message_text("📦 No listings available yet.", call.message.chat.id, call.message.message_id, reply_markup=back_button())
        return
    listings = "\n".join([f"🛍 {p['name']} (${p['price']}) — ID: `{p['id']}`" for p in data["products"].values()])
    bot.edit_message_text(listings, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_button())

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_menu(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(
            InlineKeyboardButton(f"₿ ${amt}", callback_data=f"recharge_btc_{amt}"),
            InlineKeyboardButton(f"Ł ${amt}", callback_data=f"recharge_ltc_{amt}")
        )
    kb.add(InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main"))
    bot.edit_message_text("💰 *Choose recharge amount and coin:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def create_invoice(call):
    _, coin, amount = call.data.split("_")
    user_id = str(call.from_user.id)
    amount = float(amount)
    payload = {
        "title": f"Bread Sauce Recharge - {user_id}",
        "currency": coin,
        "value": amount,
        "white_label": True,
        "return_url": RETURN_URL
    }
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    res = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if res.status_code == 200:
        url = res.json().get("payment_redirection_url")
        data["recharge_requests"].append({"user_id": user_id, "amount": amount, "coin": coin})
        save_data()
        bot.edit_message_text(f"🪙 *Send {coin.upper()} here:*\n{url}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "⚠️ Invoice failed to generate.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main_menu(call):
    bot.edit_message_text("🔙 Back to main menu:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

@bot.message_handler(commands=["credit"])
def credit_user(message):
    if str(message.from_user.id) not in ADMIN_IDS:
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
        bot.reply_to(message, "Usage: /credit USER_ID AMOUNT")

@bot.message_handler(commands=["add"])
def add_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, pid, name, price, category = message.text.split("|")
        pid = pid.strip()
        name = name.strip()
        price = float(price.strip())
        category = category.strip()
        data["products"][pid] = {
            "id": pid,
            "name": name,
            "price": price,
            "category": category
        }
        save_data()
        bot.reply_to(message, f"✅ Added {name} (${price}) to {category}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Usage: /add |id|name|price|category")

@bot.message_handler(commands=["remove"])
def remove_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, pid = message.text.split()
        if pid in data["products"]:
            del data["products"][pid]
            save_data()
            bot.reply_to(message, f"✅ Removed product with ID {pid}")
        else:
            bot.reply_to(message, "⚠️ Product not found.")
    except:
        bot.reply_to(message, "Usage: /remove PRODUCT_ID")

bot.polling()