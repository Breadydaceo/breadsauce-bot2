
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
bot.remove_webhook()  # Clear any existing webhook before polling

# Load or initialize data
try:
    with open(config["database"]["path"]) as db_file:
        data = json.load(db_file)
except FileNotFoundError:
    data = {"products": {}, "users": {}}

def save_data():
    with open(config["database"]["path"], "w") as db_file:
        json.dump(data, db_file, indent=2)

# Start command
@bot.message_handler(commands=["start"])
def send_welcome(message):
    kb = InlineKeyboardMarkup()
    for cat in CATEGORIES:
        kb.add(InlineKeyboardButton(cat, callback_data=f"cat_{cat}"))
    kb.add(InlineKeyboardButton("💰 Recharge Pocket", callback_data="recharge"))
    kb.add(InlineKeyboardButton("🕓 Purchase History", callback_data="history"))
    kb.add(InlineKeyboardButton("📜 Bread Sauce Rules", callback_data="rules"))
    bot.send_message(message.chat.id, "📲 Welcome to Bread Sauce. Choose an option:", reply_markup=kb)

# Show products in category
@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    cat_name = call.data[4:]
    msg = f"🛒 Products in *{cat_name}*:\n\n"
    found = False
    for pid, prod in data.get("products", {}).items():
        if prod["category"] == cat_name:
            msg += f"📦 *{prod['name']}* - `{prod['price']} BTC`\nID: `{pid}`\n\n"
            found = True
    if not found:
        msg += "🚫 No products in this category yet."
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

# Recharge placeholder
@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def handle_recharge(call):
    bot.send_message(call.message.chat.id, "🚧 Recharge system coming soon.")

# History placeholder
@bot.callback_query_handler(func=lambda call: call.data == "history")
def handle_history(call):
    bot.send_message(call.message.chat.id, "📦 No purchase history yet.")

# Rules
@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Bread Sauce Policy:*\n"
        "❌ No refunds.\n"
        "🪪 Dead CCs aren't my responsibility.\n"
        "🧠 If you don't know how to use the info, don't shop.\n"
        "🔁 Only 1 CC replacement allowed (must prove failure on a low-end site).\n"
        "🚫 No support. Be smart or bounce."
    )
    bot.send_message(call.message.chat.id, rules, parse_mode="Markdown")

# Run bot
print("Bot is running...")
bot.polling()
