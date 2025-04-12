import datetime
import random
import pytz
from dotenv import load_dotenv
import os

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackContext,
)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

moscow_tz = pytz.timezone("Europe/Moscow")


MESSAGES = [
    "Ты справишься с любыми трудностями 💪",
    "Ты достоин счастья ✨",
    "Ты — лучший человек для самого себя 💖",
    "Сегодня обязательно произойдёт что-то хорошее 🌞",
    "Ты не один. Я рядом 🤗",
]


async def daily_message(context: CallbackContext):
    message = random.choice(MESSAGES)
    print(f"Отправка сообщения: {message}")
    await context.bot.send_message(chat_id=context.job.chat_id, text=message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("Привет! Я твой друг 🤗 Я буду присылать тебе тёплые слова каждый день в 09:00.")

    current_time = datetime.datetime.now(moscow_tz)
    print(f"Текущее время по Москве: {current_time}")

    job_queue = context.application.job_queue
    jobs = job_queue.get_jobs_by_name(str(chat_id))
    if not jobs:
        print(f"Задачи для {chat_id} не найдены. Запускаем новую задачу.")
    for job in jobs:
        print(f"Удаление старой задачи {job.name}")
        job.schedule_removal()

    scheduled_time = datetime.time(hour=23, minute=8, tzinfo=moscow_tz)
    print(f"Запланировано отправить сообщение в {scheduled_time} по Москве")

    job_queue.run_daily(
        callback=daily_message,
        time=scheduled_time,
        chat_id=chat_id,
        name=str(chat_id),
    )


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.run_polling()
