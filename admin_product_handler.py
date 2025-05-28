
from telebot import types

# This function should be called inside your /addproduct command handler
def show_add_product_panel(bot, chat_id, categories):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for cat in categories:
        markup.add(types.InlineKeyboardButton(f"➕ Add to {cat}", callback_data=f"admin_add_{cat}"))
    bot.send_message(chat_id, "📦 Select a category to add a product to:", reply_markup=markup)

def handle_admin_add_product(bot, call, category, products):
    msg = bot.send_message(call.message.chat.id, f"Send product details for {category} in this format:\n\nname | price | data")

    @bot.message_handler(func=lambda m: m.chat.id == call.message.chat.id)
    def receive_product_data(message):
        try:
            parts = message.text.split("|")
            if len(parts) < 3:
                raise ValueError
            name, price, data = [x.strip() for x in parts]
            products[category].append({"name": name, "price": float(price), "data": data})
            bot.send_message(message.chat.id, f"✅ Product '{name}' added to {category}.")
        except:
            bot.send_message(message.chat.id, "❌ Invalid format. Please use: name | price | data")
