import telebot
import json
import requests
import uuid
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

    # Load configuration
    with open("bot_config.json") as config_file:
        config = json.load(config_file)

    TOKEN = config["telegram_bot_token"]
    ADMIN_IDS = config["admin_ids"]
    CATEGORIES = config["categories"]
    DATABASE_PATH = config["database"]["path"]
    SELLY_API_KEY = config["selly_api_key"]

    bot = telebot.TeleBot(TOKEN)
    bot.remove_webhook()

    try:
        with open(DATABASE_PATH) as db_file:
            data = json.load(db_file)
    except FileNotFoundError:
        data = {"products": {}, "users": {}, "recharge_requests": {}}

    def save_data():
        with open(DATABASE_PATH, "w") as db_file:
            json.dump(data, db_file, indent=2)

    def main_menu():
        kb = InlineKeyboardMarkup(row_width=3)
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

    @bot.message_handler(commands=["start"])
    def send_welcome(message):
        user_id = str(message.from_user.id)
        username = message.from_user.username or "User"
        data["users"].setdefault(user_id, {"username": username, "balance": 0})
        save_data()

        welcome = (
            f"👋 Welcome back to *Bread Sauce*, @{username}\\n\\n"
            "Tap below to start shopping smart 💳\\n\\n"
            "📞 *Support:* @BreadSauceSupport\\n"
            "`Account → Recharge → Listings → Buy`\\n\\n"
            "⚠️ *BTC recharges are updated within 10 minutes.*\\n"
            "Your balance will be credited manually.\\n\\n"
            "🤖 *Note:* Suspicious behavior may trigger bot lock."
        )
        bot.send_message(message.chat.id, welcome, reply_markup=main_menu(), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
    def show_products(call):
        category = call.data.split("_", 1)[1]
        found = False
        for pid, prod in data["products"].items():
            if prod["category"].lower() == category.lower():
                kb = InlineKeyboardMarkup(row_width=3)
                kb.add(
                    InlineKeyboardButton("✅ Buy", callback_data=f"buy_{pid}"),
                    InlineKeyboardButton("🚫 Cancel", callback_data="main_menu"),
                    InlineKeyboardButton("🔙 Back", callback_data="listings")
                )
                text = f"*🛍 {prod['name']}*\\n💸 *Price:* {prod['price']} BTC"
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
                found = True
                break
        if not found:
            bot.answer_callback_query(call.id, "No products available.", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
    def buy_product(call):
        user_id = str(call.from_user.id)
        pid = call.data.split("_", 1)[1]

        if pid not in data["products"]:
            bot.answer_callback_query(call.id, "❌ Product not found.", show_alert=True)
            return

        product = data["products"][pid]
        balance = data["users"].get(user_id, {}).get("balance", 0)

        if balance < float(product["price"]):
            bot.answer_callback_query(call.id, "❌ Insufficient balance.", show_alert=True)
            return

        # Deduct + expire product
        data["users"][user_id]["balance"] -= float(product["price"])
        product_info = product.get("info", "No info available.")
        del data["products"][pid]
        save_data()

        bot.edit_message_text(
            f"✅ *Purchase Complete!*\\n\\n📦 *{product['name']}*\\n💳 *Info:* `{product_info}`",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data == "profile")
    def show_profile(call):
        user_id = str(call.from_user.id)
        user = data["users"].get(user_id, {"username": "Unknown", "balance": 0})
        text = f"👤 *Your Profile*\\n\\n🪪 *User:* @{user['username']}\\n💰 *Balance:* {user['balance']:.8f} BTC"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data == "recharge")
    def recharge_menu(call):
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("₿ $25 BTC", callback_data="recharge_btc_25"),
            InlineKeyboardButton("₿ $50 BTC", callback_data="recharge_btc_50"),
            InlineKeyboardButton("₿ $100 BTC", callback_data="recharge_btc_100"),
            InlineKeyboardButton("🪙 $25 LTC", callback_data="recharge_ltc_25"),
            InlineKeyboardButton("🪙 $50 LTC", callback_data="recharge_ltc_50"),
            InlineKeyboardButton("🔙 Back", callback_data="main_menu")
        )
        bot.edit_message_text("💳 *Choose your recharge method and amount:*", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
    def generate_invoice(call):
        _, gateway, amount = call.data.split("_")
        user_id = str(call.from_user.id)

        payload = {
            "title": f"Bread Sauce Recharge: ${amount}",
            "payment_gateway": gateway,
            "currency": "USD",
            "value": float(amount),
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

        if response.ok:
            invoice = response.json()
            url = invoice.get("payment_redirection_url", "No URL")
            data["recharge_requests"][str(uuid.uuid4())] = {"user_id": user_id, "amount": amount, "gateway": gateway}
            save_data()
            bot.edit_message_text(
                f"💸 *Invoice Generated:*\\nSend payment using the button below.\\n\\n🔗 {url}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "❌ Could not generate invoice.", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data == "rules")
    def show_rules(call):
        rules = (
            "📜 *Store Rules:*\\n\\n"
            "1. ❌ No refunds. All sales final.\\n"
            "2. 🧠 Know what you’re buying.\\n"
            "3. 🛡️ Replacements only with proof (low-end fails).\\n"
            "4. 🔁 One replacement per customer.\\n"
            "5. 🤖 Bot detects suspicious activity.\\n\\n"
            "📞 *Support:* @BreadSauceSupport"
        )
        bot.edit_message_text(rules, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data == "listings")
    def show_listings(call):
        summaries = {}
        for prod in data["products"].values():
            summaries.setdefault(prod["category"], []).append(prod)

        msg = ""
        for cat, items in summaries.items():
            msg += f"*{cat} Products:*\\n"
            for prod in items:
                msg += f"🛍️ {prod['name']}\\n💸 Price: {prod['price']} BTC\\n\\n"

        bot.edit_message_text(msg or "📦 No listings available.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data == "main_menu")
    def return_to_main(call):
        bot.edit_message_text("🏠 *Main Menu:*", call.message.chat.id, call.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")

    @bot.message_handler(commands=["credit"])
    def admin_credit_user(message):
        if str(message.from_user.id) not in ADMIN_IDS:
            return

        try:
            _, uid, amount = message.text.split()
            data["users"].setdefault(uid, {"username": "Unknown", "balance": 0})
            data["users"][uid]["balance"] += float(amount)
            save_data()
            bot.reply_to(message, f"✅ Credited {amount} BTC to user ID {uid}")
        except:
            bot.reply_to(message, "❌ Usage: /credit USER_ID AMOUNT")

    @bot.message_handler(commands=["recharge_log"])
    def view_recharge_logs(message):
        if str(message.from_user.id) not in ADMIN_IDS:
            return
        logs = data.get("recharge_requests", {})
        output = "*Recharge Requests:*\n\n"
        for k, entry in logs.items():
            output += f"🧾 {entry['user_id']} → ${entry['amount']} via {entry['gateway']}\\n"
        bot.reply_to(message, output or "None logged yet.", parse_mode="Markdown")

    bot.polling()
