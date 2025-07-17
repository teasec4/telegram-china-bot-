import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes, CallbackQueryHandler
)
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
import logging
from config import BOT_TOKEN
from db import Database
from services.request_service import RequestService

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

START, DESCRIPTION, CONTACT = range(3)

REPLIES = {
    "welcome": (
        "👋 Добро пожаловать!\n\n"
        "Мы помогаем найти товары в Китае. Нажмите кнопку ниже, чтобы отправить заявку."
    ),
    "ask_description": "📝 Опишите, какой товар вы ищете.",
    "ask_contact": "📞 Оставьте контакт для связи.",
    "thanks": "✅ Спасибо! Ваша заявка отправлена.",
    "already_requested" : "Вы уже отправили заявку. Мы свяжемся как можно скорее!\n/delete - чтобы отменить заявку.\n/help - для просмотра команд.",
    "help": (
        "/start – начать\n"
        "/cancel – отменить во время заполнения\n"
        "/help – помощь \n"
        "/delete - удалить заявку полностью"
    ),
    "no_request":"У Вас нет активной заявки.",
    "deleted": "Ваша заявка успешно удалена.",
    "cancelled": "❌ Заявка отменена. Вы можете начать заново с /start."
}

db = Database()
request_service = None  # to be initialized in main()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(update.effective_user.id)
    logging.info(f"User {user_id} has_request: {bool(user_id)}")
    if db.user_has_request(user_id):
        keyboard =[[InlineKeyboardButton("Моя заявка", callback_data="view_request")]]
        await update.message.reply_text(REPLIES["already_requested"], reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        keyboard = [[InlineKeyboardButton("📨 Оставить заявку", callback_data="start_request")]]
        await update.message.reply_text(REPLIES["welcome"], reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    return START

async def handle_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.from_user.id)
    if db.user_has_request(user_id):
        await query.answer(REPLIES['already_requested'], show_alert=True)
        return ConversationHandler.END
    
    await query.answer()
    await query.message.reply_text(REPLIES["ask_description"])
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text)<5:
        await update.message.reply_text("⚠️ Пожалуйста, опишите товар подробнее (минимум 5 символов).")
        return DESCRIPTION
    context.user_data["description"] = text
    await update.message.reply_text(REPLIES["ask_contact"])
    return CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.text.strip()
    if len(contact) < 3:
        await update.message.reply_text("⚠️ Контакт слишком короткий, пожалуйста укажите корректный.")
        return CONTACT
    context.user_data["contact"] = contact
    description = context.user_data.get("description")
    user_id = int(update.effective_user.id)

    success = await request_service.create_request(user_id, description, contact)
    if not success:
        await update.message.reply_text(REPLIES['already_requested'])
    else:
        await update.message.reply_text(REPLIES["thanks"])

    return ConversationHandler.END

async def view_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.from_user.id)
    logging.info(f"View request called by user {user_id}")
    request = db.get_request_by_user(user_id)
    if request:
        description, contact = request
        message = (
            f"📄*Ваша заявка*\n\n"
            f"📦*Описание* {description}\n"
            f"📞*Контакт* {contact}\n"
        )
        keyboard = [[InlineKeyboardButton("❌ Удалить заявку", callback_data='delete_request')]]
        await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await query.message.reply_text(REPLIES['no_request'])

async def delete_request(update:Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.from_user.id)

    db.delete_request(user_id)
    await query.message.reply_text(REPLIES['deleted'])

async def delete_command(update:Update, context:ContextTypes.DEFAULT_TYPE):
    user_id = int(update._effective_user.id)
    if db.user_has_request(user_id):
        db.delete_request(user_id)
        await update.message.reply_text(REPLIES['deleted'])
    else:
        await update.message.reply_text(REPLIES['no_request'])

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(REPLIES["cancelled"])
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(REPLIES["help"])

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Неизвестная команда. Введите /help чтобы увидеть доступные команды.")

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await update.message.reply_text(f"🆔 Chat ID: `{chat.id}`", parse_mode="Markdown")

def main():
    global request_service

    filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
    application = Application.builder().token(BOT_TOKEN).build()

    global db
    request_service = RequestService(db, application.bot)

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_start_button, pattern="^start_request$")],
        states={
            START: [CallbackQueryHandler(handle_start_button, pattern="^start_request$")],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("delete", delete_command))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(view_request, pattern="^view_request$"))
    application.add_handler(CallbackQueryHandler(delete_request, pattern="^delete_request$"))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(CommandHandler("chatid", get_chat_id))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()