import os
import sys
from flask import Flask, jsonify, request
from telebot import TeleBot
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.db import get_db

app = Flask(__name__)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = TeleBot(BOT_TOKEN, threaded=False)

@app.route('/api/cron', methods=['GET', 'POST'])
def trigger_reminders():
    """
    Triggered by cron-job.org every 5 minutes.
    Checks Supabase for tasks scheduled for right now, and sends a Telegram message.
    """
    try:
        db = get_db()
        
        # 1. Fetch incomplete tasks that are due (scheduled_for <= NOW) and haven't been reminded
        # Supabase Python client doesn't have a direct NOW(), so we compute it in Python
        # or we just query for is_reminded=false and filter in Python to avoid timezone hell.
        # Actually, let's filter in Python for safety, since we might only have a few tasks.
        
        active_chaps = db.table("chapters").select("*, subjects(name, user_id)").eq("status", "in_progress").eq("is_reminded", False).execute()
        
        if not active_chaps.data:
            return jsonify({"status": "ok", "message": "No active tasks need reminding."}), 200
            
        reminded_count = 0
        server_local_now = datetime.datetime.now(datetime.timezone.utc)
        
        for chap in active_chaps.data:
            if not chap.get("scheduled_for"):
                continue
                
            try:
                dt_str = chap["scheduled_for"].replace("Z", "+00:00") if "Z" in chap["scheduled_for"] else chap["scheduled_for"]
                dt_obj = datetime.datetime.fromisoformat(dt_str)
                
                # Make timezone aware if naive
                if dt_obj.tzinfo is None:
                    dt_obj = dt_obj.replace(tzinfo=datetime.timezone.utc)
                    
                # If scheduled time has passed (or is right now)
                if dt_obj <= server_local_now:
                    user_id = chap["subjects"]["user_id"]
                    user_res = db.table("users").select("telegram_chat_id").eq("id", user_id).execute()
                    
                    if user_res.data and user_res.data[0].get("telegram_chat_id"):
                        chat_id = user_res.data[0]["telegram_chat_id"]
                        sub_name = chap["subjects"]["name"]
                        chap_name = chap["name"]
                        
                        msg = f"🔔 **Study Reminder!**\n\nIt's time to study **{sub_name}: {chap_name}**.\n\nOpen StudyOS to start your focus timer!"
                        bot.send_message(chat_id, msg, parse_mode="Markdown")
                        
                        # Mark as reminded
                        db.table("chapters").update({"is_reminded": True}).eq("id", chap["id"]).execute()
                        reminded_count += 1
                        
            except Exception as e:
                print(f"Cron error for {chap['id']}: {e}")
                
        return jsonify({"status": "ok", "reminded": reminded_count}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=3001)
