import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from telegram_store_bot import bot

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    bot.answer_callback_query(call.id)

    rules_text = (
        "📜 *Bread Sauce Store Rules*\n\n"
        "1️⃣ All sales are final. Refunds only issued if proof of dead product is submitted.\n"
        "2️⃣ If you don't know how to use it, don't buy it.\n"
        "3️⃣ Chargebacks = banned.\n"
        "4️⃣ BTC deposits must match exact amount requested.\n"
        "5️⃣ Replacement policy: 1 verified dead CC per user, no exceptions.\n"
        "6️⃣ Questions? Contact @BreadSauceSupport\n\n"
        "✅ Use responsibly. Stay under radar. Bread smart."
    )

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")
    )

    bot.send_message(call.message.chat.id, rules_text, parse_mode="Markdown", reply_markup=kb)
