#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KubReminder — Telegram-бот для школы программирования с уведомлениями
Требует: python-telegram-bot версии 21+ и pytz
Создан для преподавателей школы KubikRubik, чтобы не забывать свои занятия.
"""

import os
import json
import logging
from datetime import datetime, time, timedelta
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ============ НАСТРОЙКИ ============
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ADMIN_IDS = [int(os.getenv("ADMIN_ID", "1040093417"))]
LESSONS_FILE = "lessons.json"

TBILISI_TZ = pytz.timezone("Asia/Tbilisi")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ ФАЙЛОВЫЕ ФУНКЦИИ ============
def load_lessons():
    try:
        if os.path.exists(LESSONS_FILE):
            with open(LESSONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Ошибка при загрузке занятий: {e}")
        return []

def save_lessons(lessons):
    try:
        with open(LESSONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(lessons, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении занятий: {e}")
        return False

# ============ КОМАНДЫ ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if ADMIN_IDS and update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для добавления занятий.")
        return
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
        lesson_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        lesson_datetime = TBILISI_TZ.localize(lesson_datetime)
        lesson = {
            "date": date_str,
            "time": time_str,
            "description": description,
            "datetime": lesson_datetime.isoformat(),
            "reminded": False  # новое поле для 30-минутного уведомления
        }
        lessons = load_lessons()
        lessons.append(lesson)
        lessons.sort(key=lambda x: x['datetime'])
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
        logger.error(f"Ошибка при добавлении занятия: {e}")
        await update.message.reply_text("❌ Произошла ошибка.")

async def list_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lessons = load_lessons()
    if not lessons:
        await update.message.reply_text("📭 Нет запланированных занятий.")
        return
    now = datetime.now(TBILISI_TZ)
    upcoming = [l for l in lessons if datetime.fromisoformat(l['datetime']).astimezone(TBILISI_TZ) >= now]
    if not upcoming:
        await update.message.reply_text("📭 Нет предстоящих занятий.")
        return
    message = "📚 Ближайшие занятия:\n\n"
    for i, l in enumerate(upcoming[:10], 1):
        message += f"{i}. 📅 {l['date']} 🕒 {l['time']}\n   📝 {l['description']}\n\n"
    await update.message.reply_text(message)

async def today_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lessons = load_lessons()
    now = datetime.now(TBILISI_TZ)
    today = now.date()
    today_list = [l for l in lessons if datetime.fromisoformat(l['datetime']).astimezone(TBILISI_TZ).date() == today]
    if not today_list:
        await update.message.reply_text("📭 Сегодня занятий нет.")
        return
    message = "📌 Занятия на сегодня:\n\n"
    for i, l in enumerate(today_list, 1):
        message += f"{i}. 🕒 {l['time']} 📝 {l['description']}\n"
    await update.message.reply_text(message)

async def delete_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_IDS and update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав для удаления занятий.")
        return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("❌ Используйте: /delete_lesson НОМЕР")
        return
    lessons = load_lessons()
    idx = int(context.args[0]) - 1
    if 0 <= idx < len(lessons):
        removed = lessons.pop(idx)
        save_lessons(lessons)
        await update.message.reply_text(f"🗑 Занятие удалено: {removed['description']}")
    else:
        await update.message.reply_text("❌ Неверный номер занятия.")

# ============ JOBQUEUE ============
async def daily_check(context: ContextTypes.DEFAULT_TYPE):
    lessons = load_lessons()
    now = datetime.now(TBILISI_TZ)
    today = now.date()
    changed = False  # для сохранения поля reminded

    for l in lessons:
        lesson_time = datetime.fromisoformat(l['datetime']).astimezone(TBILISI_TZ)
        time_until_lesson = lesson_time - now

        # Напоминание за 30 минут до занятия
        if not l.get("reminded") and timedelta(0) <= time_until_lesson <= timedelta(minutes=30):
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"⏰ Напоминание через 30 минут:\n📝 {l['description']} в {lesson_time.strftime('%H:%M')}"
            )
            l["reminded"] = True
            changed = True

        # Дневное уведомление в 10:00
        if lesson_time.date() == today and now.hour == 10 and now.minute == 0:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"🔔 Сегодня занятие в {lesson_time.strftime('%H:%M')}:\n📝 {l['description']}"
            )

    if changed:
        save_lessons(lessons)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка при обновлении: {context.error}")

# ============ ОСНОВНАЯ ФУНКЦИЯ ============
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_lesson", add_lesson))
    application.add_handler(CommandHandler("lessons", list_lessons))
    application.add_handler(CommandHandler("today", today_lessons))
    application.add_handler(CommandHandler("delete_lesson", delete_lesson))
    application.add_error_handler(error_handler)

    jq = application.job_queue
    jq.run_daily(daily_check, time=time(hour=10, minute=0), days=(0,1,2,3,4,5,6))
    jq.run_repeating(daily_check, interval=60, first=0)

    logger.info("🚀 KubReminder запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
