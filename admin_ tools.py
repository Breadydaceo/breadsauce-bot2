import telebot
from telegram_store_bot import bot, load_data, save_data

@bot.message_handler(commands=["credit"])
def credit_user(message):
    admin_id = str(message.from_user.id)

    # Only allow admins
    if admin_id not in load_data().get("admin_ids", []):
        bot.send_message(message.chat.id, "🚫 You are not authorized to use this command.")
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError("Invalid format")

        _, username_raw, amount_str = parts
        username = username_raw.replace("@", "").strip()
        amount = float(amount_str)

        data = load_data()
        user_id = None

        # Find the user ID by username
        for uid, info in data["users"].items():
            if info["username"].lower() == username.lower():
                user_id = uid
                break

        if not user_id:
            bot.send_message(message.chat.id, f"❌ Username @{username} not found.")
            return

        # Credit the balance
        data["users"][user_id]["balance"] += amount
        save_data(data)

        bot.send_message(message.chat.id, f"✅ Credited `{amount} BTC` to @{username}'s pocket.", parse_mode="Markdown")

    except Exception as e:
        print(f"[ERROR] credit_user: {e}")
        bot.send_message(message.chat.id, "❌ Usage: /credit @username 0.002")
