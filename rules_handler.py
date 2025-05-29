
import telebot
from telegram_store_bot import bot

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def show_rules(call):
    bot.answer_callback_query(call.id)

    rules_msg = (
        "📜 *Store Rules:*

"
        "1. ❌ No Refunds — All sales are final.
"
        "2. 🧠 Know how to use what you’re buying. If you don't, don’t buy.
"
        "3. 💳 Dead cards will *not* be replaced unless proven low-level failed only.
"
        "4. 🔁 You may get *one* replacement if strict proof is provided (screenshots or video).
"
        "5. 🕵️‍♂️ Suspicious activity will trigger bot behavior protection.
"
        "6. 💬 Support: @BreadSauceSupport
"
    )

    bot.edit_message_text(
        rules_msg,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )
