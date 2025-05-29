from telegram_store_bot import bot
import recharge_handler
import buy_handler
import profile_handler
import listings_handler
import rules_handler
import main_menu_handler

# Start polling
if __name__ == "__main__":
    bot.polling(none_stop=True)
