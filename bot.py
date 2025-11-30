#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KubReminder - Telegram bot for a programming school with notifications
Requires: python-telegram-bot version 21+ and pytz
Created for teachers of KubikRubik school, so they don't forget their lessons.
"""

import os
import json
import logging
from datetime import datetime, time, timedelta
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ============ CONFIGURATION ============
# Telegram Bot Token, read from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Default Chat ID for main notifications
CHAT_ID = os.getenv("CHAT_ID")

# Reads a comma-separated string of Admin IDs and converts them to a list of integers.
admin_id_str = os.getenv("ADMIN_ID")
ADMIN_IDS = [int(uid.strip()) for uid in admin_id_str.split(',') if uid.strip()]

# List of other allowed chat IDs (e.g., group chats)
ALLOWED_CHATS = os.getenv("ALLOWED_CHATS", "").split(",") if os.getenv("ALLOWED_CHATS") else []
# File to store lesson schedule
LESSONS_FILE = "lessons.json"

# Timezone setting (Tbilisi, Georgia)
TBILISI_TZ = pytz.timezone("Asia/Tbilisi")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ FILE FUNCTIONS ============
def load_lessons():
    """Loads the lessons schedule from the JSON file."""
    try:
        if os.path.exists(LESSONS_FILE):
            with open(LESSONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading lessons: {e}")
        return []

def save_lessons(lessons):
    """Saves the lessons schedule to the JSON file."""
    try:
        with open(LESSONS_FILE, 'w', encoding='utf-8') as f:
            # Use ensure_ascii=False for proper display in JSON
            json.dump(lessons, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving lessons: {e}")
        return False

# ============ COMMANDS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command, greets the user, and provides command info."""
    now_tbilisi = datetime.now(TBILISI_TZ).strftime("%Y-%m-%d %H:%M")
    message = (
        f"👋 Hi! I'm KubReminder — your assistant for the programming school.\n"
        f"⏰ Current time in Tbilisi: {now_tbilisi}\n\n"
        "🎯 I'm here to help teachers remember their lessons and remind them on time.\n\n"
        "📌 What I can do:\n"
        "📚 Show upcoming lessons: /lessons\n"
        "📌 Show today's lessons: /today\n"
        "📝 Add new lessons (admin only): /add_lesson\n"
        "❌ Delete lessons (admin only): /delete_lesson\n\n"
        "🔔 I will remind you about lessons in advance (30 minutes before) and every day at 10:00 AM!"
    )
    await update.message.reply_text(message)

async def add_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /add_lesson command (admin-only). Adds a new lesson."""
    # Check for admin rights
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You do not have permission to add lessons.")
        return

    # Check if the command is executed in an allowed chat
    chat_id = str(update.effective_chat.id)
    if ALLOWED_CHATS and chat_id not in ALLOWED_CHATS and chat_id != CHAT_ID:
        await update.message.reply_text("❌ This chat is not authorized to use the bot.")
        return

    # Check for correct argument count
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ Invalid command format.\n"
            "Use: /add_lesson YYYY-MM-DD HH:MM description\n\n"
            "📌 Example:\n"
            "/add_lesson 2025-10-21 17:00 Python Lesson Preparation"
        )
        return
    try:
        date_str = context.args[0]
        time_str = context.args[1]
        description = ' '.join(context.args[2:])
        # Combine date and time, then localize to Tbilisi timezone
        lesson_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        lesson_datetime = TBILISI_TZ.localize(lesson_datetime)
        
        lesson = {
            "date": date_str,
            "time": time_str,
            "description": description,
            "datetime": lesson_datetime.isoformat(),
            "reminded": False  # New field for 30-minute notification status
        }
        
        lessons = load_lessons()
        lessons.append(lesson)
        lessons.sort(key=lambda x: x['datetime']) # Sort by datetime
        
        if save_lessons(lessons):
            message = f"✅ Lesson added:\n📅 Date: {date_str}\n🕒 Time: {time_str}\n📝 Description: {description}\n\n"
            message += "📌 All current lessons:\n"
            # Note: The original code showed all lessons, but listing only *upcoming* is better practice.
            # However, maintaining the original logic to display *all* added lessons here:
            for i, l in enumerate(lessons, 1):
                message += f"{i}. {l['date']} {l['time']} — {l['description']}\n"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ Error saving the lesson.")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid date or time format.\n"
            "Use: /add_lesson YYYY-MM-DD HH:MM description\n\n"
            "📌 Example:\n"
            "/add_lesson 2025-10-21 17:00 Python Lesson Preparation"
        )
    except Exception as e:
        logger.error(f"Error adding lesson: {e}")
        await update.message.reply_text("❌ An error occurred.")

async def list_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /lessons command. Lists upcoming lessons."""
    lessons = load_lessons()
    if not lessons:
        await update.message.reply_text("📭 No lessons scheduled.")
        return
    
    now = datetime.now(TBILISI_TZ)
    # Filter for upcoming lessons (current time or later)
    upcoming = [l for l in lessons if datetime.fromisoformat(l['datetime']).astimezone(TBILISI_TZ) >= now]
    
    if not upcoming:
        await update.message.reply_text("📭 No upcoming lessons.")
        return
    
    message = "📚 Upcoming lessons:\n\n"
    # List up to 10 upcoming lessons
    for i, l in enumerate(upcoming[:10], 1):
        message += f"{i}. 📅 {l['date']} 🕒 {l['time']}\n   📝 {l['description']}\n\n"
        
    await update.message.reply_text(message)

