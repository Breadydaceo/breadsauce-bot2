
import telebot
import json
import requests
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load config
with open("bot_config.json") as config_file:
    config = json.load(config_file)

TOKEN = config["telegram_bot_token"]
ADMIN_IDS = config["admin_ids"]
CATEGORIES = config["categories"]
COINBASE_API_KEY = config["coinbase_api_key"]

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# Load or initialize data
try:
    with open(config["database"]["path"]) as db_file:
        data = json.load(db_file)
except FileNotFoundError:
    data = {"products": {}, "users": {}, "payments": {}, "spam": {}}

def save_data():
    with open(config["database"]["path"], "w") as db_file:
        json.dump(data, db_file, indent=2)

def is_spamming(user_id):
    now = time.time()
    last = data["spam"].get(str(user_id), 0)
    if now - last < 2:  # 2 second cooldown
        return True
    data["spam"][str(user_id)] = now
    return False

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "user"
    welcome = (
        f"👋 Welcome back to Bread Sauce, @{username}\n\n"
        "Use one of the tabs below to start shopping smart 💳\n\n"
        "*Support:* @BreadSauceSupport\n\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *Important:* BTC recharges are updated within 10 minutes.\n"
        "Your balance will be added automatically."
    )
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
    bot.send_message(message.chat.id, welcome, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def handle_recharge(call):
    if is_spamming(call.from_user.id):
        bot.answer_callback_query(call.id, "🤖 Bot behavior detected. Please slow down.")
        return
    msg = (
        "*Bread Sauce v1.0 - Deposit*

"
        "Choose your deposit amount or type /deposit {amount}

"
        "*Supported:* BTC
"
        "_Funds will be added after 2 confirmations._"
    )
    kb = InlineKeyboardMarkup(row_width=3)
    amounts = [25, 50, 100, 250, 500, 1000]
    for i in range(0, len(amounts), 3):
        row = [InlineKeyboardButton(f"${amt}", callback_data=f"deposit_{amt}") for amt in amounts[i:i+3]]
        kb.row(*row)
    kb.row(InlineKeyboardButton("📦 Main Menu", callback_data="main_menu"))
    bot.send_message(call.message.chat.id, msg, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_"))
def handle_preset_deposit(call):
    if is_spamming(call.from_user.id):
        bot.answer_callback_query(call.id, "🤖 Bot behavior detected. Please slow down.")
        return
    amount = call.data.split("_")[1]
    create_charge(call.message.chat.id, amount)

@bot.message_handler(commands=["deposit"])
def handle_custom_deposit(message):
    try:
        amount = float(message.text.split()[1])
        create_charge(message.chat.id, amount)
    except:
        bot.send_message(message.chat.id, "❌ Invalid format. Use /deposit 150")

@bot.callback_query_handler(func=lambda call: call.data.startswith("refresh_"))
def refresh_status(call):
    charge_id = call.data.split("_")[1]
    status = get_charge_status(charge_id)
    bot.answer_callback_query(call.id, f"Status: {status}")

def get_charge_status(charge_id):
    url = f"https://api.commerce.coinbase.com/charges/{charge_id}"
    headers = {
        "X-CC-Api-Key": COINBASE_API_KEY,
        "X-CC-Version": "2018-03-22"
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        return data["data"]["timeline"][-1]["status"]
    return "Unknown"

def create_charge(chat_id, amount):
    payload = {
        "name": "Bread Sauce BTC Recharge",
        "description": f"Recharge for {chat_id}",
        "local_price": {"amount": str(amount), "currency": "USD"},
        "pricing_type": "fixed_price",
        "metadata": {"user": chat_id}
    }
    headers = {
        "Content-Type": "application/json",
        "X-CC-Api-Key": COINBASE_API_KEY,
        "X-CC-Version": "2018-03-22"
    }
    r = requests.post("https://api.commerce.coinbase.com/charges", json=payload, headers=headers)
    if r.status_code == 201:
        charge = r.json()["data"]
        hosted_url = charge["hosted_url"]
        address = charge["addresses"]["bitcoin"]
        btc_amt = charge["pricing"]["bitcoin"]["amount"]
        charge_id = charge["id"]
        data["payments"][charge_id] = {"user": chat_id, "usd": amount}
        save_data()
        msg = (
            "*📥 Deposit Instructions*

"
            f"Send *exactly* `{btc_amt} BTC`
"
            f"To: `{address}`
"
            f"Charge ID: `{charge_id}`

"
            "🕒 *Expires in 8 hours.*
"
            "✅ Wait for 2 confirmations.
"
            "📩 DM @BreadSauceSupport after payment."
        )
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("📋 Copy Address", callback_data="copy_disabled"),
            InlineKeyboardButton("🔁 Refresh Status", callback_data=f"refresh_{charge_id}"),
            InlineKeyboardButton("🌐 Open Invoice", url=hosted_url)
        )
        bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=kb)
    else:
        bot.send_message(chat_id, "⚠️ Coinbase error. Try again later.")

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def go_back(call):
    send_welcome(call)

bot.polling()
