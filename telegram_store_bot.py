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
bot.remove_webhook()

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
        f"👋 Welcome back to *Bread Sauce*, @{username}\n\n"
        "Tap below to start shopping smart 💳\n\n"
        "📞 *Support:* @BreadSauceSupport\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *BTC/LTC recharges are updated manually within 10 minutes.*\n"
        "🤖 Suspicious activity may trigger bot protection."
    )
    bot.send_message(message.chat.id, welcome, reply_markup=build_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def list_category(call):
    category = call.data.split("_", 1)[1]
    products = [p for p in data["products"].values() if p["category"] == category]
    kb_back = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back_main"))
    if not products:
        bot.edit_message_text("🚫 Nothing in this section right now.", call.message.chat.id, call.message.message_id, reply_markup=kb_back)
        return
    for p in products:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{p['id']}"),
            InlineKeyboardButton("🚫 Cancel", callback_data="back_main")
        )
        text = f"*🛍 {p['name']}*\n💲 *Price:* ${p['price']}"
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_to_main(call):
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
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Store Rules:*\n\n"
        "❌ No refunds.\n"
        "🧠 Know what you’re buying.\n"
        "🛡️ Replacements allowed with proof (low-end only).\n"
        "🔁 One replacement per customer.\n"
        "🤖 Bot monitors suspicious activity."
    )
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back_main"))
    bot.edit_message_text(rules, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    listings = ""
    for p in data["products"].values():
        listings += f"🛍️ {p['name']} (${p['price']}) — ID: `{p['id']}`\n"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back_main"))
    bot.edit_message_text(listings or "📦 No listings available.", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_button_options(call):
    kb = InlineKeyboardMarkup(row_width=3)
    for amt in [5, 25, 50, 100, 500, 1000]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"manual_btc_{amt}"))
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_main"))
    bot.edit_message_text("💸 Choose your deposit amount:", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.message_handler(commands=["deposit"])
def custom_deposit(message):
    try:
        amount = float(message.text.split()[1])
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("BTC", callback_data=f"manual_btc_{amount}"),
            InlineKeyboardButton("LTC", callback_data=f"manual_ltc_{amount}"),
            InlineKeyboardButton("🔙 Back", callback_data="back_main")
        )
        bot.send_message(message.chat.id, f"💰 *Choose coin for ${amount}:*", parse_mode="Markdown", reply_markup=kb)
    except:
        bot.reply_to(message, "⚠️ Usage: /deposit 100")

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_prompt(call):
    kb = InlineKeyboardMarkup(row_width=2)
    for amt in [25, 50, 100, 150, 200, 300, 500]:
        kb.add(InlineKeyboardButton(f"${amt}", callback_data=f"choosecoin_{amt}"))
    bot.edit_message_text("💰 *Choose how much you want to recharge:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("choosecoin_"))
def coin_selector(call):
    amount = call.data.split("_")[1]
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("₿ BTC", callback_data=f"manual_btc_{amount}"),
        InlineKeyboardButton("🪙 LTC", callback_data=f"manual_ltc_{amount}"),
        InlineKeyboardButton("🔙 Back", callback_data="recharge")
    )
    bot.edit_message_text(f"💱 *Select coin for ${amount} recharge:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("manual_"))
def generate_invoice(call):
    _, coin, amt = call.data.split("_")
    amount = float(amt)
    user_id = str(call.from_user.id)

    payload = {
        "title": f"Bread Sauce Recharge - {user_id}",
        "white_label": True,
        "value": amount,
        "currency": coin.upper(),
        "payment_gateway": coin.lower(),
        "product_id": "pay",
        "return_url": "https://breadydaceo.selly.store"
    }

    headers = {
        "Authorization": "Bearer ozJSANrGszds47fwWCo1nveeZHujSwGq_WCMs26EXZGP9m4zXssZfexZNd7TS549",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://selly.io/api/v2/payment_requests", headers=headers, json=payload)
        if response.status_code == 200:
            invoice = response.json()
            address = invoice.get("crypto_address")
            charge_id = invoice.get("id")
            value = invoice.get("value")
            if address:
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={address}"
                caption = (
                    f"📥 *Send {coin.upper()} to the address below:*\n\n"
                    f"`{address}`\n\n"
                    f"💰 *Amount:* `{value}`\n"
                    f"🆔 *Charge ID:* `{charge_id}`\n\n"
                    "⚠️ Send exact amount. Use this address only once. Wait for confirmations."
                )
                bot.send_photo(call.message.chat.id, qr_url, caption=caption, parse_mode="Markdown")
            else:
                bot.send_message(call.message.chat.id, f"⚠️ No address returned.\n\n`{invoice}`", parse_mode="Markdown")
        else:
            error = response.text
            bot.send_message(call.message.chat.id, f"❌ Failed to generate invoice.\n`{error}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"🔥 Exception:\n`{str(e)}`", parse_mode="Markdown")

bot.polling()