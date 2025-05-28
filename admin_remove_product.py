
from telebot import types

def show_remove_product_panel(bot, chat_id, products):
    markup = types.InlineKeyboardMarkup()
    for category, items in products.items():
        if items:
            markup.add(types.InlineKeyboardButton(f"🗑 Remove from {category}", callback_data=f"admin_rm_{category}"))
    if markup.keyboard:
        bot.send_message(chat_id, "🗂 Select a category to remove a product from:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "📭 No products available to remove.")

def handle_admin_remove_category(bot, call, products):
    cat = call.data.split("_", 2)[2]
    markup = types.InlineKeyboardMarkup()
    for i, item in enumerate(products[cat]):
        markup.add(types.InlineKeyboardButton(f"❌ {item['name']} - {item['price']} BTC", callback_data=f"rm_{cat}_{i}"))
    bot.send_message(call.message.chat.id, f"Select a product to remove from {cat}:", reply_markup=markup)

def handle_confirm_removal(bot, call, products):
    _, cat, idx = call.data.split("_")
    idx = int(idx)
    removed = products[cat].pop(idx)
    bot.send_message(call.message.chat.id, f"✅ Removed '{removed['name']}' from {cat}.")
