import os
import sys
import html

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

# ------------------------------------------------------------------
# Book-wise syllabus views
# Each command maps to an ordered list of subjects (books) from the DB.
# ------------------------------------------------------------------

SUBJECT_VIEWS = {
    'math':    ['Mathematics'],
    'science': ['Physics', 'Chemistry', 'Biology'],
    'sst':     ['History', 'Geography', 'Civics', 'Economics'],
    'eng':     ['Eng: First Flight', 'Eng: Footprints Without Feet'],
    'hindi':   ['Hindi: Kshitij', 'Hindi: Kritika'],
}

VIEW_LABELS = {
    'math':    '📐 Mathematics',
    'science': '🔬 Science',
    'sst':     '🌐 Social Science',
    'eng':     '📗 English',
    'hindi':   '📕 Hindi',
}

def render_book(subject: dict, chapters: list):
    """Build one book's message: progress header + a tick-box per pending chapter.

    Returns (text, markup). markup is None when every chapter is completed.
    Completed chapters drop off the list; the header count tracks overall progress.
    """
    total = len(chapters)
    done = sum(1 for c in chapters if c['status'] == 'completed')
    pending = [c for c in chapters if c['status'] != 'completed']
    # Chapter number order first, then unnumbered ones alphabetically
    pending.sort(key=lambda c: (c.get('chapter_no') is None, c.get('chapter_no') or 0, c['name']))

    name = html.escape(subject['name'])
    if total and not pending:
        return f"📖 <b>{name}</b>\n\n🎉 All {total} chapters completed! Outstanding! 🏆", None

    lines = [f"📖 <b>{name}</b> — {done}/{total} done", ""]
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for c in pending:
        icon = "⏳" if c['status'] == 'in_progress' else "⬜"
        lines.append(f"{icon} {html.escape(c['name'])}")
        markup.add(telebot.types.InlineKeyboardButton(
            f"{icon} {c['name']}",
            callback_data=f"done_{c['id']}",
        ))
    lines.append("")
    lines.append("👇 Tap a chapter to mark it completed")
    return "\n".join(lines), markup

@bot.message_handler(commands=list(SUBJECT_VIEWS.keys()))
def handle_subject(message):
    cmd = message.text.split()[0].lstrip('/').lower()
    book_names = SUBJECT_VIEWS.get(cmd)
    if not book_names:
        return
    label = VIEW_LABELS.get(cmd, f"📚 {cmd}")
    try:
        # Fetch the books for this command, preserving our defined order
        subs = db.table('subjects').select('id, name').in_('name', book_names).execute()
        by_name = {s['name']: s for s in subs.data}
        ordered = [by_name[n] for n in book_names if n in by_name]
        if not ordered:
            bot.send_message(
                message.chat.id,
                f"🤔 No subjects found for {label}.\nRun the curriculum setup in the StudyOS app first.",
            )
            return

        # One query for all books, then group chapters by subject
        sub_ids = [s['id'] for s in ordered]
        chaps = db.table('chapters').select('id, name, status, chapter_no, subject_id') \
            .in_('subject_id', sub_ids).order('chapter_no').execute()
        grouped = {}
        for c in chaps.data or []:
            grouped.setdefault(c['subject_id'], []).append(c)

        total = sum(len(v) for v in grouped.values())
        done = sum(1 for v in grouped.values() for c in v if c['status'] == 'completed')
        bot.send_message(
            message.chat.id,
            f"{label} — *{done}/{total}* chapters done\nTap a chapter to mark it ✅ completed:",
            parse_mode="Markdown",
        )

        # One message per book, each with its own tick-boxes
        for sub in ordered:
            text, markup = render_book(sub, grouped.get(sub['id'], []))
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

def _safe_answer(call, text: str):
    """Answer the callback toast; never let a stale/expired query crash the handler."""
    try:
        bot.answer_callback_query(call.id, text)
    except Exception:
        pass  # query too old (>15s) or invalid -> Telegram only needs HTTP 200 anyway


def _safe_edit(chat_id, message_id, text, markup):
    """Edit the book message in place; degrade gracefully when Telegram refuses."""
    try:
        if markup is None:
            bot.edit_message_text(text, chat_id, message_id)
        else:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    except Exception:
        # "message is not modified" / message too old to edit -> send fresh instead
        try:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            return  # channel dead (user blocked bot, etc.) - nothing more we can do


