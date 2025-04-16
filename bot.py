import datetime
import random
import pytz
from dotenv import load_dotenv
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler
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
    ("UTC−12:00", "Etc/GMT+12"),
    ("UTC−11:00", "Etc/GMT+11"),
    ("UTC−10:00 (Гавайи)", "Etc/GMT+10"),
    ("UTC−09:00 (Аляска)", "Etc/GMT+9"),
    ("UTC−08:00 (Калифорния)", "Etc/GMT+8"),
    ("UTC−07:00 (Денвер)", "Etc/GMT+7"),
    ("UTC−06:00 (Центральная Америка)", "Etc/GMT+6"),
    ("UTC−05:00 (Нью-Йорк, Торонто)", "Etc/GMT+5"),
    ("UTC−04:00 (Каракас)", "Etc/GMT+4"),
    ("UTC−03:00 (Буэнос-Айрес)", "Etc/GMT+3"),
    ("UTC−02:00", "Etc/GMT+2"),
    ("UTC−01:00", "Etc/GMT+1"),
    ("UTC±00:00 (Лондон)", "Etc/GMT"),
    ("UTC+01:00 (Берлин, Париж)", "Etc/GMT-1"),
    ("UTC+02:00 (Киев, Афины)", "Etc/GMT-2"),
    ("UTC+03:00 (Москва, Стамбул)", "Etc/GMT-3"),
    ("UTC+04:00 (Баку, Дубай)", "Etc/GMT-4"),
    ("UTC+05:00 (Ташкент, Екатеринбург)", "Etc/GMT-5"),
    ("UTC+06:00 (Алматы, Бишкек)", "Etc/GMT-6"),
    ("UTC+07:00 (Бангкок, Новосибирск)", "Etc/GMT-7"),
    ("UTC+08:00 (Пекин, Иркутск)", "Etc/GMT-8"),
    ("UTC+09:00 (Токио, Якутск)", "Etc/GMT-9"),
    ("UTC+10:00 (Владивосток, Сидней)", "Etc/GMT-10"),
    ("UTC+11:00 (Сахалин)", "Etc/GMT-11"),
    ("UTC+12:00 (Камчатка, Магадан)", "Etc/GMT-12"),
    ("UTC+13:00", "Etc/GMT-13"),
    ("UTC+14:00", "Etc/GMT-14"),
]


async def daily_message(context: CallbackContext):
    message = random.choice(MESSAGES)
    print(f"Отправка сообщения: {message}")
    await context.bot.send_message(chat_id=context.job.chat_id, text=message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for tz_label, tz_value in TIMEZONE_OPTIONS:
        keyboard.append([InlineKeyboardButton(text=tz_label, callback_data=tz_value)])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await update.message.reply_text(
        "Привет! Я твой друг 🤗 Я буду присылать тебе тёплые слова каждый день. Для этого мне нужно знать твой часовой пояс. Пожалуйста, выбери свой из списка:",
        reply_markup=reply_markup
    )
    return TIMEZONE


async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_timezone = update.callback_query.data

    if user_timezone not in pytz.all_timezones:
        await query.answer("Пожалуйста, выбери часовой пояс из предложенного списка.")
        return TIMEZONE

    chat_id = query.message.chat.id
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

    await query.edit_message_text(
        f"Отлично! Теперь я буду писать тебе каждый день в 09:00."
    )
    print(query.data)
    return ConversationHandler.END


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        TIMEZONE: [CallbackQueryHandler(set_timezone)],
    },
    fallbacks=[],
)

app.add_handler(conversation_handler)

app.run_polling()
