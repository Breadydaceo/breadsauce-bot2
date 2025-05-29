import telebot
import json
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from telegram_store_bot import bot, load_data, save_data

# Load recharge tiers
with open("recharge_options.json") as f:
    RECHARGE_OPTIONS = json.load(f)

# Your Selly API Key
SELLY_API_KEY = "RcpAoDayA-RgLcDXtx3L4j586H3zv7LrZmX11s4sPZKBD-9noafSVrbVUHwvTmCq"

# Recharge menu callback
@bot.callback_query_handler(func=lambda call: call.data == "recharge_menu")
def handle_recharge_menu(call):
    bot.answer_callback_query(call.id)
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Bitcoin (BTC)", callback_data="recharge_crypto_BTC"),
        InlineKeyboardButton("💰 Litecoin (LTC)", callback_data="recharge_crypto_LTC"),
        InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu")
    )
    bot.send_message(call.message.chat.id, "🔌 Choose a recharge method:", reply_markup=kb)

# Crypto method selection (BTC/LTC)
@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_crypto_"))
def handle_crypto_type(call):
    bot.answer_callback_query(call.id)
    crypto = call.data.split("_")[-1]
    kb = InlineKeyboardMarkup(row_width=3)
    for option in RECHARGE_OPTIONS[crypto]:
        usd = option["usd"]
        label = f"${usd}"
        kb.add(InlineKeyboardButton(label, callback_data=f"create_invoice_{crypto}_{usd}"))
    kb.add(InlineKeyboardButton("⬅️ Back", callback_data="recharge_menu"))
    bot.send_message(call.message.chat.id, f"💵 Select a recharge amount in {crypto}:", reply_markup=kb)

# Invoice creation handler
@bot.callback_query_handler(func=lambda call: call.data.startswith("create_invoice_"))
def handle_create_invoice(call):
    bot.answer_callback_query(call.id)
    _, crypto, usd = call.data.split("_")
    usd = int(usd)
    user_id = str(call.from_user.id)

    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "title": f"{crypto} Recharge - Bread Sauce",
        "currency": "USD",
        "email": f"{user_id}@breadsauce.io",  # fake email for tracking
        "value": usd,
        "gateway": crypto.lower()
    }

    response = requests.post("https://api.selly.io/v2/invoices", headers=headers, json=payload)

    if response.status_code == 201:
        invoice = response.json()
        address = invoice["payment"]["address"]
        amount = invoice["payment"]["amount"]
        currency = invoice["payment"]["crypto_currency"]
        expires = invoice["payment"]["timeout"]

        msg = (
            f"🔌 *Recharge Pocket*\n\n"
            f"💳 *Payment Method:* {currency}\n"
            f"📥 *Address:* `{address}`\n"
            f"💸 *Amount:* `{amount}` {currency}\n"
            f"🧾 *USD Value:* ${usd}\n"
            f"⏳ *Expires in:* {expires} minutes\n\n"
            f"⚠️ Send exact amount. After payment, balance will be updated manually."
        )
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "❌ Error creating invoice. Try again later.")