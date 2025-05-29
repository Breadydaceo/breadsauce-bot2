
import telebot
from telegram_store_bot import bot, load_data
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    bot.answer_callback_query(call.id)
    data = load_data()

    grouped = {}
    for pid, product in data["products"].items():
        grouped.setdefault(product["category"], []).append((pid, product))

    for category, items in grouped.items():
        msg = f"📦 *{category} Listings:*

"
        for pid, product in items:
            msg += (
                f"💠 *{product['name']}*
"
                f"💵 Price: `{product['price']} BTC`
"
                f"📌 Info revealed after purchase

"
            )

        # Only show the first product’s buttons per category (for display purpose)
        first_pid = items[0][0]
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Buy", callback_data=f"buy_{first_pid}_yes"),
            InlineKeyboardButton("🚫 Cancel", callback_data=f"cancel_{category}")
        )

        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown", reply_markup=kb)
