
from bot_config import ADMIN_IDS
from telebot.types import Message
import json

# Load and save data
with open("bot_config.json") as config_file:
    config = json.load(config_file)

DATA_PATH = config["database"]["path"]
try:
    with open(DATA_PATH) as db_file:
        data = json.load(db_file)
except FileNotFoundError:
    data = {"products": {}, "users": {}}

def save_data():
    with open(DATA_PATH, "w") as db_file:
        json.dump(data, db_file, indent=2)

def add_product(product_id, name, category, price):
    data["products"][product_id] = {
        "name": name,
        "category": category,
        "price": price
    }
    save_data()

# Handler function to plug into main bot
def handle_add_product_command(bot):

    @bot.message_handler(commands=["addproduct"])
    def start_add_product(message: Message):
        if str(message.from_user.id) not in ADMIN_IDS:
            return bot.send_message(message.chat.id, "🚫 Not authorized.")
        msg = bot.send_message(message.chat.id, "Send product in format:

Name | Category | Price")
        bot.register_next_step_handler(msg, lambda m: complete_add_product(bot, m))

def complete_add_product(bot, message: Message):
    try:
        name, category, price = [x.strip() for x in message.text.split("|")]
        with open(DATA_PATH) as db_file:
            data = json.load(db_file)
        pid = str(len(data["products"]) + 1)
        add_product(pid, name, category, price)
        bot.send_message(message.chat.id, f"✅ *{name}* added to *{category}* for *{price} BTC*.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error adding product: {e}")
