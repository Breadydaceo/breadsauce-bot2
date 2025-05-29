
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
        f"👋 Welcome back to Bread Sauce, @{username}\n\n"
        "Use one of the tabs below to start shopping smart 💳\n\n"
        "*Support:* @BreadSauceSupport\n\n"
        "`Account → Recharge → Listings → Buy`\n\n"
        "⚠️ *Important:* BTC recharges are updated within 10 minutes.\n"
        "Your balance will be added automatically.\n\n"
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_category(call):
    cat_name = call.data[4:]
    msg = f"📂 *Products in {cat_name}*:\n\n"
    found = False
    for pid, prod in data.get("products", {}).items():
        if prod["category"] == cat_name:
            msg += f"🔹 *{prod['name']}* — `{prod['price']} BTC`\nID: `{pid}`\n\n"
            found = True
    if not found:
        msg += "🚫 Nothing in this section right now."
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

# === NEW BTC-ONLY RECHARGE SYSTEM ===
BTC_ADDRESS = "bc1qexampleyourbtcaddress"

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def handle_recharge_menu(call):
    kb = InlineKeyboardMarkup(row_width=3)
    buttons = [
        InlineKeyboardButton("$25", callback_data="recharge_amt_25"),
        InlineKeyboardButton("$50", callback_data="recharge_amt_50"),
        InlineKeyboardButton("$100", callback_data="recharge_amt_100"),
        InlineKeyboardButton("$200", callback_data="recharge_amt_200"),
        InlineKeyboardButton("$400", callback_data="recharge_amt_400"),
        InlineKeyboardButton("$500", callback_data="recharge_amt_500"),
        InlineKeyboardButton("$1000", callback_data="recharge_amt_1000"),
        InlineKeyboardButton("Custom", callback_data="recharge_amt_custom")
    ]
    kb.add(*buttons)
    bot.send_message(call.message.chat.id, "💰 *How much BTC do you want to upload?*", reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_amt_"))
def handle_recharge_amount(call):
    amount = call.data.split("_")[-1]
    if amount == "custom":
        bot.send_message(call.message.chat.id, "🔢 *Enter the custom amount (in USD) you'd like to upload:*", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, process_custom_recharge)
    else:
        bot.send_message(call.message.chat.id, f"🪙 *Send BTC equivalent to ${amount} here:*\n`{BTC_ADDRESS}`", parse_mode="Markdown")

def process_custom_recharge(message):
    try:
        usd_amount = float(message.text)
        bot.send_message(message.chat.id, f"🪙 *Send BTC equivalent to ${usd_amount} here:*\n`{BTC_ADDRESS}`", parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid amount. Please try again.")

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def handle_listings(call):
    categories_list = "*Available Categories:*\n\n"
    for cat in CATEGORIES:
        categories_list += f"📁 {cat}\n"
    bot.send_message(call.message.chat.id, categories_list, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def handle_profile(call):
    uid = str(call.from_user.id)
    bal = data.get(uid, {}).get("balance", 0)
    msg = (
        f"👤 *Your Bread Sauce Profile:*\n\n"
        f"🆔 ID: `{uid}`\n"
        f"💳 Balance: `{bal} BTC`\n"
        "🛍 Purchase history coming soon..."
    )
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    rules = (
        "📜 *Bread Sauce Policy:*\n"
        "❌ No refunds.\n"
        "🪪 Dead CCs aren't my responsibility.\n"
        "🧠 If you don't know how to use the info, don't shop.\n"
        "🔁 Only 1 CC replacement allowed (must prove failure on a low-end site).\n"
        "🚫 No crybaby support."
    )
    bot.send_message(call.message.chat.id, rules, parse_mode="Markdown")

bot.polling()