async def today_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /today command. Lists lessons scheduled for today."""
    lessons = load_lessons()
    now = datetime.now(TBILISI_TZ)
    today = now.date()
    
    # Filter lessons for today's date
    today_list = [l for l in lessons if datetime.fromisoformat(l['datetime']).astimezone(TBILISI_TZ).date() == today]
    
    if not today_list:
        await update.message.reply_text("📭 No lessons today.")
        return
    
    message = "📌 Lessons for today:\n\n"
    for i, l in enumerate(today_list, 1):
        message += f"{i}. 🕒 {l['time']} 📝 {l['description']}\n"
        
    await update.message.reply_text(message)

async def delete_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /delete_lesson command (admin-only). Deletes a lesson by index."""
    # Check for admin rights
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You do not have permission to delete lessons.")
        return

    # Check if the command is executed in an allowed chat
    chat_id = str(update.effective_chat.id)
    if ALLOWED_CHATS and chat_id not in ALLOWED_CHATS and chat_id != CHAT_ID:
        await update.message.reply_text("❌ This chat is not authorized to use the bot.")
        return
        
    # Check for correct argument format (one digit)
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("❌ Use: /delete_lesson NUMBER")
        return
        
    lessons = load_lessons()
    idx = int(context.args[0]) - 1 # Convert 1-based index to 0-based
    
    if 0 <= idx < len(lessons):
        removed = lessons.pop(idx)
        save_lessons(lessons)
        await update.message.reply_text(f"🗑 Lesson deleted: {removed['description']}")
    else:
        await update.message.reply_text("❌ Invalid lesson number.")

# ============ JOBQUEUE ============
async def daily_check(context: ContextTypes.DEFAULT_TYPE):
    """
    Job function run by the JobQueue.
    Performs two types of checks:
    1. 30-minute reminder before a lesson.
    2. Daily 10:00 AM notification for lessons on the current day.
    """
    lessons = load_lessons()
    now = datetime.now(TBILISI_TZ)
    today = now.date()
    changed = False  # Flag to indicate if lessons.json needs saving (due to 'reminded' status update)

    # Determine all target chat IDs (main chat + allowed chats)
    target_chats = [CHAT_ID] + ALLOWED_CHATS
    # Remove duplicates and None/empty strings if present
    target_chats = list(set(filter(None, target_chats)))

    for l in lessons:
        lesson_time = datetime.fromisoformat(l['datetime']).astimezone(TBILISI_TZ)
        time_until_lesson = lesson_time - now

        # 1. 30-minute reminder
        # Check if reminder hasn't been sent and the lesson is in the next 30 minutes
        if not l.get("reminded") and timedelta(0) <= time_until_lesson <= timedelta(minutes=30):
            # Send to all target chats
            for chat in target_chats:
                try:
                    await context.bot.send_message(
                        chat_id=chat,
                        text=f"⏰ Reminder in 30 minutes:\n📝 {l['description']} at {lesson_time.strftime('%H:%M')}"
                    )
                except Exception as e:
                    logger.error(f"Error sending 30-min reminder to chat {chat}: {e}")
            
            # Mark as reminded and set the flag to save
            l["reminded"] = True
            changed = True

        # 2. Daily 10:00 AM notification (This part executes only once per day at 10:00 AM because of the JobQueue setting)
        # Check if the lesson is today AND the current time is exactly 10:00 AM
        # Note: The 10:00 AM check is a minor inefficiency here as the run_daily scheduler already ensures this job
        # runs only at 10:00 AM. However, keeping the check for robustness if the job were ever run manually or by another scheduler.
        if lesson_time.date() == today and now.hour == 10 and now.minute == 0:
            # Send to all target chats
            for chat in target_chats:
                try:
                    await context.bot.send_message(
                        chat_id=chat,
                        text=f"🔔 Today's lesson is at {lesson_time.strftime('%H:%M')}:\n📝 {l['description']}"
                    )
                except Exception as e:
                    logger.error(f"Error sending daily check to chat {chat}: {e}")

    # Save lessons.json if any 'reminded' status was updated
    if changed:
        save_lessons(lessons)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Logs errors caused by Updates."""
    logger.error(f"Update {update} caused error: {context.error}")

# ============ MAIN FUNCTION ============
def main():
    """Starts the bot."""
    # Ensure TOKEN is set
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set. Exiting.")
        return
        
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_lesson", add_lesson))
    application.add_handler(CommandHandler("lessons", list_lessons))
    application.add_handler(CommandHandler("today", today_lessons))
    application.add_handler(CommandHandler("delete_lesson", delete_lesson))

    # Add error handler
    application.add_error_handler(error_handler)

    # Setup JobQueue for periodic tasks
    jq = application.job_queue
    
    # Schedule the daily check at 10:00 AM (only sends daily lesson list)
    # The 'time' argument ensures it runs precisely at 10:00 TBILISI_TZ time.
    jq.run_daily(daily_check, time=time(hour=10, minute=0, tzinfo=TBILISI_TZ), days=(0, 1, 2, 3, 4, 5, 6), name="daily_10am_check")
    
    # Schedule the check for 30-minute reminders (runs every 60 seconds)
    jq.run_repeating(daily_check, interval=60, first=0, name="30min_reminder_check")

    logger.info("🚀 KubReminder started!")
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()