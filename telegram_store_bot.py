import telebot
import json
import requests
import uuid
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === CONFIG ===
with open("bot_config.json") as config_file:
    config = json.load(config_file)

TOKEN = config["8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"]
ADMIN_IDS = config["7388528456"]
CATEGORIES = config["categories"]
SELLY_API_KEY = config["Nz9mvDhUj_u1ESbbj_acvHPdWiah6zxVr7YfA2pJ66eg16kB4ZQrTN7KT_8-e_4n"]
bot = telebot.TeleBot(TOKEN)
data_path = config["database"]["path"]

try:
    with open(data_path) as db_file:
        data = json.load(db_file)
except FileNotFoundError:
    data = {"products": {}, "users": {}}

def save_data():
    with open(data_path, "w") as db_file:
        json.dump(data, db_file, indent=2)

def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

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

@bot.message_handler(commands=["start"])
def send_welcome(message):
    uid = str(message.from_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {"balance": 0}
        save_data()
    bot.send_message(
        message.chat.id,
        f"👋 Welcome to Bread Sauce, @{message.from_user.username or 'user'}\n\n"
        "Use the buttons below to navigate the store.\n\n"
        "*Support:* @BreadSauceSupport\n\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ BTC/LTC recharges are manually approved.\n\n"
        "🤖 *Bot behavior triggers detection.*",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    cat = call.data[4:]
    msg = f"📂 *{cat} Listings:*\n\n"
    kb = InlineKeyboardMarkup(row_width=2)
    found = False

    for pid, product in data["products"].items():
        if product["category"] == cat:
            msg += f"{product['name']}\nPRICE : ${product['price']} Purchase 🛒\n\n"
            kb.add(InlineKeyboardButton("🛒 Purchase", callback_data=f"preview_{pid}"))
            found = True

    kb.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu"))
    bot.edit_message_text(msg if found else "🚫 Nothing in this category yet.",
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          reply_markup=kb,
                          parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("preview_"))
def show_preview(call):
    pid = call.data.split("_")[1]
    prod = data["products"].get(pid)
    if not prod:
        return bot.answer_callback_query(call.id, "Product not found.")
    msg = (
        f"Info: {prod['name']}\n"
        f"PRICE : ${prod['price']}\n"
        f"{prod['preview']}"
    )
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
        InlineKeyboardButton("🚫 Cancel", callback_data=f"cat_{prod['category']}")
    )
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_product(call):
    uid = str(call.from_user.id)
    pid = call.data.split("_")[1]
    prod = data["products"].get(pid)
    if not prod:
        return bot.answer_callback_query(call.id, "Product not found.")
    user_bal = data["users"][uid]["balance"]

    if user_bal < prod["price"]:
        return bot.answer_callback_query(call.id, "Insufficient balance.")
    
    data["users"][uid]["balance"] -= prod["price"]
    bot.send_message(call.message.chat.id, f"✅ *Purchased:* `{prod['name']}`\n\n{prod['content']}", parse_mode="Markdown")
    del data["products"][pid]
    save_data()

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def handle_recharge(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"pay_{amt}"))
    kb.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu"))
    bot.edit_message_text("🪙 Select recharge amount:", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def create_invoice(call):
    uid = str(call.from_user.id)
    amount = call.data.split("_")[1]
    invoice_id = str(uuid.uuid4())

    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": f"Recharge for user {uid}",
        "value": amount,
        "currency": "BTC",
        "product_id": "pay",
        "white_label": True,
        "metadata": {
            "telegram_id": uid,
            "custom_id": invoice_id
        }
    }

    response = requests.post("https://api.selly.io/v2/payments", json=payload, headers=headers)

    if response.status_code == 200:
        invoice = response.json()
        payment_url = invoice.get("payment_url", "[NO URL]")
        bot.edit_message_text(f"🪙 *Pay with BTC or LTC:*\n\n{payment_url}",
                              call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "❌ Failed to generate invoice.")

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    msg = "*Available Categories:*\n\n"
    for cat in CATEGORIES:
        msg += f"📁 {cat}\n"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    uid = str(call.from_user.id)
    bal = data["users"].get(uid, {}).get("balance", 0)
    msg = f"👤 *Profile*\n\n🆔 ID: `{uid}`\n💰 Balance: `${bal}`"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Store Rules:*\n"
        "❌ No refunds.\n"
        "🪪 Dead CCs not our responsibility.\n"
        "🧠 Know what you're doing before buying.\n"
        "🔁 One replacement only (low-end site proof required)."
    )
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu"))
    bot.edit_message_text(rules, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def return_home(call):
    bot.edit_message_text("🏠 Main Menu:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

# === ADMIN COMMANDS ===

@bot.message_handler(commands=["add"])
def add_product(message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split(" ", 5)
        _, name, price, category, preview, content = parts
        pid = str(uuid.uuid4())
        data["products"][pid] = {
            "name": name,
            "price": float(price),
            "category": category,
            "preview": preview,
            "content": content
        }
        save_data()
        bot.reply_to(message, f"✅ Added product `{name}`.")
    except Exception as e:
        bot.reply_to(message, f"❌ Usage:\n/add NAME PRICE CATEGORY PREVIEW CONTENT\nError: {e}")

@bot.message_handler(commands=["remove"])
def remove_product(message):
    if not is_admin(message.from_user.id):
        return
    pid = message.text.split(" ", 1)[1]
    if pid in data["products"]:
        del data["products"][pid]
        save_data()
        bot.reply_to(message, f"✅ Removed product `{pid}`.")
    else:
        bot.reply_to(message, "❌ Product not found.")

@bot.message_handler(commands=["credit"])
def credit_user(message):
    if not is_admin(message.from_user.id):
        return
    try:
        _, username, amount = message.text.split()
        for uid, user_data in data["users"].items():
            if bot.get_chat(int(uid)).username == username:
                user_data["balance"] += float(amount)
                save_data()
                bot.reply_to(message, f"✅ Credited `${amount}` to @{username}.")
                return
        bot.reply_to(message, "❌ User not found.")
    except Exception as e:
        bot.reply_to(message, f"❌ Usage: /credit USERNAME AMOUNT\nError: {e}")

bot.polling()