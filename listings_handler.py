
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from telegram_store_bot import bot, load_data

# Store recent message IDs per user to delete/edit later
user_messages = {}

@bot.callback_query_handler(func=lambda call: call.data == "listings")
def show_listings(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    user_id = str(call.from_user.id)

    data = load_data()
    products = data.get("products", {})

    if not products:
        bot.edit_message_text("⚠️ No products available right now.", chat_id, call.message.message_id)
        return

    # Clear old message if needed
    if user_id in user_messages:
        try:
            bot.delete_message(chat_id, user_messages[user_id])
        except:
            pass

    grouped_text = {}
    product_buttons = {}

    # Group products by category
    for pid, p in products.items():
        category = p.get("category", "Uncategorized")
        name = p.get("name")
        price = p.get("price")
        emoji = "🛍"
        product_line = f"{emoji} *{name}*
💸 *Price:* `{price} BTC`
"

        if category not in grouped_text:
            grouped_text[category] = []
            product_buttons[category] = []

        grouped_text[category].append(product_line)

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ BUY", callback_data=f"buy_{pid}_yes"),
            InlineKeyboardButton("🚫 CANCEL", callback_data="cancel_purchase")
        )
        product_buttons[category].append(kb)

    # Send grouped messages by category
    for category, items in grouped_text.items():
        block = f"📦 *{category} Products:*

" + "
".join(items)
        msg = bot.send_message(chat_id, block, parse_mode="Markdown")
        user_messages[user_id] = msg.message_id

        # Send buttons under each block
        for kb in product_buttons[category]:
            bot.send_message(chat_id, "🛒 Choose an action:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_purchase")
def cancel_purchase(call):
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
