"""
StudyOS – Telegram Bot Webhook
Netlify Serverless Function (Python)
"""

import os
import sys
import html
import json
from collections import defaultdict

import telebot

# Allow importing from the project root (services/)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from services.db import get_db

# ── Bot init ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False) if BOT_TOKEN else None
db  = get_db()

# ── Subject mapping ───────────────────────────────────────────────────────────
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

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_user():
    res = db.table('users').select('*').limit(1).execute()
    return res.data[0] if res.data else None

def render_book(subject, chapters):
    total   = len(chapters)
    done    = sum(1 for c in chapters if c['status'] == 'completed')
    pending = [c for c in chapters if c['status'] != 'completed']
    pending.sort(key=lambda c: (c.get('chapter_no') is None,
                                c.get('chapter_no') or 0,
                                c['name']))
    name = html.escape(subject['name'])
    if total and not pending:
        return (f"📖 <b>{name}</b>\n\n🎉 All {total} chapters completed! 🏆", None)
    lines  = [f"📖 <b>{name}</b> — {done}/{total} done", ""]
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for c in pending:
        icon = "⏳" if c['status'] == 'in_progress' else "⬜"
        lines.append(f"{icon} {html.escape(c['name'])}")
        markup.add(telebot.types.InlineKeyboardButton(
            f"✅ {c['name']}", callback_data=f"done_{c['id']}"))
    return ("\n".join(lines), markup)

def _safe_answer(call, text):
    try:
        bot.answer_callback_query(call.id, text)
    except Exception:
        pass

def _safe_edit(chat_id, message_id, text, markup):
    try:
        if markup is None:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML")
        else:
            bot.edit_message_text(text, chat_id, message_id,
                                  reply_markup=markup, parse_mode="HTML")
    except Exception:
        try:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass

# ── Callback: tick a chapter done ────────────────────────────────────────────
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

        sub_res  = db.table('subjects').select('id, name').eq('id', chapter['subject_id']).execute()
        chap_res = db.table('chapters').select('id, name, status, chapter_no').eq('subject_id', chapter['subject_id']).execute()
        if sub_res.data and chap_res.data:
            text, markup = render_book(sub_res.data[0], chap_res.data)
            _safe_edit(call.message.chat.id, call.message.message_id, text, markup)
        bot.send_message(call.message.chat.id, f"✅ Marked '{chapter['name']}' as Completed!")
    except Exception as e:
        _safe_answer(call, f"Error: {e}")

