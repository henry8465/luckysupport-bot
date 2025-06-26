from flask import Flask, request
import telegram
import os
import json
import requests

# 初始化 Telegram Bot
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telegram.Bot(token=TOKEN)

# 建立 Flask 應用
app = Flask(__name__)

# webhook 對應群組 A / B
WEBHOOK_MAP = {
    "A": os.getenv("SHEET_A_WEBHOOK"),
    "B": os.getenv("SHEET_B_WEBHOOK")
}

# 已點擊的使用者記錄
joined_users = {
    "A": set(),
    "B": set()
}

# 處理 Telegram webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message and update.message.text:
        handle_command(update)
    elif update.callback_query:
        handle_callback(update.callback_query)
    return "ok"

# 處理 /draw 指令，發送 JOIN 按鈕
def handle_command(update):
    text = update.message.text
    chat_id = update.message.chat_id
    if text.startswith("/draw"):
        parts = text.split()
        if len(parts) == 2 and parts[1] in ["A", "B"]:
            group = parts[1]
            keyboard = [[telegram.InlineKeyboardButton("JOIN", callback_data=f"join_{group}")]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id=chat_id, text=f"🎉 Click JOIN raffle!", reply_markup=reply_markup)

# 處理按鈕點擊與 webhook 傳送
def handle_callback(query):
    user_id = query.from_user.id
    username = query.from_user.username or "unknown"
    group = query.data.split("_")[1]

    if user_id in joined_users[group]:
        query.answer("Already joined")
    else:
        joined_users[group].add(user_id)
        webhook_url = WEBHOOK_MAP[group]
        payload = {
            "user_id": user_id,
            "username": username
        }
        try:
            requests.post(webhook_url, json=payload)
        except Exception as e:
            print("Failed to send to webhook:", e)
        query.answer("Joined!")
    return
