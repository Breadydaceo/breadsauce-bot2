
import telebot
from telegram_store_bot import bot, load_data, save_data
from transaction_logger import log_transaction

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyfinal_"))
def handle_final_buy(call):
    bot.answer_callback_query(call.id)

    try:
        _, product_id, _ = call.data.split("_")
        user_id = str(call.from_user.id)
        username = call.from_user.username or "user"

        data = load_data()
        product = data["products"].pop(product_id, None)  # Remove product after purchase

        if not product:
            bot.edit_message_text("❌ Product not found or already sold.", call.message.chat.id, call.message.message_id)
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
        user_info.setdefault("purchases", []).append(product)

        save_data(data)

        log_transaction("purchase", user_id, username, {
            "product_id": product_id,
            "name": product["name"],
            "category": product["category"],
            "price": price
        })

        details = product.get("details", "❓ No details set for this product.")
        bot.edit_message_text(
            f"✅ *Purchase Complete!*

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
        print(f"[ERROR] auto_expire handle_final_buy: {e}")
        bot.edit_message_text("❌ Failed to process purchase.", call.message.chat.id, call.message.message_id)
