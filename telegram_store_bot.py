import telebot
import json
import requests
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
ADMIN_IDS = ["8032004385"]
SELLY_API_KEY = "ozJSANrGszds47fwWCo1nveeZHujSwGq_WCMs26EXZGP9m4zXssZfexZNd7TS549"
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
    user_id = str(message.from_user.id)
    username = message.from_user.username or "user"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()
    welcome = (
        f"👋 Welcome back to *Bread Sauce*, @{username}"
        "Tap below to start shopping smart 💳"
        "📞 *Support:* @BreadSauceSupport"
        "`Account → Recharge → Listings → Buy`"
        "⚠️ *BTC recharges are updated manually within 10 minutes.*"
        "🤖 Suspicious activity may trigger bot protection."
    )
    bot.send_message(message.chat.id, welcome, reply_markup=build_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def list_category(call):
    category = call.data.split("_", 1)[1]
    products = [p for p in data["products"].values() if p["category"] == category]
    if not products:
        bot.edit_message_text("🚫 Nothing in this section right now.", call.message.chat.id, call.message.message_id)
        return
    for p in products:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{p['id']}"),
            InlineKeyboardButton("🚫 Cancel", callback_data="cancel")
        )
        text = f"*🛍 {p['name']}*"
"💲 *Price:* ${p['price']}"
@bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_back(call):
    bot.edit_message_text("🔙 Back to main menu:", call.message.chat.id, call.message.message_id, reply_markup=build_menu())

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    uid = str(call.from_user.id)
    user = data["users"].get(uid, {"username": "unknown", "balance": 0})
    msg = f"👤 *Your Profile*"

"🪪 *User:* @{user['username']}"
"💰 *Balance:* ${user['balance']:.2f}"
@bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Store Rules:*"
        "❌ No refunds."
        "🧠 Know what you’re buying."
        "🛡️ Replacements allowed with proof (low-end only)."
        "🔁 One replacement per customer."
        "🤖 Bot monitors suspicious activity."
    )
@bot.edit_message_text(rules, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    listings = ""
    for p in data["products"].values():
        listings += f"🛍️ {p['name']} (${p['price']}) — ID: `{p['id']}`"
    bot.edit_message_text(listings or "📦 No listings available.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_prompt(call):
    kb = InlineKeyboardMarkup(row_width=2)
    options = [25, 50, 100, 150, 200, 300, 500]
    for amt in options:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"recharge_{amt}"))
    bot.edit_message_text("💰 *Choose recharge amount:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def generate_invoice(call):
    amount = float(call.data.split("_", 1)[1])
    user_id = str(call.from_user.id)
    payload = {
        "title": f"Bread Sauce Recharge - {user_id}",
        "white_label": True,"
        "value": amount,"
        "currency": "USD","
        "email": f"{user_id}@noreply.io","
        "return_url": RETURN_URL"
    }
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if response.status_code == 200:
        invoice = response.json()
        invoice_url = invoice.get("payment_redirection_url")
        msg = f"🪙 *Send BTC here:*"

"{invoice_url}"
@bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
@bot.answer_callback_query(call.id, "⚠️ Invoice generation failed.", show_alert=false)

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
        data["products"][pid] = {
            "id": pid,
            "name": name.strip(),
            "price": float(price),
            "category": category.strip()
        }
        save_data()
        bot.reply_to(message, f"✅ Added {name} to {category}")
    except:
        bot.reply_to(message, "Usage: /add |id|name|price|category")

bot.polling()