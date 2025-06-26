from flask import Flask, request
import telegram
import os
import json
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

WEBHOOK_MAP = {
    "A": os.getenv("SHEET_A_WEBHOOK"),
    "B": os.getenv("SHEET_B_WEBHOOK")
}

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message and update.message.text:
        handle_command(update)
    elif update.callback_query:
        handle_callback(update.callback_query)
    return "ok"

def handle_command(update):
    text = update.message.text
    chat_id = update.message.chat_id
    thread_id = update.message.message_thread_id  # ✅ 支援 thread 分頁

    if text.startswith("/draw"):
        parts = text.split()
        if len(parts) == 2 and parts[1] in ["A", "B"]:
            group = parts[1]
            keyboard = [[telegram.InlineKeyboardButton("JOIN", callback_data=f"join_{group}")]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)

            # ✅ 加入 message_thread_id，支援主題分頁
            bot.send_message(
                chat_id=chat_id,
                text=f"🎉 Click to JOIN raffle!",
                reply_markup=reply_markup,
                message_thread_id=thread_id  # 如果是在主題中會正確回傳
            )

def handle_callback(query):
    user_id = query.from_user.id
    username = query.from_user.username or "unknown"
    first_name = query.from_user.first_name or ""
    last_name = query.from_user.last_name or ""
    full_name = (first_name + " " + last_name).strip()
    group = query.data.split("_")[1]
    webhook_url = WEBHOOK_MAP[group]

    payload = {
        "user_id": user_id,
        "username": username,
        "name": full_name
    }

    try:
        r = requests.post(webhook_url, json=payload)
        if r.text.strip() == "duplicate":
            query.answer("Already joined")
        else:
            query.answer("Joined!")
    except Exception as e:
        query.answer("Error: couldn't submit")

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"
