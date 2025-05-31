import telebot
import json
import os
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === CONFIG ===
TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
ADMIN_ID = "7388528456"
SELLY_API_KEY = "Nz9mvDhUj_u1ESbbj_acvHPdWiah6zxVr7YfA2pJ66eg16kB4ZQrTN7KT_8-e_4n"
RETURN_URL = "https://breadydaceo.selly.store"
DB_PATH = "bot_db.json"

bot = telebot.TeleBot(TOKEN)

# === INIT DATABASE ===
if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump({"products": {}, "users": {}, "recharges": []}, f)

with open(DB_PATH) as f:
    data = json.load(f)

def save_data():
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

# === MAIN MENU ===
def main_menu():
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

# === START ===
@bot.message_handler(commands=["start"])
def send_welcome(message):
    uid = str(message.from_user.id)
    username = message.from_user.username or "user"
    if uid not in data["users"]:
        data["users"][uid] = {"username": username, "balance": 0}
        save_data()
    text = (
        f"👋 Welcome back to *Bread Sauce*, @{username}\n\n"
        "Use the tabs below to shop smart 💳\n\n"
        "⚠️ BTC recharges are processed manually.\n"
        "🤖 Suspicious behavior may trigger bot protection."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

# === PRODUCT CATEGORY VIEW ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    category = call.data[4:]
    products = [p for p in data["products"].values() if p["category"] == category]
    if not products:
        bot.edit_message_text("🚫 Nothing in this section right now.", call.message.chat.id, call.message.message_id, reply_markup=back_btn())
        return
    for product in products:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{product['id']}"),
            InlineKeyboardButton("🚫 Cancel", callback_data="cancel")
        )
        text = f"🛍 *{product['name']}*\n💰 *Price:* ${product['price']}"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)

# === BUY PRODUCT ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_product(call):
    uid = str(call.from_user.id)
    pid = call.data.split("_")[1]
    user = data["users"].get(uid)
    product = data["products"].get(pid)

    if not user or not product:
        bot.answer_callback_query(call.id, "⚠️ Product not found.")
        return

    if user["balance"] < product["price"]:
        bot.answer_callback_query(call.id, "❌ Insufficient balance.")
        return

    user["balance"] -= product["price"]
    product_info = product["info"]
    del data["products"][pid]  # auto-expire
    save_data()

    bot.edit_message_text(f"✅ *Purchase successful!*\n\n`{product_info}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# === CANCEL ===
@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_back(call):
    bot.edit_message_text("🔙 Back to menu:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

# === PROFILE ===
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    uid = str(call.from_user.id)
    user = data["users"].get(uid, {"username": "unknown", "balance": 0})
    msg = f"👤 *Profile*\n\n🪪 *User:* @{user['username']}\n💰 *Balance:* ${user['balance']:.2f}"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="cancel"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

# === RULES ===
@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    msg = (
        "📜 *Rules:*\n"
        "❌ No refunds\n"
        "🧠 Know what you’re buying\n"
        "🛡️ 1 Replacement allowed (low-end only)\n"
        "🤖 Suspicious activity = ban"
    )
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="cancel"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

# === LISTINGS ===
@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    listings = ""
    for p in data["products"].values():
        listings += f"🛍️ {p['name']} (${p['price']}) — ID: `{p['id']}`\n"
    listings = listings or "📦 No listings available."
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="cancel"))
    bot.edit_message_text(listings, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

# === RECHARGE MENU ===
@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_prompt(call):
    kb = InlineKeyboardMarkup(row_width=3)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"recharge_{amt}"))
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="cancel"))
    bot.edit_message_text("💰 *Choose recharge amount:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

# === GENERATE SELLY INVOICE ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def generate_invoice(call):
    amount = call.data.split("_")[1]
    uid = str(call.from_user.id)

    payload = {
        "title": f"Recharge ${amount} - {uid}",
        "currency": "BTC",
        "value": amount,
        "white_label": True,
        "return_url": RETURN_URL
    }

    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if r.status_code == 200:
        invoice = r.json()
        url = invoice.get("payment_redirection_url")
        data["recharges"].append({"user_id": uid, "amount": amount, "url": url})
        save_data()
        bot.edit_message_text(f"🪙 *Send BTC here:*\n\n{url}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "⚠️ Invoice failed. Try again.")

# === ADMIN COMMANDS ===
@bot.message_handler(commands=["add"])
def add_product(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    try:
        _, pid, name, price, category, info = message.text.split("|")
        data["products"][pid.strip()] = {
            "id": pid.strip(),
            "name": name.strip(),
            "price": float(price),
            "category": category.strip(),
            "info": info.strip()
        }
        save_data()
        bot.reply_to(message, f"✅ Added {name.strip()} to {category.strip()}")
    except:
        bot.reply_to(message, "❌ Usage: /add |id|name|price|category|info")

@bot.message_handler(commands=["remove"])
def remove_product(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    try:
        _, pid = message.text.split()
        if pid in data["products"]:
            del data["products"][pid]
            save_data()
            bot.reply_to(message, "✅ Product removed.")
        else:
            bot.reply_to(message, "⚠️ Product ID not found.")
    except:
        bot.reply_to(message, "❌ Usage: /remove product_id")

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
        bot.reply_to(message, "❌ Usage: /credit user_id amount")

@bot.message_handler(commands=["recharges"])
def list_recharges(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    logs = data.get("recharges", [])
    if not logs:
        bot.reply_to(message, "📭 No recharges found.")
    else:
        msg = "\n".join([f"{log['user_id']} - ${log['amount']}" for log in logs[-10:]])
        bot.reply_to(message, f"📄 Last Recharges:\n{msg}")

# === RUN ===
bot.polling()