"""
StudyOS - Local Telegram Bot Runner
Runs the bot with long polling on your own machine.
Use this when the Vercel deployment is disabled/paused (402) or for development.

Usage:
    .venv/Scripts/python.exe scripts/run_bot.py

Stop with Ctrl+C. While this runs, remove_webhook() ensures Telegram delivers
updates HERE and not to the (dead) Vercel webhook. To go back to Vercel later,
visit https://<your-app>.vercel.app/api/set_webhook once it's redeployed.
"""
import os
import sys
import time

# Windows consoles default to cp1252 and crash on emoji prints
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("TELEGRAM_BOT_TOKEN"):
    print("❌ TELEGRAM_BOT_TOKEN missing from .env")
    sys.exit(1)

# Importing api/webhook.py registers every command handler on its bot instance
# (/start, /plan, /add, /mid, /math, /science, /sst, /eng, /hindi, callbacks,
# and the free-text AI doubt solver).
from api.webhook import bot  # noqa: E402

if bot is None:
    print("❌ Bot could not be initialized (missing token?).")
    sys.exit(1)

print("🔄 Removing Vercel webhook so updates come here...")
# Transient disconnects happen (especially right after a previous instance was
# killed mid-request) - retry a few times before giving up.
for attempt in range(1, 6):
    try:
        bot.remove_webhook()
        break
    except Exception as e:
        if attempt == 5:
            print(f"❌ Could not clear webhook after 5 attempts: {e}")
            sys.exit(1)
        wait = 3 * attempt
        print(f"   attempt {attempt} failed ({type(e).__name__}), retrying in {wait}s...")
        time.sleep(wait)

print("🤖 StudyOS bot is polling locally. Press Ctrl+C to stop.\n")
try:
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
except KeyboardInterrupt:
    print("\n👋 Bot stopped.")
