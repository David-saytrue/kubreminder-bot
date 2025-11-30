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
            # Use ensure_ascii=False for proper Russian/Cyrillic character display in JSON
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
        f"👋 Привет! Я KubReminder — твой помощник для школы программирования.\n"
        f"⏰ Сейчас в Тбилиси: {now_tbilisi}\n\n"
        "🎯 Я здесь, чтобы помочь преподавателям не забывать свои занятия и вовремя о них напомнить.\n\n"
        "📌 Что я умею:\n"
        "📚 Показать ближайшие занятия: /lessons\n"
        "📌 Показать занятия на сегодня: /today\n"
        "📝 Добавлять новые занятия (только админ): /add_lesson\n"
        "❌ Удалять занятия (только админ): /delete_lesson\n\n"
        "🔔 Я буду напоминать о преподавательских занятиях заранее (за 30 минут) и каждый день в 10:00!"
    )
    await update.message.reply_text(message)

async def add_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /add_lesson command (admin-only). Adds a new lesson."""
    # Check for admin rights
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для добавления занятий.")
        return

    # Check if the command is executed in an allowed chat
    chat_id = str(update.effective_chat.id)
    if ALLOWED_CHATS and chat_id not in ALLOWED_CHATS and chat_id != CHAT_ID:
        await update.message.reply_text("❌ Этот чат не авторизован для использования бота.")
        return

    # Check for correct argument count
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ Неверный формат команды.\n"
            "Используйте: /add_lesson ГГГГ-ММ-ДД ЧЧ:ММ описание\n\n"
            "📌 Пример:\n"
            "/add_lesson 2025-10-21 17:00 Подготовка к занятию по Python"
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
            message = f"✅ Занятие добавлено:\n📅 Дата: {date_str}\n🕒 Время: {time_str}\n📝 Описание: {description}\n\n"
            message += "📌 Все текущие занятия:\n"
            for i, l in enumerate(lessons, 1):
                message += f"{i}. {l['date']} {l['time']} — {l['description']}\n"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ Ошибка при сохранении занятия.")
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты или времени.\n"
            "Используйте: /add_lesson ГГГГ-ММ-ДД ЧЧ:ММ описание\n\n"
            "📌 Пример:\n"
            "/add_lesson 2025-10-21 17:00 Подготовка к занятию по Python"
        )
    except Exception as e:
        logger.error(f"Error adding lesson: {e}")
        await update.message.reply_text("❌ Произошла ошибка.")

async def list_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /lessons command. Lists upcoming lessons."""
    lessons = load_lessons()
    if not lessons:
        await update.message.reply_text("📭 Нет запланированных занятий.")
        return
    
    now = datetime.now(TBILISI_TZ)
    # Filter for upcoming lessons (current time or later)
    upcoming = [l for l in lessons if datetime.fromisoformat(l['datetime']).astimezone(TBILISI_TZ) >= now]
    
    if not upcoming:
        await update.message.reply_text("📭 Нет предстоящих занятий.")
        return
    
    message = "📚 Ближайшие занятия:\n\n"
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
        await update.message.reply_text("📭 Сегодня занятий нет.")
        return
    
    message = "📌 Занятия на сегодня:\n\n"
    for i, l in enumerate(today_list, 1):
        message += f"{i}. 🕒 {l['time']} 📝 {l['description']}\n"
        
    await update.message.reply_text(message)

async def delete_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /delete_lesson command (admin-only). Deletes a lesson by index."""
    # Check for admin rights
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для удаления занятий.")
        return

    # Check if the command is executed in an allowed chat
    chat_id = str(update.effective_chat.id)
    if ALLOWED_CHATS and chat_id not in ALLOWED_CHATS and chat_id != CHAT_ID:
        await update.message.reply_text("❌ Этот чат не авторизован для использования бота.")
        return
        
    # Check for correct argument format (one digit)
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("❌ Используйте: /delete_lesson НОМЕР")
        return
        
    lessons = load_lessons()
    idx = int(context.args[0]) - 1 # Convert 1-based index to 0-based
    
    if 0 <= idx < len(lessons):
        removed = lessons.pop(idx)
        save_lessons(lessons)
        await update.message.reply_text(f"🗑 Занятие удалено: {removed['description']}")
    else:
        await update.message.reply_text("❌ Неверный номер занятия.")

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
                        text=f"⏰ Напоминание через 30 минут:\n📝 {l['description']} в {lesson_time.strftime('%H:%M')}"
                    )
                except Exception as e:
                    logger.error(f"Error sending 30-min reminder to chat {chat}: {e}")
            
            # Mark as reminded and set the flag to save
            l["reminded"] = True
            changed = True

        # 2. Daily 10:00 AM notification (This part executes only once per day at 10:00 AM because of the JobQueue setting)
        # Check if the lesson is today AND the current time is exactly 10:00 AM
        if lesson_time.date() == today and now.hour == 10 and now.minute == 0:
            # Send to all target chats
            for chat in target_chats:
                try:
                    await context.bot.send_message(
                        chat_id=chat,
                        text=f"🔔 Сегодня занятие в {lesson_time.strftime('%H:%M')}:\n📝 {l['description']}"
                    )
                except Exception as e:
                    logger.error(f"Error sending daily check to chat {chat}: {e}")

    # Save lessons.json if any 'reminded' status was updated
    if changed:
        save_lessons(lessons)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Logs errors caused by Updates."""
    logger.error(f"Update caused error: {context.error}")

# ============ MAIN FUNCTION ============
def main():
    """Starts the bot."""
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

    logger.info("🚀 KubReminder запущен!")
    
    # Run the bot until the user presses Ctrl-C
    # allowed_updates=Update.ALL_TYPES is good practice for robustness
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()