import telebot
import json
import os
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
ADMIN_IDS = ["7388528456"]
DB_PATH = "bot_db.json"
SELLY_API_KEY = "ozJSANrGszds47fwWCo1nveeZHujSwGq_WCMs26EXZGP9m4zXssZfexZNd7TS549"
RETURN_URL = "https://breadydaceo.selly.store"

bot = telebot.TeleBot(TOKEN)

if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump({"products": {}, "users": {}, "recharges": []}, f)

with open(DB_PATH) as f:
    data = json.load(f)

def save_data():
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def get_main_menu():
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
    uid = str(message.from_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {"balance": 0, "username": message.from_user.username or "user"}
        save_data()
    bot.send_message(message.chat.id, (
        f"👋 Welcome to *Bread Sauce*, @{data['users'][uid]['username']}\n\n"
        "💳 Tap a category below to start shopping smart\n\n"
        "⚠️ BTC & LTC recharges added manually after ~10 mins\n"
        "🤖 Suspicious behavior will trigger bot protection\n\n"
        "*Support:* @BreadSauceSupport"
    ), reply_markup=get_main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    cat = call.data.split("_", 1)[1]
    items = [p for p in data["products"].values() if p["category"] == cat]
    if not items:
        bot.edit_message_text(f"🚫 No items in *{cat}* right now.", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_to_menu())
        return
    for item in items:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{item['id']}"),
            InlineKeyboardButton("🚫 Cancel", callback_data="cancel")
        )
        kb.add(InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main"))
        text = f"*🛍 {item['name']}*\n💰 *Price:* ${item['price']:.2f}\n🆔 `{item['id']}`"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)

def back_to_menu():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main"))

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    bot.edit_message_text("🔙 Back to main menu:", call.message.chat.id, call.message.message_id, reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile(call):
    uid = str(call.from_user.id)
    user = data["users"].get(uid, {"balance": 0, "username": "unknown"})
    msg = f"👤 *User:* @{user['username']}\n💰 *Balance:* ${user['balance']:.2f}"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_to_menu())

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def rules(call):
    msg = (
        "📜 *Store Rules:*\n"
        "❌ No refunds\n"
        "🧠 Know what you’re buying\n"
        "🛡️ 1 CC replacement allowed w/ proof (low-end site only)\n"
        "🤖 Suspicious activity will block access"
    )
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_to_menu())

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def listings(call):
    items = data["products"].values()
    if not items:
        msg = "📦 No active listings"
    else:
        msg = "\n\n".join([f"🔹 *{i['name']}* — `${i['price']}`\n🆔 `{i['id']}`" for i in items])
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_to_menu())

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def choose_coin(call):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("₿ Bitcoin", callback_data="coin_btc"),
        InlineKeyboardButton("Ł Litecoin", callback_data="coin_ltc"),
        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")
    )
    bot.edit_message_text("💰 *Choose your payment method:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("coin_"))
def choose_amount(call):
    coin = call.data.split("_", 1)[1]
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"recharge_{coin}_{amt}"))
    kb.add(InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main"))
    bot.edit_message_text(f"💰 *Choose recharge amount:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def generate_invoice(call):
    _, coin, amount = call.data.split("_")
    user_id = str(call.from_user.id)
    payload = {
        "title": f"Recharge ${amount}",
        "value": float(amount),
        "currency": coin.lower(),
        "white_label": True,
        "return_url": RETURN_URL
    }
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    r = requests.post("https://selly.io/api/v2/payment_requests", json=payload, headers=headers)
    if r.status_code == 200:
        invoice = r.json().get("payment_redirection_url", "Unavailable")
        data["recharges"].append({"user": user_id, "amount": float(amount), "coin": coin.upper()})
        save_data()
        bot.edit_message_text(f"🪙 *Send payment here:*\n\n{invoice}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("⚠️ Failed to generate invoice.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_buy(call):
    uid = str(call.from_user.id)
    pid = call.data.split("_", 1)[1]
    user = data["users"].get(uid)
    product = data["products"].get(pid)
    if not user or not product:
        bot.answer_callback_query(call.id, "❌ Invalid product or user.")
        return
    if user["balance"] < product["price"]:
        bot.answer_callback_query(call.id, "💸 Not enough balance.")
        return
    user["balance"] -= product["price"]
    del data["products"][pid]
    save_data()
    bot.edit_message_text(f"✅ *Purchase successful!*\n\n{product['name']}:\n`{product.get('info', 'No details provided.')}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_action(call):
    bot.edit_message_text("❌ Cancelled.", call.message.chat.id, call.message.message_id, reply_markup=get_main_menu())

@bot.message_handler(commands=["credit"])
def credit_cmd(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, uid, amt = message.text.split()
        data["users"][uid]["balance"] += float(amt)
        save_data()
        bot.reply_to(message, f"✅ Credited ${amt} to user {uid}")
    except:
        bot.reply_to(message, "❌ Usage: /credit USERID AMOUNT")

@bot.message_handler(commands=["add"])
def add_cmd(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, pid, name, price, category, info = message.text.split("|")
        data["products"][pid.strip()] = {
            "id": pid.strip(),
            "name": name.strip(),
            "price": float(price.strip()),
            "category": category.strip(),
            "info": info.strip()
        }
        save_data()
        bot.reply_to(message, f"✅ Added product: {name.strip()}")
    except:
        bot.reply_to(message, "❌ Usage: /add |id|name|price|category|info")

@bot.message_handler(commands=["remove"])
def remove_cmd(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, pid = message.text.split()
        if pid in data["products"]:
            del data["products"][pid]
            save_data()
            bot.reply_to(message, f"✅ Removed product {pid}")
        else:
            bot.reply_to(message, "❌ Product not found.")
    except:
        bot.reply_to(message, "❌ Usage: /remove PRODUCT_ID")

@bot.message_handler(commands=["recharges"])
def view_recharges(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    if not data["recharges"]:
        bot.reply_to(message, "📭 No recent recharges.")
        return
    msg = "\n".join([f"🧾 User: {r['user']} — ${r['amount']} {r['coin']}" for r in data["recharges"][-10:]])
    bot.reply_to(message, f"*Last Recharges:*\n{msg}", parse_mode="Markdown")

bot.polling()