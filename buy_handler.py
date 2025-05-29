
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram_store_bot import bot, load_data, save_data
from transaction_logger import log_transaction

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def confirm_buy(call):
    bot.answer_callback_query(call.id)

    try:
        _, product_id, _ = call.data.split("_")
        data = load_data()
        product = data["products"].get(product_id)

        if not product:
            bot.edit_message_text("❌ Product not found.", call.message.chat.id, call.message.message_id)
            return

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buyfinal_{product_id}_yes"),
            InlineKeyboardButton("🚫 Cancel", callback_data=f"cancel_{product['category']}")
        )
        bot.edit_message_text(
            f"🛍 *{product['name']}*
💰 *{product['price']} BTC*

Do you want to buy this item?",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown", reply_markup=kb
        )

    except Exception as e:
        print(f"[ERROR] confirm_buy: {e}")
        bot.edit_message_text("❌ Something went wrong.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyfinal_"))
def handle_final_buy(call):
    bot.answer_callback_query(call.id)

    try:
        _, product_id, _ = call.data.split("_")
        user_id = str(call.from_user.id)
        username = call.from_user.username or "user"

        data = load_data()
        product = data["products"].get(product_id)

        if not product:
            bot.edit_message_text("❌ Product not found.", call.message.chat.id, call.message.message_id)
            return

        price = float(product["price"])
        user_info = data["users"].setdefault(user_id, {"username": username, "balance": 0.0})
        balance = float(user_info.get("balance", 0.0))

        if balance < price:
            bot.edit_message_text(
                f"🚫 Insufficient balance.
💸 Your balance: `{balance}` BTC",
                call.message.chat.id, call.message.message_id,
                parse_mode="Markdown"
            )
            return

        data["users"][user_id]["balance"] = round(balance - price, 6)
        save_data(data)

        log_transaction("purchase", user_id, username, {
            "product_id": product_id,
            "name": product["name"],
            "category": product["category"],
            "price": price
        })

        details = product.get("details", "❓ No details set for this product.")
        bot.edit_message_text(
            f"✅ *Purchase Successful!*

"
            f"*Product:* {product['name']}
"
            f"*Category:* {product['category']}
"
            f"*Price:* {price} BTC

"
            f"*Delivered Info:*
`{details}`",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown"
        )

    except Exception as e:
        print(f"[ERROR] handle_final_buy: {e}")
        bot.edit_message_text("❌ Failed to complete purchase.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def cancel_purchase(call):
    bot.answer_callback_query(call.id)

    try:
        category = call.data.split("_", 1)[1]
        data = load_data()
        products = [
            f"*{p['name']}* - {p['price']} BTC"
            for p in data["products"].values()
            if p["category"] == category
        ]

        if products:
            text = f"📦 *{category} Products:*

" + "
".join(products)
        else:
            text = f"⚠️ No products available in *{category}*"

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    except Exception as e:
        print(f"[ERROR] cancel_purchase: {e}")
        bot.edit_message_text("❌ Failed to return to category.", call.message.chat.id, call.message.message_id)
