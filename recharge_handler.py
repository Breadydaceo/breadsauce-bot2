
import telebot
import json
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram_store_bot import bot, load_data

# Load recharge tiers
RECHARGE_OPTIONS = {
    "BTC": [25, 50, 100, 200, 300, 500, 1000],
    "LTC": [25, 50, 100, 200, 300, 500, 1000]
}

SELLY_API_KEY = "RcpAoDayA-RgLcDXtx3L4j586H3zv7LrZmX11s4sPZKBD-9noafSVrbVUHwvTmCq"

@bot.callback_query_handler(func=lambda call: call.data == "recharge_menu")
def show_recharge_menu(call):
    bot.answer_callback_query(call.id)
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Bitcoin (BTC)", callback_data="recharge_BTC"),
        InlineKeyboardButton("💰 Litecoin (LTC)", callback_data="recharge_LTC"),
        InlineKeyboardButton("🏠 Back", callback_data="main_menu")
    )
    bot.edit_message_text("🔌 Choose a payment method:", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_") and len(call.data.split("_")) == 2)
def show_recharge_tiers(call):
    bot.answer_callback_query(call.id)
    method = call.data.split("_")[1]
    kb = InlineKeyboardMarkup(row_width=3)
    for amount in RECHARGE_OPTIONS[method]:
        kb.add(InlineKeyboardButton(f"${amount}", callback_data=f"createinvoice_{method}_{amount}"))
    kb.add(InlineKeyboardButton("⬅️ Back", callback_data="recharge_menu"))
    bot.edit_message_text(f"💵 Select amount to recharge with {method}:", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("createinvoice_"))
def create_invoice(call):
    bot.answer_callback_query(call.id)
    _, method, usd = call.data.split("_")
    usd = int(usd)
    user_id = str(call.from_user.id)

    headers = {
        "Authorization": f"Bearer {SELLY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "title": f"{method} Recharge",
        "currency": "USD",
        "email": f"{user_id}@breadsauce.io",
        "value": usd,
        "gateway": method.lower()
    }

    response = requests.post("https://api.selly.io/v2/invoices", headers=headers, json=payload)

    if response.status_code == 201:
        invoice = response.json()
        pay = invoice["payment"]
        msg = (
            f"🔌 *Recharge Pocket*

"
            f"💳 *Payment Method:* {method}
"
            f"📥 *Address:* `{pay['address']}`
"
            f"💸 *Amount:* `{pay['amount']}` {method}
"
            f"🧾 *USD:* ${usd}
"
            f"⏳ *Expires in:* {pay['timeout']} minutes

"
            f"⚠️ Send the exact amount. Manual balance update will follow after confirmation."
        )
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "❌ Error creating invoice. Try again later.")
