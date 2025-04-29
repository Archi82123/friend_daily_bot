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
    CallbackQueryHandler,
    MessageHandler,
    filters
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

TIMEZONE, TIME_SELECTION = range(2)

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
    await query.answer()

    user_timezone = query.data

    if user_timezone not in pytz.all_timezones:
        await query.answer("Пожалуйста, выбери часовой пояс из списка.")
        return TIMEZONE

    context.user_data["timezone"] = user_timezone

    await query.edit_message_text(
        "Отлично! Теперь напиши, в какое время ты хочешь получать сообщение.\n\nФормат: ЧЧ:ММ (например, 09:00 или 18:30)"
    )
    return TIME_SELECTION


async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    try:
        user_time = datetime.datetime.strptime(user_input, "%H:%M").time()
    except ValueError:
        await update.message.reply_text("Неверный формат времени. Пожалуйста, введи время в формате ЧЧ:ММ (например, 09:00).")
        return TIME_SELECTION

    chat_id = update.message.chat.id
    timezone_str = context.user_data.get("timezone")

    if not timezone_str:
        await update.message.reply_text("Что-то пошло не так. Пожалуйста, начни сначала с команды /start.")
        return ConversationHandler.END

    tz = pytz.timezone(timezone_str)

    # Удаляем старые задания
    job_queue = context.application.job_queue
    jobs = job_queue.get_jobs_by_name(str(chat_id))
    for job in jobs:
        job.schedule_removal()

    # Назначаем новое задание
    job_queue.run_daily(
        callback=daily_message,
        time=user_time,
        chat_id=chat_id,
        name=str(chat_id),
        tzinfo=tz
    )

    await update.message.reply_text(f"Готово! Теперь я буду присылать сообщения каждый день в {user_input} по времени {timezone_str}.")
    return ConversationHandler.END


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        TIMEZONE: [CallbackQueryHandler(set_timezone)],
        TIME_SELECTION: [CommandHandler("start", start), MessageHandler(filters.TEXT & ~filters.COMMAND, set_time)],
    },
    fallbacks=[],
)

app.add_handler(conversation_handler)

app.run_polling()
