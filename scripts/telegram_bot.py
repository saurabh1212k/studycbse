import os
import sys
import telebot

# Ensure we can import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from services.db import get_db
from services.gemini_service import ask_doubt

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not found in .env")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
db = get_db()

def get_user():
    """Helper to fetch the default user."""
    users = db.table('users').select('*').limit(1).execute()
    if users.data:
        return users.data[0]
    return None

@bot.message_handler(commands=['start'])
def handle_start(message):
    """Links the Telegram chat ID to the Supabase user."""
    chat_id = str(message.chat.id)
    user = get_user()
    
    if not user:
        bot.reply_to(message, "Error: No user found in the database. Please start the app first.")
        return
        
    try:
        # Save chat ID to DB
        db.table('users').update({'telegram_chat_id': chat_id}).eq('id', user['id']).execute()
        
        welcome_text = (
            "🚀 **Welcome to StudyOS Companion!**\n\n"
            "Your Telegram account has been successfully linked to your Supabase database.\n\n"
            "**Commands:**\n"
            "/plan - Get your 'Today's Study Plan'\n"
            "Just text me any question to use the AI Doubt Solver!"
        )
        bot.reply_to(message, welcome_text, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"Database Error: {e}\nDid you run the SQL migration to add telegram_chat_id?")

@bot.message_handler(commands=['plan'])
def handle_plan(message):
    """Fetches 'in_progress' chapters from the database."""
    bot.send_message(message.chat.id, "Fetching your study plan for today...")
    
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
    """Searches for a chapter and adds it to Today's Study Plan."""
    query = message.text.replace('/add', '').strip()
    
    if not query:
        bot.send_message(message.chat.id, "Please provide a chapter name. Example: `/add Light` or `/add Carbon`", parse_mode="Markdown")
        return
        
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Search for chapter by name (case-insensitive partial match)
        search_res = db.table("chapters").select("id, name, subjects(name)").ilike("name", f"%{query}%").limit(1).execute()
        
        if not search_res.data:
            # Not found in CBSE syllabus -> Create as Custom Topic
            users = db.table("users").select("id").limit(1).execute()
            uid = users.data[0]['id']
            
            subs = db.table("subjects").select("id").eq("name", "Custom Topics").execute()
            if subs.data:
                sub_id = subs.data[0]['id']
            else:
                res = db.table("subjects").insert({"name": "Custom Topics", "user_id": uid, "color_hex": "#9ca3af"}).execute()
                sub_id = res.data[0]['id']
                
            db.table("chapters").insert({"subject_id": sub_id, "name": query, "status": "in_progress"}).execute()
            
            bot.send_message(message.chat.id, f"✅ Created custom topic **'{query}'** and added it to Today's Study Plan!", parse_mode="Markdown")
            return
            
        chapter = search_res.data[0]
        sub_name = chapter["subjects"]["name"] if chapter.get("subjects") else "General"
        
        # Update database to set it in_progress
        db.table("chapters").update({"status": "in_progress"}).eq("id", chapter["id"]).execute()
        
        bot.send_message(message.chat.id, f"✅ Successfully added **{sub_name}: {chapter['name']}** to Today's Study Plan!", parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"Database Error: {e}")

@bot.message_handler(func=lambda message: True)
def handle_doubt(message):
    """Passes regular text to Gemini AI Doubt Solver."""
    bot.send_chat_action(message.chat.id, 'typing')
    
    question = message.text
    try:
        # Use our existing Gemini service
        answer = ask_doubt(question, "General")
        
        # Telegram has a 4096 char limit, so we chunk it if necessary
        for i in range(0, len(answer), 4000):
            bot.send_message(message.chat.id, answer[i:i+4000], parse_mode="Markdown")
            
    except Exception as e:
        bot.reply_to(message, "Sorry, my AI brain encountered an error. Please try again.")
        print(f"Gemini Error: {e}")

if __name__ == "__main__":
    print("StudyOS Telegram Companion is running...")
    bot.infinity_polling()
