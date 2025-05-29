
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from telegram_store_bot import bot, load_data

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def show_main_menu(call):
    bot.answer_callback_query(call.id)

    user_id = str(call.from_user.id)
    data = load_data()

    username = data["users"].get(user_id, {}).get("username", "unknown")
    balance = data["users"].get(user_id, {}).get("balance", 0)

    welcome = (
        f"👋 Welcome back to *Bread Sauce*, @{username}\n\n"
        f"💼 *Your Info:*\n"
        f"🆔 ID: `{user_id}`\n"
        f"💰 Balance: `{balance} BTC`\n\n"
        "Use the tabs below to start shopping smart 💳"
    )

    kb = InlineKeyboardMarkup(row_width=2)
    menu_buttons = [
        InlineKeyboardButton("💳 Gift Cards", callback_data="cat_Gift Cards"),
        InlineKeyboardButton("🪪 Proz", callback_data="cat_Fullz"),
        InlineKeyboardButton("🧠 BIN Numbers", callback_data="cat_BIN Numbers"),
        InlineKeyboardButton("💼 CCs", callback_data="cat_CCs"),
        InlineKeyboardButton("🔮 Glass", callback_data="cat_Glass"),
        InlineKeyboardButton("💰 Recharge Pocket", callback_data="recharge_menu"),
        InlineKeyboardButton("📂 Listings", callback_data="listings"),
        InlineKeyboardButton("👤 Profile", callback_data="profile"),
        InlineKeyboardButton("📜 Rules", callback_data="rules")
    ]
    kb.add(*menu_buttons)

    bot.send_message(call.message.chat.id, welcome, reply_markup=kb, parse_mode="Markdown")
