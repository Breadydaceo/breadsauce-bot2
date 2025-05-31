import telebot

# Your bot token
TOKEN = "8032004385:AAEyYPljNDvah5WxWNHurmYTq9WXSwBg8FY"

bot = telebot.TeleBot(TOKEN)

# Remove the webhook
bot.remove_webhook()
print("✅ Webhook removed. You can now use polling.")
