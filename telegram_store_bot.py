
import telebot
from telebot import types
import requests
import json
import time
from admin_product_handler import show_add_product_panel, handle_admin_add_product
from admin_remove_product import show_remove_product_panel, handle_admin_remove_category, handle_confirm_removal

with open("bot_config.json") as f:
    config = json.load(f)

bot = telebot.TeleBot(config["telegram_bot_token"])
admin_ids = config["admin_ids"]
categories = config["categories"]
coinbase_api_key = config["coinbase_api_key"]

try:
    with open("data.json") as f:
        db = json.load(f)
except:
    db = {}

def save_db():
    with open("data.json", "w") as f:
        json.dump(db, f, indent=2)

def get_balance(user_id):
    return db.get(str(user_id), {}).get("balance", 0)

def add_balance(user_id, amount):
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"balance": 0, "history": [], "purchases": []}
    db[uid]["balance"] += amount
    db[uid]["history"].append(f"Received {amount} BTC")
    save_db()

def deduct_balance(user_id, amount):
    uid = str(user_id)
    db[uid]["balance"] -= amount
    save_db()

products = {cat: [] for cat in categories}

@bot.message_handler(commands=["start"])
def send_welcome(message):
    uid = str(message.from_user.id)
    if uid not in db:
        db[uid] = {"balance": 0, "history": [], "purchases": []}
    markup = types.InlineKeyboardMarkup(row_width=2)
    for cat in categories:
        markup.add(types.InlineKeyboardButton(cat, callback_data=f"cat_{cat}"))
    markup.add(
        types.InlineKeyboardButton("💰 Recharge Pocket", callback_data="recharge"),
        types.InlineKeyboardButton("📈 Recharge History", callback_data="rchist"),
        types.InlineKeyboardButton("🕓 Purchase History", callback_data="purchases"),
        types.InlineKeyboardButton("📜 Bread Sauce Rules", callback_data="rules")
    )
    bot.send_message(message.chat.id, "📲 Welcome to Bread Sauce. Select an option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_products(call):
    cat = call.data.split("_", 1)[1]
    uid = str(call.from_user.id)
    if not products.get(cat):
        bot.send_message(call.message.chat.id, f"❌ No products in {cat}.")
        return
    for i, p in enumerate(products[cat]):
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton(f"Buy {p['name']} - {p['price']} BTC", callback_data=f"buy_{cat}_{i}"))
        bot.send_message(call.message.chat.id, f"{p['name']} - {p['price']} BTC", reply_markup=btn)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_product(call):
    _, cat, idx = call.data.split("_")
    uid = str(call.from_user.id)
    product = products[cat][int(idx)]
    if get_balance(uid) < product["price"]:
        bot.send_message(call.message.chat.id, "❌ Insufficient balance.")
        return
    deduct_balance(uid, product["price"])
    db[uid]["purchases"].append(product["name"])
    bot.send_message(call.message.chat.id, f"✅ Purchase successful.\n\n{product['data']}")
    save_db()

@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def recharge_btc(call):
    uid = str(call.from_user.id)
    payload = {
        "name": "Bread Sauce Wallet Recharge",
        "description": f"Recharge for {uid}",
        "local_price": {
            "amount": "10.00",
            "currency": "USD"
        },
        "pricing_type": "fixed_price",
        "metadata": {
            "user_id": uid
        }
    }
    headers = {
        "Content-Type": "application/json",
        "X-CC-Api-Key": coinbase_api_key,
        "X-CC-Version": "2018-03-22"
    }
    response = requests.post("https://api.commerce.coinbase.com/charges", json=payload, headers=headers)
    if response.status_code == 201:
        data = response.json()["data"]
        hosted_url = data["hosted_url"]
        bot.send_message(call.message.chat.id, f"🪙 Click below to recharge:
{hosted_url}

Send BTC and we’ll credit your wallet after confirmation.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ Failed to generate invoice. Try again later.")

@bot.callback_query_handler(func=lambda call: call.data == "rchist")
def show_recharge_history(call):
    uid = str(call.from_user.id)
    hist = db.get(uid, {}).get("history", [])
    bot.send_message(call.message.chat.id, "\n".join(hist) if hist else "No recharges yet.")

@bot.callback_query_handler(func=lambda call: call.data == "purchases")
def show_purchases(call):
    uid = str(call.from_user.id)
    buys = db.get(uid, {}).get("purchases", [])
    bot.send_message(call.message.chat.id, "\n".join(buys) if buys else "No purchases yet.")

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    bot.send_message(call.message.chat.id, "📜 Bread Sauce Policy:\n❌ No refunds.\n🪪 Dead CCs not my responsibility.\n🧠 Don’t know how to use it? Don’t shop.\n🔁 One replacement if proven dead on low-end site.\n🚫 No crybaby BS.")

@bot.message_handler(commands=["addproduct"])
def admin_add_product_cmd(message):
    if str(message.from_user.id) in admin_ids:
        show_add_product_panel(bot, message.chat.id, categories)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_add_"))
def admin_product_input(call):
    if str(call.from_user.id) in admin_ids:
        cat = call.data.split("_", 2)[2]
        handle_admin_add_product(bot, call, cat, products)

@bot.message_handler(commands=["removeproduct"])
def admin_remove_product_cmd(message):
    if str(message.from_user.id) in admin_ids:
        show_remove_product_panel(bot, message.chat.id, products)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_rm_"))
def admin_select_category_to_remove(call):
    if str(call.from_user.id) in admin_ids:
        handle_admin_remove_category(bot, call, products)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rm_"))
def admin_confirm_removal(call):
    if str(call.from_user.id) in admin_ids:
        handle_confirm_removal(bot, call, products)

bot.polling()
