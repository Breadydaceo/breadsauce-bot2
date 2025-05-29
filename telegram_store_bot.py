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
    welcome = (
        f"👋 Welcome back to Bread Sauce, @{username}\n"
        "Use one of the tabs below to start shopping smart 💳\n\n"
        "*Support:* @BreadSauceSupport\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *Important:* BTC recharges are updated within 10 minutes.\n"
        "Your balance will be added automatically.\n\n"
        "🤖 *Note:* Suspicious behavior may trigger bot protection."
    )
    kb = InlineKeyboardMarkup(row_width=2)
    menu_buttons = [
        InlineKeyboardButton("💳 Gift Cards", callback_data="cat_Gift Cards"),
        InlineKeyboardButton("🪪 Proz", callback_data="cat_Fullz"),
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
    bot.send_message(message.chat.id, welcome, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_products(call):
    category_name = call.data.split("_", 1)[1]
    
    # Load current products
    try:
        with open(config["database"]["path"]) as db_file:
            data = json.load(db_file)
    except FileNotFoundError:
        data = {"products": {}, "users": {}}

    # Filter products by category
    products = [
        f"*{p['name']}* — {p['price']} BTC"
        for p in data["products"].values()
        if p["category"] == category_name
    ]

    if products:
        product_list = "\n".join(products)
        bot.send_message(call.message.chat.id, f"📦 *{category_name} Products:*\n\n{product_list}", parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, f"⚠️ No products available in *{category_name}*", parse_mode="Markdown")

bot.polling()
bot.polling()