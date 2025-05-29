
import telebot
from telegram_store_bot import bot, load_data, save_data
from transaction_logger import log_transaction

@bot.message_handler(commands=["credit"])
def credit_user(message):
    admin_id = str(message.from_user.id)
    config = load_data()

    if admin_id not in config.get("admin_ids", []):
        bot.send_message(message.chat.id, "🚫 You are not authorized to use this command.")
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError("Invalid format. Usage: /credit @username 0.002")

        _, raw_username, amount_str = parts
        username = raw_username.replace("@", "").strip()
        amount = float(amount_str)

        data = load_data()
        user_id = None

        for uid, info in data["users"].items():
            if info.get("username", "").lower() == username.lower():
                user_id = uid
                break

        if not user_id:
            bot.send_message(message.chat.id, f"❌ User @{username} not found.")
            return

        data["users"][user_id]["balance"] += amount
        save_data(data)

        log_transaction("credit", user_id, username, {
            "amount": amount,
            "credited_by": admin_id
        })

        bot.send_message(message.chat.id, f"✅ Credited `{amount} BTC` to @{username}'s pocket.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Usage: /credit @username 0.002")
        print(f"[ERROR] credit_user: {e}")
