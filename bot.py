import datetime
import random
import pytz
from dotenv import load_dotenv
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext,
    ConversationHandler,
)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


MESSAGES = [
    "Ты справишься с любыми трудностями 💪",
    "Ты достоин счастья ✨",
    "Ты — лучший человек для самого себя 💖",
    "Сегодня обязательно произойдёт что-то хорошее 🌞",
    "Ты не один. Я рядом 🤗",
]

TIMEZONE = range(1)

TIMEZONE_OPTIONS = [
    'Europe/Moscow',
    'Europe/Kaliningrad',
    'Asia/Yekaterinburg',
    'Asia/Novosibirsk',
    'Asia/Krasnoyarsk',
    'Asia/Irkutsk',
    'Asia/Yakutsk',
    'Asia/Vladivostok',
    'Asia/Magadan',
    'Asia/Sakhalin',
    'Asia/Kamchatka',
]

async def daily_message(context: CallbackContext):
    message = random.choice(MESSAGES)
    print(f"Отправка сообщения: {message}")
    await context.bot.send_message(chat_id=context.job.chat_id, text=message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[tz] for tz in TIMEZONE_OPTIONS]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Привет! Я твой друг 🤗 Я буду присылать тебе тёплые слова каждый день в 09:00.\n"
        "Для этого выбери свой часовой пояс из списка:",
        reply_markup=reply_markup
    )
    return TIMEZONE


async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_timezone = update.message.text

    if user_timezone not in pytz.all_timezones:
        await update.message.reply_text("Пожалуйста, выбери часовой пояс из предложенного списка.")
        return TIMEZONE

    chat_id = update.effective_chat.id
    tz = pytz.timezone(user_timezone)

    job_queue = context.application.job_queue
    jobs = job_queue.get_jobs_by_name(str(chat_id))
    for job in jobs:
        job.schedule_removal()

    scheduled_time = datetime.time(hour=9, minute=0, tzinfo=tz)
    job_queue.run_daily(
        callback=daily_message,
        time=scheduled_time,
        chat_id=chat_id,
        name=str(chat_id),
    )

    await update.message.reply_text(f"Отлично! Теперь я буду писать тебе каждый день в 09:00 по времени {user_timezone}.")
    return ConversationHandler.END


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        TIMEZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_timezone)],
    },
    fallbacks=[],
)

app.add_handler(conv_handler)

app.run_polling()