# ── /start ────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = str(message.chat.id)
    user = get_user()
    if not user:
        bot.reply_to(message, "Error: No user found. Please open the StudyOS app first.")
        return
    try:
        db.table('users').update({'telegram_chat_id': chat_id}).eq('id', user['id']).execute()
        bot.reply_to(message,
            "🚀 *Welcome to StudyOS Companion!*\n\n"
            "Your Telegram account is securely linked.\n\n"
            "*Commands:*\n"
            "/plan – Today's Study Plan\n"
            "/add [topic] – Add a chapter to Today's Plan\n"
            "/math, /science, /sst, /eng, /hindi – Pending syllabus chapters\n"
            "/donechaps\\_math, /donechaps\\_science, etc. – View completed chapters",
            parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Database Error: {e}")

# ── /plan ─────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=['plan'])
def handle_plan(message):
    try:
        res = db.table("chapters").select("*, subjects(name)").eq("status", "in_progress").execute()
        if not res.data:
            bot.send_message(message.chat.id, "🎉 Your plan is empty! No pending chapters today.")
            return
        text = "📋 *Today's Study Plan:*\n\n"
        for c in res.data:
            sub = c["subjects"]["name"] if c.get("subjects") else "General"
            text += f"🔹 *{sub}*: {c['name']}\n"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

# ── /add ──────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=['add'])
def handle_add(message):
    query = message.text.replace('/add', '').strip()
    if not query:
        bot.send_message(message.chat.id,
                         "Please provide a chapter name. Example: `/add Light`",
                         parse_mode="Markdown")
        return
    try:
        res = db.table("chapters").select("id, name, subjects(name)").ilike("name", f"%{query}%").limit(1).execute()
        if not res.data:
            user = get_user()
            subs = db.table("subjects").select("id").eq("name", "Custom Topics").execute()
            sub_id = subs.data[0]['id'] if subs.data else \
                db.table("subjects").insert({"name": "Custom Topics",
                                             "user_id": user['id'],
                                             "color_hex": "#9ca3af"}).execute().data[0]['id']
            db.table("chapters").insert({"subject_id": sub_id,
                                         "name": query,
                                         "status": "in_progress"}).execute()
            bot.send_message(message.chat.id,
                             f"✅ Created *'{query}'* and added to Today's Plan!",
                             parse_mode="Markdown")
            return
        chap = res.data[0]
        db.table("chapters").update({"status": "in_progress"}).eq("id", chap["id"]).execute()
        bot.send_message(message.chat.id,
                         f"✅ Added *{chap['name']}* to Today's Plan!",
                         parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"Database Error: {e}")

# ── /math /science /sst /eng /hindi ─────────────────────────────────────────
@bot.message_handler(commands=list(SUBJECT_VIEWS.keys()))
def handle_subject(message):
    cmd       = message.text.split('@')[0].lstrip('/').lower()
    sub_names = SUBJECT_VIEWS.get(cmd)
    label     = VIEW_LABELS.get(cmd, f"📚 {cmd}")
    if not sub_names:
        return
    try:
        subs = db.table('subjects').select('id, name').in_('name', sub_names).execute()
        by_name = {s['name']: s for s in subs.data}
        ordered = [by_name[n] for n in sub_names if n in by_name]
        if not ordered:
            bot.send_message(message.chat.id,
                             f"No subjects found for {label}. Set up your curriculum in the StudyOS app first.")
            return
        sub_ids = [s['id'] for s in ordered]
        chaps   = db.table('chapters').select('id, name, status, chapter_no, subject_id') \
                    .in_('subject_id', sub_ids).order('chapter_no').execute()
        grouped = {}
        for c in chaps.data or []:
            grouped.setdefault(c['subject_id'], []).append(c)

        total = sum(len(v) for v in grouped.values())
        done  = sum(1 for v in grouped.values() for c in v if c['status'] == 'completed')
        bot.send_message(message.chat.id,
                         f"{label}\n📊 Overall: {done}/{total} done",
                         parse_mode="Markdown")
        for sub in ordered:
            book_chaps = grouped.get(sub['id'], [])
            text, markup = render_book(sub, book_chaps)
            bot.send_message(message.chat.id, text,
                             reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

# ── /donechaps_* ─────────────────────────────────────────────────────────────
@bot.message_handler(commands=['donechaps_math', 'donechaps_sst', 'donechaps_science',
                                'donechaps_eng', 'donechaps_hindi'])
def handle_donechaps(message):
    cmd       = message.text.split('@')[0].strip('/').replace('donechaps_', '')
    sub_names = SUBJECT_VIEWS.get(cmd)
    label     = VIEW_LABELS.get(cmd, cmd)
    if not sub_names:
        return
    try:
        res = db.table("chapters").select("name, subjects(name)").eq("status", "completed").execute()
        if not res.data:
            bot.send_message(message.chat.id, f"No completed chapters in {label} yet. Keep going! 💪")
            return
        grouped = defaultdict(list)
        for c in res.data:
            s = c["subjects"]["name"] if c.get("subjects") else ""
            if s in sub_names:
                grouped[s].append(c["name"])
        if not grouped:
            bot.send_message(message.chat.id, f"No completed chapters in {label} yet. Keep going! 💪")
            return
        msg = f"✅ *Completed Chapters in {label}:*\n\n"
        for s in sub_names:
            if s in grouped:
                msg += f"📖 *{s}*\n"
                for chap in grouped[s]:
                    msg += f"  • {chap}\n"
                msg += "\n"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Database Error: {e}")

# ── AI Doubt Solver ───────────────────────────────────────────────────────────
@bot.message_handler(func=lambda message: True)
def handle_doubt(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        from services.gemini_service import ask_doubt
        answer = ask_doubt(message.text, "General")
        for i in range(0, len(answer), 4000):
            bot.send_message(message.chat.id, answer[i:i+4000])
    except Exception as e:
        bot.reply_to(message, f"Sorry, my AI brain encountered an error: {e}")

# ── Netlify handler ───────────────────────────────────────────────────────────
def handler(event, context):
    """Netlify invokes this for every incoming HTTP request."""
    if not bot:
        return {"statusCode": 500, "body": "Bot token not configured"}

    method = event.get("httpMethod", "GET")

    # Health-check / root
    if method == "GET":
        return {
            "statusCode": 200,
            "body": "🤖 StudyOS Telegram Bot is alive! Go to /api/set_webhook to activate."
        }

    # Telegram sends POST with JSON update
    if method == "POST":
        content_type = event.get("headers", {}).get("content-type", "")
        if "application/json" in content_type:
            try:
                update = telebot.types.Update.de_json(event.get("body", "{}"))
                bot.process_new_updates([update])
                return {"statusCode": 200, "body": "ok"}
            except Exception as e:
                return {"statusCode": 500, "body": str(e)}

    return {"statusCode": 403, "body": "Forbidden"}
