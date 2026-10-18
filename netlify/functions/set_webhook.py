"""
StudyOS – Set Webhook
Netlify Function: visit /api/set_webhook in your browser after deploying.
"""

import os
import sys

import telebot

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None


def handler(event, context):
    if not bot:
        return {"statusCode": 500, "body": "TELEGRAM_BOT_TOKEN not set."}

    # Derive the base URL from the incoming request host
    headers = event.get("headers", {})
    host = headers.get("host", "")
    url = f"https://{host}/api/webhook"

    bot.remove_webhook()
    success = bot.set_webhook(url=url)

    if success:
        return {"statusCode": 200, "body": f"✅ Webhook set to: {url}"}
    else:
        return {"statusCode": 500, "body": "❌ Failed to set webhook. Check your bot token."}
