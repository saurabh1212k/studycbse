"""
StudyOS – Daily 8 AM Morning Briefing
Netlify Scheduled Function (fires at 02:30 UTC = 08:00 IST daily)
Schedule is defined in netlify.toml under [functions."cron"]
"""

import os
import sys
import json

import telebot

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.db import get_db

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None


def handler(event, context):
    if not bot:
        return {"statusCode": 500, "body": "Bot token not configured"}

    try:
        db    = get_db()
        chaps = db.table("chapters").select("name, scheduled_for").eq("status", "in_progress").execute()

        if not chaps.data:
            return {"statusCode": 200, "body": json.dumps({"status": "ok", "message": "No tasks today"})}

        msg = "🌅 *Good Morning! Here is your Study Plan for today:*\n\n"
        for i, c in enumerate(chaps.data):
            time_str = ""
            if c.get("scheduled_for"):
                try:
                    time_str = " 🕒 " + c["scheduled_for"].split("T")[1][:5]
                except Exception:
                    pass
            msg += f"{i + 1}. {c['name']}{time_str}\n"
        msg += "\n*Let's crush it today!* 🚀"

        users = db.table("users").select("telegram_chat_id").execute()
        sent  = 0
        for u in users.data:
            chat_id = u.get("telegram_chat_id")
            if chat_id:
                try:
                    bot.send_message(chat_id, msg, parse_mode="Markdown")
                    sent += 1
                except Exception:
                    pass

        return {"statusCode": 200, "body": json.dumps({"status": "ok", "sent": sent})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"status": "error", "message": str(e)})}
