-- 1. Add Telegram Chat ID to users table to link your account
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT;
