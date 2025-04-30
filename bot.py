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

from constants import (
    GREETING_MESSAGE,
    INVALID_TIME_FORMAT_MESSAGE,
    SET_TIME_PROMPT,
    ERROR_NO_TIMEZONE,
    CONFIRMATION_MESSAGE,
    INVALID_TIMEZONE_SELECTED,
    DAILY_MESSAGES,
    TIMEZONE_OPTIONS,
    CHOOSE_YOUR_TIMEZONE,
    MOSCOW_TIME_ZONE,
    OTHER_TIME_ZONE
)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


TIMEZONE, TIME_SELECTION = range(2)


async def daily_message(context: CallbackContext):
    message = random.choice(DAILY_MESSAGES)
    print(f"Отправка сообщения: {message}")
    await context.bot.send_message(chat_id=context.job.chat_id, text=message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(MOSCOW_TIME_ZONE, callback_data="Etc/GMT-3")],
        [InlineKeyboardButton(OTHER_TIME_ZONE, callback_data="SHOW_ALL")]
    ]

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await update.message.reply_text(
        GREETING_MESSAGE,
        reply_markup=reply_markup
    )
    return TIMEZONE


async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_timezone = query.data

    if user_timezone == "SHOW_ALL":
        keyboard = [
            [InlineKeyboardButton(text=label, callback_data=value)]
            for label, value in TIMEZONE_OPTIONS
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            CHOOSE_YOUR_TIMEZONE,
            reply_markup=reply_markup
        )
        return TIMEZONE

    if user_timezone not in pytz.all_timezones:
        await query.answer(INVALID_TIMEZONE_SELECTED)
        return TIMEZONE

    context.user_data["timezone"] = user_timezone

    await query.edit_message_text(
        SET_TIME_PROMPT
    )
    return TIME_SELECTION


async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    try:
        user_time = datetime.datetime.strptime(user_input, "%H:%M").time()
    except ValueError:
        await update.message.reply_text(INVALID_TIME_FORMAT_MESSAGE)
        return TIME_SELECTION

    chat_id = update.message.chat.id
    timezone_str = context.user_data.get("timezone")

    if not timezone_str:
        await update.message.reply_text(ERROR_NO_TIMEZONE)
        return ConversationHandler.END

    tz = pytz.timezone(timezone_str)
    user_time_with_tz = datetime.time(hour=user_time.hour, minute=user_time.minute, tzinfo=tz)


    job_queue = context.application.job_queue
    jobs = job_queue.get_jobs_by_name(str(chat_id))
    for job in jobs:
        job.schedule_removal()

    job_queue.run_daily(
        callback=daily_message,
        time=user_time_with_tz,
        chat_id=chat_id,
        name=str(chat_id)
    )

    await update.message.reply_text(CONFIRMATION_MESSAGE.format(time=user_input, timezone=timezone_str))
    return ConversationHandler.END


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
    ],
    states={
        TIMEZONE: [
            CallbackQueryHandler(set_timezone)
        ],
        TIME_SELECTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, set_time),
            CommandHandler("start", start),  # позволяет сбросить на любом шаге
        ],
    },
    fallbacks=[
    ],
)

app.add_handler(conversation_handler)

app.run_polling()
