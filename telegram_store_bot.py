
import telebot
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load config
with open("bot_config.json") as config_file:
    config = json.load(config_file)

TOKEN = config["telegram_bot_token"]
ADMIN_IDS = config["admin_ids"]
CATEGORIES = config["categories"]

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
    user_id = message.from_user.id
    username = message.from_user.username or "user"
    welcome = f"""👋 Welcome back to Bread Sauce, @{username}

Use one of the tabs below to start shopping smart 💳

*Support:* @BreadSauceSupport

`Account → Recharge → Listings → Buy`

⚠️ Important: BTC recharges are updated within 10 minutes.
Your balance will be added automatically.

🤖 Note: Suspicious behavior may trigger bot protection.
"""
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
    if str(user_id) in ADMIN_IDS:
        kb.add(InlineKeyboardButton("🛠 Add Product", callback_data="admin_add_product"))
    bot.send_message(message.chat.id, welcome, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_product")
def prompt_add_product(call):
    if str(call.from_user.id) not in ADMIN_IDS:
        return bot.send_message(call.message.chat.id, "🚫 Not authorized.")
    msg = bot.send_message(call.message.chat.id, "✏️ Send product like this:

Name | Category | Price")
    bot.register_next_step_handler(msg, finish_add_product)

@bot.message_handler(commands=["addproduct"])
def add_product_cmd(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return bot.send_message(message.chat.id, "🚫 Not authorized.")
    msg = bot.send_message(message.chat.id, "✏️ Send product like this:

Name | Category | Price")
    bot.register_next_step_handler(msg, finish_add_product)

def finish_add_product(message):
    try:
        name, category, price = [x.strip() for x in message.text.split("|")]
        with open(config["database"]["path"]) as db_file:
            data = json.load(db_file)

        pid = str(len(data["products"]) + 1)
        data["products"][pid] = {
            "name": name,
            "category": category,
            "price": price
        }

        with open(config["database"]["path"], "w") as db_file:
            json.dump(data, db_file, indent=2)

        bot.send_message(message.chat.id, f"✅ *{name}* added to *{category}* for *{price} BTC*.", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Error. Format must be:
Name | Category | Price")

bot.polling()
