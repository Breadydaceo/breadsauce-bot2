import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from telegram_store_bot import bot, load_data

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    bot.answer_callback_query(call.id)
    data = load_data()
    products = data["products"]

    if not products:
        bot.send_message(call.message.chat.id, "⚠️ No products available right now.")
        return

    for pid, product in products.items():
        name = product.get("name")
        category = product.get("category")
        price = product.get("price")
        details = product.get("details", "No details available.")

        text = (
            f"📦 *{name}*\n"
            f"🗂 *Category:* {category}\n"
            f"💸 *Price:* `{price} BTC`\n\n"
            f"{details}"
        )

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ BUY", callback_data=f"buy_{pid}_yes"),
            InlineKeyboardButton("🚫 CANCEL PURCHASE", callback_data="cancel_purchase")
        )

        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_purchase")
def cancel_purchase(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "❌ Purchase canceled. You can keep browsing listings or return to the menu.")