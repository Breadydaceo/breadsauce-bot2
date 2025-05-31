import telebot
import json
import os
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"
ADMIN_IDS = ["7388528456"]
DB_PATH = "bot_db.json"
SELLY_API_KEY = "ozJSANrGszds47fwWCo1nveeZHujSwGq_WCMs26EXZGP9m4zXssZfexZNd7TS549"

bot = telebot.TeleBot(TOKEN)

if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump({"products": {}, "users": {}}, f)

with open(DB_PATH) as f:
    data = json.load(f)

def save_data():
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

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

def back_button():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu"))
    return kb

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "user"
    data["users"].setdefault(user_id, {"username": username, "balance": 0})
    save_data()
    welcome = (
        f"👋 Welcome back to *Bread Sauce*, @{username}\n\n"
        "Use one of the tabs below to start shopping smart 💳\n\n"
        "*Support:* @BreadSauceSupport\n\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *BTC/LTC recharges are updated manually within 10 minutes.*\n"
        "🤖 Suspicious activity may trigger bot protection."
    )
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def handle_back(call):
    bot.edit_message_text("📍 Main Menu:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    category = call.data.split("_", 1)[1]
    products = [p for p in data["products"].values() if p["category"] == category]
    if not products:
        bot.edit_message_text("🚫 Nothing in this section right now.", call.message.chat.id, call.message.message_id, reply_markup=back_button())
        return
    for p in products:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{p['id']}"),
            InlineKeyboardButton("🚫 Cancel", callback_data="back_to_menu")
        )
        text = f"*🛍 {p['name']}*\n💲 *Price:* ${p['price']}"
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy(call):
    product_id = call.data.split("_", 1)[1]
    user_id = str(call.from_user.id)
    product = data["products"].get(product_id)
    user = data["users"].get(user_id, {"balance": 0})
    if not product:
        bot.answer_callback_query(call.id, "Product not found.")
        return
    if user["balance"] < product["price"]:
        bot.answer_callback_query(call.id, "❌ Not enough balance.")
        return
    user["balance"] -= product["price"]
    save_data()
    bot.send_message(call.message.chat.id, f"✅ *Purchase successful!*\n\n📦 `{product.get('content', 'No content set.')}`", parse_mode="Markdown")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def handle_recharge(call):
    kb = InlineKeyboardMarkup(row_width=3)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"recharge_{amt}"))
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_menu"))
    bot.edit_message_text("💰 *Select Recharge Amount:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def generate_invoice(call):
    amount = float(call.data.split("_", 1)[1])
    user_id = str(call.from_user.id)
    payload = {
        "title": f"Recharge {user_id}",
        "currency": "BTC",
        "value": amount,
        "white_label": True,
        "metadata": {
            "custom_id": user_id
        }
    }
    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
    if response.status_code == 200:
        invoice = response.json()
        invoice_url = invoice.get("payment_redirection_url", "Unavailable")
        bot.edit_message_text(f"🪙 *Send BTC here:*\n{invoice_url}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("⚠️ Failed to generate invoice.", call.message.chat.id, call.message.message_id, reply_markup=back_button())

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    uid = str(call.from_user.id)
    user = data["users"].get(uid, {"username": "unknown", "balance": 0})
    msg = f"👤 *Your Profile*\n\n🪪 *User:* @{user['username']}\n💰 *Balance:* ${user['balance']:.2f}"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_button())

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Store Rules:*\n"
        "❌ No refunds\n"
        "🧠 Know what you're buying\n"
        "🔁 One replacement per CC (low-end test only)\n"
        "🚫 No crybaby support\n"
        "🤖 Suspicious behavior will be flagged"
    )
    bot.edit_message_text(rules, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_button())

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    msg = "*Available Products:*\n\n"
    if not data["products"]:
        msg += "📭 No products listed."
    for pid, prod in data["products"].items():
        msg += f"🛍️ *{prod['name']}* — ${prod['price']} | ID: `{pid}`\n"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=back_button())

@bot.message_handler(commands=["credit"])
def credit_user(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, uid, amount = message.text.split()
        amount = float(amount)
        if uid in data["users"]:
            data["users"][uid]["balance"] += amount
            save_data()
            bot.reply_to(message, f"✅ Credited ${amount:.2f} to user {uid}")
        else:
            bot.reply_to(message, "⚠️ User not found.")
    except:
        bot.reply_to(message, "Usage: /credit user_id amount")

@bot.message_handler(commands=["add"])
def add_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        parts = message.text.split("|")
        _, pid, name, price, category, content = parts
        data["products"][pid.strip()] = {
            "id": pid.strip(),
            "name": name.strip(),
            "price": float(price.strip()),
            "category": category.strip(),
            "content": content.strip()
        }
        save_data()
        bot.reply_to(message, f"✅ Added product: {name.strip()} in {category.strip()}")
    except:
        bot.reply_to(message, "Usage: /add |id|name|price|category|content")

@bot.message_handler(commands=["remove"])
def remove_product(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    try:
        _, pid = message.text.split()
        if pid in data["products"]:
            del data["products"][pid]
            save_data()
            bot.reply_to(message, f"🗑️ Removed product ID: {pid}")
        else:
            bot.reply_to(message, "❌ Product ID not found.")
    except:
        bot.reply_to(message, "Usage: /remove product_id")

bot.polling()