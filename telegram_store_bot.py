import telebot
import json
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Load config
with open("bot_config.json") as config_file:
    config = json.load(config_file)

TOKEN = config["telegram_bot_token"]
ADMIN_IDS = config["admin_ids"]
CATEGORIES = config["categories"]
NOWPAYMENTS_API_KEY = config.get("nowpayments_api_key")

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

try:
    with open(config["database"]["path"]) as db_file:
        data = json.load(db_file)
except FileNotFoundError:
    data = {"products": {}, "users": {}}

def save_data():
    with open(config["database"]["path"], "w") as db_file:
        json.dump(data, db_file, indent=2)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    username = message.from_user.username or "user"
    welcome = (
        f"👋 Welcome back to Bread Sauce, @{username}"

"
        "Use one of the tabs below to start shopping smart 💳

"
        "*Support:* @BreadSauceSupport

"
        "`Account → Recharge → Listings → Buy`

"
        "⚠️ *Important:* BTC recharges are updated within 10 minutes.
"
        "Your balance will be added automatically.
"
        "🤖 *Note:* Suspicious behavior may trigger bot protection."
    )
    kb = InlineKeyboardMarkup(row_width=2)
    menu_buttons = [
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
    kb.add(*menu_buttons)
    bot.send_message(message.chat.id, welcome, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def ask_recharge_amount(call):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    amounts = ["25", "50", "100", "150", "200", "300", "500", "Custom"]
    for amt in amounts:
        markup.add(KeyboardButton(f"${amt}"))
    msg = bot.send_message(call.message.chat.id, "💵 Select a recharge amount:", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_recharge_step)

def handle_recharge_step(message):
    user_id = str(message.from_user.id)
    amount_text = message.text.strip().replace("$", "")
    try:
        amount = float(amount_text)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid amount. Try again.")
        return

    payload = {
        "price_amount": amount,
        "price_currency": "usd",
        "pay_currency": "btc",
        "order_id": user_id,
        "order_description": f"Recharge for user {user_id}"
    }
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post("https://api.nowpayments.io/v1/payment", json=payload, headers=headers)
    if response.status_code == 200:
        pay_address = response.json().get("pay_address")
        if pay_address:
            bot.send_message(message.chat.id, f"🪙 *Send BTC to this address:*
`{pay_address}`", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "⚠️ No BTC address returned. Try again later.")
    else:
        bot.send_message(message.chat.id, "⚠️ Could not generate BTC address. Try again later.")

bot.polling()
