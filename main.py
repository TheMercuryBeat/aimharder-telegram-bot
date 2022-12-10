import os
import logging
from dotenv import load_dotenv
from datetime import date, timedelta
from warnings import filterwarnings
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.warnings import PTBUserWarning
from src.aimharder import Aimharder


load_dotenv()
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log_level)
logger = logging.getLogger(__name__)

CLASS_NAME, HOUR, BOOK, NONE = range(4)


def is_owner(user_id: int):
    return user_id == int(os.getenv('TELEGRAM_OWNER_ID'))


def get_days_options():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    return {'today': today.strftime('%Y%m%d'), 'tomorrow': tomorrow.strftime('%Y%m%d')}


def none_keyboard_button():
    return [InlineKeyboardButton('None', callback_data=str(NONE))]


def build_inline_buttons_by_days(days):
    return [list(map(lambda day: InlineKeyboardButton(str(day), callback_data=str(days[day])), days))]


def build_inline_buttons_by_class_names(class_names):
    keyboard = list(map(lambda class_name: [InlineKeyboardButton(class_name, callback_data=class_name)], class_names))
    keyboard.append(none_keyboard_button())
    return keyboard


def build_inline_buttons_by_hours(class_names):
    inline_button_by_time = list(map(lambda clazz: InlineKeyboardButton(
        f'{clazz.time} ({clazz.ocupation}/{clazz.limit})', callback_data=clazz.id), class_names))

    keyboard = []

    for index in range(0, len(inline_button_by_time), 2):
        hours = inline_button_by_time[index:index + 2]
        keyboard.append(hours)

    keyboard.append(none_keyboard_button())
    return keyboard


class AimharderBot:

    def __init__(self, aimharder: Aimharder):
        self.aimharder = aimharder

    async def start(self, update: Update, context: CallbackContext) -> int:
        user = update.message.from_user
        logger.debug("User %s started the conversation", user.first_name)

        if not is_owner(user.id):
            logger.info("User %s is not the owner.", user.first_name)
            return ConversationHandler.END

        if self.aimharder.booked_training is None:
            reply_markup = InlineKeyboardMarkup(build_inline_buttons_by_days(get_days_options()))
            await update.message.reply_text("Choose a day", reply_markup=reply_markup)
            return CLASS_NAME
        else:
            await update.message.reply_text(f'You have already booked a training: {self.aimharder.booked_training}')
            return ConversationHandler.END

    async def select_class_name(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()

        selected_day = query.data
        trainings = self.aimharder.list_trainings_by_date(selected_day)

        if len(trainings) <= 0:
            await query.edit_message_text("No there trainings!")
            return ConversationHandler.END

        class_names = sorted(set([training.class_name for training in trainings]))
        reply_markup = InlineKeyboardMarkup(build_inline_buttons_by_class_names(class_names))
        await query.edit_message_text(text="Choose a class", reply_markup=reply_markup)
        return HOUR

    async def select_hour(self, update: Update, context: CallbackContext):

        query = update.callback_query
        await query.answer()

        class_type = query.data

        if str(NONE) == class_type:
            await query.edit_message_text(text="See you next time!")
            return ConversationHandler.END

        class_by_name = filter(lambda training: training.class_name == class_type, self.aimharder.trainings)
        reply_markup = InlineKeyboardMarkup(build_inline_buttons_by_hours(class_by_name))
        await query.edit_message_text(text="Choose an hour", reply_markup=reply_markup)
        return BOOK

    async def book_class(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()

        training_id = query.data

        if str(NONE) == training_id:
            await query.edit_message_text(text="See you next time!")
            return ConversationHandler.END

        is_booked_training = self.aimharder.book_training(int(training_id))
        reply_message = f'{self.aimharder.booked_training} 💪💪' if is_booked_training else f'⚠️The training wasn\'t booked ⚠️'
        await query.edit_message_text(reply_message)
        return ConversationHandler.END

    async def booked_training_handler(self, update: Update, context: CallbackContext):
        training = self.aimharder.booked_training
        message = 'You don\'t have any training booked' if training is None \
            else f'You have a training booked: {training} 💪💪'
        await update.message.reply_text(message)
        return ConversationHandler.END

    async def cancel_booking_handler(self, update: Update, context: CallbackContext):
        training = self.aimharder.booked_training
        if training is None:
            message = 'You don\'t have any booked training!'
        else:
            is_cancelled_booking = self.aimharder.cancel_training()
            message = 'Cancelled training!' if is_cancelled_booking else 'Couldn\'t cancel the booked training!'
        await update.message.reply_text(message)
        return ConversationHandler.END


if __name__ == '__main__':

    logger.info('Starting up telegram bot...')

    application = ApplicationBuilder().token(os.getenv('TELEGRAM_TOKEN')).build()
    aimharder_bot = AimharderBot(Aimharder())

    booked_training_handler = CommandHandler('bookedtraining', aimharder_bot.booked_training_handler)
    cancel_handler = CommandHandler('canceltraining', aimharder_bot.cancel_booking_handler)

    book_training_handler = ConversationHandler(
        entry_points=[CommandHandler("booktraining", aimharder_bot.start)],
        states={
            CLASS_NAME: [CallbackQueryHandler(aimharder_bot.select_class_name)],
            HOUR: [CallbackQueryHandler(aimharder_bot.select_hour)],
            BOOK: [CallbackQueryHandler(aimharder_bot.book_class)]
        },
        fallbacks=[CommandHandler("booktraining", aimharder_bot.start)]
    )

    application.add_handler(book_training_handler)
    application.add_handler(booked_training_handler)
    application.add_handler(cancel_handler)

    application.run_polling()
