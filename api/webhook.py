import os
import sys
from flask import Flask, request, jsonify
import telebot

# Ensure we can import our services (Vercel runs from root)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.db import get_db

app = Flask(__name__)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if BOT_TOKEN:
    # IMPORTANT: Vercel kills background threads, so we must run synchronously
    bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
    db = get_db()
else:
    bot = None

def get_user():
    """Helper to fetch the default user."""
    users = db.table('users').select('*').limit(1).execute()
    if users.data:
        return users.data[0]
    return None

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = str(message.chat.id)
    user = get_user()
    if not user:
        bot.reply_to(message, "Error: No user found in the database. Please start the app first.")
        return
    try:
        db.table('users').update({'telegram_chat_id': chat_id}).eq('id', user['id']).execute()
        welcome_text = (
            "🚀 **Welcome to StudyOS Companion!**\n\n"
            "Your Telegram account is securely linked (Vercel Edition).\n\n"
            "**Commands:**\n"
            "/plan - Get your 'Today's Study Plan'\n"
            "/add [topic] - Add a chapter to Today's Plan\n"
            "/math, /science, /sst, /eng, /hindi - View & complete syllabus"
        )
        bot.reply_to(message, welcome_text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Database Error: {e}")

@bot.message_handler(commands=['plan'])
def handle_plan(message):
    try:
        active_chaps = db.table("chapters").select("*, subjects(name)").eq("status", "in_progress").execute()
        if not active_chaps.data:
            bot.send_message(message.chat.id, "🎉 Your plan is empty! You have no pending chapters today.")
            return
        plan_text = "📋 **Today's Study Plan:**\n\n"
        for chap in active_chaps.data:
            sub_name = chap["subjects"]["name"] if chap.get("subjects") else "General"
            plan_text += f"🔹 *{sub_name}*: {chap['name']}\n"
        bot.send_message(message.chat.id, plan_text, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error fetching plan: {e}")

@bot.message_handler(commands=['add'])
def handle_add(message):
    query = message.text.replace('/add', '').strip()
    if not query:
        bot.send_message(message.chat.id, "Please provide a chapter name. Example: `/add Light`", parse_mode="Markdown")
        return
    try:
        search_res = db.table("chapters").select("id, name, subjects(name)").ilike("name", f"%{query}%").limit(1).execute()
        if not search_res.data:
            user = get_user()
            subs = db.table("subjects").select("id").eq("name", "Custom Topics").execute()
            if subs.data:
                sub_id = subs.data[0]['id']
            else:
                res = db.table("subjects").insert({"name": "Custom Topics", "user_id": user['id'], "color_hex": "#9ca3af"}).execute()
                sub_id = res.data[0]['id']
            db.table("chapters").insert({"subject_id": sub_id, "name": query, "status": "in_progress"}).execute()
            bot.send_message(message.chat.id, f"✅ Created custom topic **'{query}'** and added it to Today's Study Plan!", parse_mode="Markdown")
            return
            
        chapter = search_res.data[0]
        sub_name = chapter["subjects"]["name"] if chapter.get("subjects") else "General"
        db.table("chapters").update({"status": "in_progress"}).eq("id", chapter["id"]).execute()
        bot.send_message(message.chat.id, f"✅ Successfully added **{sub_name}: {chapter['name']}** to Today's Study Plan!", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"Database Error: {e}")

@bot.message_handler(commands=['math', 'eng', 'hindi', 'sst', 'science'])
def handle_subject_tags(message):
    cmd = message.text.split()[0].lower()
    
    # Map commands to actual database subject names
    if cmd == '/math':
        query = ['Mathematics']
    elif cmd == '/science':
        query = ['Physics', 'Chemistry', 'Biology']
    elif cmd == '/sst':
        query = ['History', 'Geography', 'Civics', 'Economics']
    elif cmd == '/eng':
        query = ['Eng: First Flight', 'Eng: Footprints Without Feet']
    elif cmd == '/hindi':
        query = ['Hindi: Kshitij', 'Hindi: Kritika']
    else:
        return
        
    try:
        # Fetch all subjects to get their IDs
        subs = db.table('subjects').select('id, name').execute()
        target_sub_ids = [s['id'] for s in subs.data if any(q in s['name'] for q in query)]
        
        if not target_sub_ids:
            bot.send_message(message.chat.id, f"No subjects found for {cmd}.")
            return
            
        # Fetch pending chapters for those subjects
        chapters = db.table('chapters').select('id, name').in_('subject_id', target_sub_ids).neq('status', 'completed').execute()
        
        if not chapters.data:
            bot.send_message(message.chat.id, f"🎉 You have no pending chapters in {cmd}! Everything is completed.")
            return
            
        # Build Inline Keyboard with Tick Boxes
        markup = telebot.types.InlineKeyboardMarkup()
        for chap in chapters.data:
            btn = telebot.types.InlineKeyboardButton(f"⬜ {chap['name']}", callback_data=f"done_{chap['id']}")
            markup.add(btn)
            
        bot.send_message(message.chat.id, f"📚 **Pending Syllabus for {cmd}**\nClick a box to mark it as Completed:", reply_markup=markup, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('done_'))
def handle_complete_callback(call):
    chap_id = call.data.split('_')[1]
    try:
        # Mark as completed in DB
        db.table('chapters').update({'status': 'completed'}).eq('id', chap_id).execute()
        
        # Fetch chapter name for the confirmation message
        chap = db.table('chapters').select('name').eq('id', chap_id).execute()
        chap_name = chap.data[0]['name'] if chap.data else "Chapter"
        
        # Answer the callback so the loading spinner on the button stops
        bot.answer_callback_query(call.id, "Marked as Completed! 🎉")
        
        # Send a confirmation message
        bot.send_message(call.message.chat.id, f"✅ Marked **{chap_name}** as Completed!", parse_mode="Markdown")
        
        # Note: We don't delete the big button list so they can keep checking off other chapters!
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {e}")


# --- VERCEL WEBHOOK ROUTES ---

@app.route('/api/webhook', methods=['POST'])
def webhook():
    """Receives updates from Telegram and passes them to the bot."""
    if not bot:
        return "Bot not configured", 500
        
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return jsonify({"error": "unsupported type"}), 403

@app.route('/api/set_webhook', methods=['GET'])
def set_webhook():
    """Run this once in your browser after deploying to Vercel to link the bot."""
    if not bot:
        return "Bot not configured", 500
        
    url = f"https://{request.host}/api/webhook"
    bot.remove_webhook()
    success = bot.set_webhook(url=url)
    
    if success:
        return f"✅ Webhook successfully set to: {url}"
    else:
        return "❌ Failed to set webhook", 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return "🤖 StudyOS Telegram Bot is alive and running on Vercel! To activate it, go to /api/set_webhook"

# Vercel requires the app variable to be exposed
if __name__ == '__main__':
    app.run(debug=True)