@bot.callback_query_handler(func=lambda call: call.data.startswith('done_'))
def handle_complete_callback(call):
    chap_id = call.data.split('_', 1)[1]
    try:
        res = db.table('chapters').select('id, name, subject_id, status').eq('id', chap_id).execute()
        if not res.data:
            _safe_answer(call, "Chapter not found!")
            return
        chapter = res.data[0]

        if chapter['status'] != 'completed':
            db.table('chapters').update({'status': 'completed'}).eq('id', chap_id).execute()
        _safe_answer(call, f"✅ {chapter['name']} completed! 🎉")

        # Re-render the book this chapter belongs to, editing the SAME message,
        # so the tick-boxes always reflect reality (no stale lists piling up).
        sub_res = db.table('subjects').select('id, name').eq('id', chapter['subject_id']).execute()
        if sub_res.data:
            chaps = db.table('chapters').select('id, name, status, chapter_no') \
                .eq('subject_id', chapter['subject_id']).order('chapter_no').execute()
            text, markup = render_book(sub_res.data[0], chaps.data or [])
            if call.message:
                _safe_edit(call.message.chat.id, call.message.message_id, text, markup)
                return

        bot.send_message(call.message.chat.id, f"✅ Marked '{chapter['name']}' as Completed!")
    except Exception as e:
        _safe_answer(call, f"Error: {e}")

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
            "Your Telegram account is securely linked.\n\n"
            "**Commands:**\n"
            "/plan - Get your 'Today's Study Plan'\n"
            "/add [topic] - Add a chapter to Today's Plan\n"
            "/mid - View Midterm Marathon Syllabus\n"
            "/math, /science, /sst, /eng, /hindi - Syllabus book-wise (tap a chapter to complete it)"
        )
        bot.reply_to(message, welcome_text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Database Error: {e}")

@bot.message_handler(commands=['mid'])
def handle_midterm(message):
    midterm_text = (
        "🔥 **Midterm Marathon Timetable (Sep 5 - 16)**\n\n"
        "📅 **Sep 5-6**\n📐 Maths: Ch 7, 14, 6 (PYQ Practice)\n\n"
        "📅 **Sep 7**\n📊 Economics: Ch 1, 2\n\n"
        "📅 **Sep 8**\n🧬 Biology: Whole Biology Revision\n\n"
        "📅 **Sep 9**\n🌍 Geography: Whole Geography Revision\n\n"
        "📅 **Sep 10**\n🏛️ Civics & 📐 Maths: Civics Ch 3 + Start Trigonometry\n\n"
        "📅 **Sep 11**\n📐 Maths: Trigonometry\n\n"
        "📅 **Sep 12-13**\n🏛️ Civics & 📐 Maths: Civics Ch 1-3, Maths Ch 1-3\n\n"
        "📅 **Sep 14-15**\n🧪 Chem & 📜 History: Chem Ch 1-2, History Ch 1-2\n\n"
        "📅 **Sep 16**\n⚡ Physics: Ch 1, 2\n\n"
        "🚀 *Let's crush this midterm!*"
    )
    bot.send_message(message.chat.id, midterm_text, parse_mode="Markdown")

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

@bot.message_handler(func=lambda message: True)
def handle_fallback(message):
    """Catch-all: helpful hint instead of the removed AI doubt solver."""
    bot.reply_to(
        message,
        "🤖 I didn't catch that. Try one of my commands:\n\n"
        "/plan - Today's Study Plan\n"
        "/add [topic] - Add a chapter to Today's Plan\n"
        "/mid - Midterm Marathon Syllabus\n"
        "/math, /science, /sst, /eng, /hindi - Syllabus book-wise",
    )

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

@app.route('/api/cron', methods=['GET', 'POST'])
def daily_briefing():
    try:
        from datetime import date
        today = date.today().isoformat()

        # We fetch all tasks in progress or scheduled for today
        chaps = get_db().table("chapters").select("name, scheduled_for").eq("status", "in_progress").execute()

        if not chaps.data:
            return jsonify({"status": "ok", "message": "No tasks for today"})

        msg = f"🌅 **Good Morning! Here is your Study Plan for today:**\n\n"
        for i, c in enumerate(chaps.data):
            time_str = ""
            if c.get("scheduled_for"):
                try:
                    time_str = " 🕒 " + c["scheduled_for"].split("T")[1][:5]
                except:
                    pass
            msg += f"{i+1}. {c['name']}{time_str}\n"

        msg += "\n*Let's crush it today!* 🚀"

        # /start stores each user's telegram_chat_id in the users table,
        # so we can push the briefing to every linked chat.
        users = get_db().table("users").select("telegram_chat_id").execute()
        sent = 0
        for u in users.data:
            chat_id = u.get("telegram_chat_id")
            if chat_id:
                try:
                    bot.send_message(chat_id, msg, parse_mode="Markdown")
                    sent += 1
                except:
                    pass

        return jsonify({"status": "ok", "message": f"Briefing sent to {sent} users"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return "🤖 StudyOS Telegram Bot is alive! To activate the webhook, go to /api/set_webhook"

# Vercel requires the app variable to be exposed
if __name__ == '__main__':
    app.run(debug=True)
