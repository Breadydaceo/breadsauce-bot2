
import telebot
from telegram_store_bot import bot, load_data

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    username = call.from_user.username or "user"

    data = load_data()
    user_info = data["users"].get(user_id, {"username": username, "balance": 0.0, "purchases": []})
    balance = user_info.get("balance", 0.0)
    purchases = user_info.get("purchases", [])

    total_purchases = len(purchases)
    last_purchase = purchases[-1]["name"] if purchases else "None"

    profile_msg = (
        f"👤 *User Profile*

"
        f"🆔 Username: @{username}
"
        f"🪙 Balance: `{balance} BTC`
"
        f"🛒 Total Purchases: `{total_purchases}`
"
        f"🧾 Last Purchase: *{last_purchase}*"
    )

    bot.edit_message_text(
        profile_msg,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )
