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
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
CLASS_TYPE, HOUR, BOOK, END = range(4)


def is_owner(user_id: int):
    return user_id == int(os.getenv('TELEGRAM_OWNER_ID'))


def get_days_options():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    return {'today': today.strftime('%Y%m%d'), 'tomorrow': tomorrow.strftime('%Y%m%d')}


def build_inline_buttons_by_days(days):
    return list(map(lambda day: InlineKeyboardButton(str(day), callback_data=str(days[day])), days))


def build_inline_buttons_by_class_names(class_names):
    keyboard = list(map(lambda class_name: [InlineKeyboardButton(class_name, callback_data=class_name)], class_names))
    keyboard.append([InlineKeyboardButton('None', callback_data=str(END))])
    return keyboard


def build_inline_buttons_by_hours(class_names):
    inline_button_by_time = list(map(lambda clazz: InlineKeyboardButton(
        f'{clazz.time} ({clazz.ocupation}/{clazz.limit})', callback_data=clazz.id), class_names))

    keyboard = []

    for index in range(0, len(inline_button_by_time), 2):
        hours = inline_button_by_time[index:index + 2]
        keyboard.append(hours)

    keyboard.append([InlineKeyboardButton('None', callback_data=str(END))])
    return keyboard


class AimharderBot:

    logger = logging.getLogger(__name__)

    def __init__(self, app: Aimharder):
        self.app = app

    async def start(self, update: Update, context: CallbackContext) -> int:
        user = update.message.from_user
        self.logger.debug("User %s started the conversation", user.first_name)
        if is_owner(user.id):
            if self.app.booked_training is None:
                keyboard = build_inline_buttons_by_days(get_days_options())
                reply_markup = InlineKeyboardMarkup([keyboard])
                await update.message.reply_text("Hi! Choose a date", reply_markup=reply_markup)
                return CLASS_TYPE
            else:
                await update.message.reply_text(f'You have already booked a training: {self.app.booked_training}')
                return ConversationHandler.END
        else:
            self.logger.info("User %s is not the owner.", user.first_name)
            await update.message.reply_text("Bye Bye")
            return ConversationHandler.END

    async def select_class_name(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()

        selected_date = query.data
        trainings = self.app.list_trainings_by_date(selected_date)

        if len(trainings) > 0:
            class_names = sorted(set([training.class_name for training in trainings]))
            keyboard = build_inline_buttons_by_class_names(class_names)
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="What class?", reply_markup=reply_markup)
            return HOUR
        else:
            await query.edit_message_text("No there trainings")
            return ConversationHandler.END

    async def select_hour(self, update: Update, context: CallbackContext):

        query = update.callback_query
        await query.answer()

        class_type = query.data

        if END == class_type:
            await query.edit_message_text(text="See you next time!")
            return ConversationHandler.END

        class_by_name = filter(lambda training: training.class_name == class_type, self.app.trainings)
        keyboard = build_inline_buttons_by_hours(class_by_name)
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text="What time would you like?", reply_markup=reply_markup)
        return BOOK

    async def book_class(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()

        training_id = query.data

        if END == int(training_id):
            await query.edit_message_text(text="See you next time!")
        else:
            is_booked_training = self.app.book_training(training_id)
            if is_booked_training:
                reply_message = f'{self.app.booked_training} 💪💪'
            else:
                reply_message = f'⚠️The training wasn\'t booked ⚠️'
            await query.edit_message_text(reply_message)
        return ConversationHandler.END

    async def end(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text="See you next time!")
        return ConversationHandler.END

    async def booked_training_handler(self, update: Update, context: CallbackContext):
        training = self.app.booked_training
        message = 'You don\'t have any training booked' if training is None \
            else f'You have a training booked: {training} 💪💪'
        await update.message.reply_text(message)

    async def cancel_booking_handler(self, update: Update, context: CallbackContext):
        is_cancelled_booking = self.app.cancel_training()
        message = 'Cancelled training!' if is_cancelled_booking else 'You don\'t have any booked training!'
        await update.message.reply_text(message)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.info('Starting up telegram bot...')

    application = ApplicationBuilder().token(os.getenv('TELEGRAM_TOKEN')).build()
    aimharder_bot = AimharderBot(Aimharder())

    booked_training_handler = CommandHandler('bookedtraining', aimharder_bot.booked_training_handler)
    cancel_handler = CommandHandler('canceltraining', aimharder_bot.cancel_booking_handler)

    book_training_handler = ConversationHandler(
        entry_points=[CommandHandler("booktraining", aimharder_bot.start)],
        states={
            CLASS_TYPE: [CallbackQueryHandler(aimharder_bot.select_class_name)],
            HOUR: [CallbackQueryHandler(aimharder_bot.select_hour)],
            BOOK: [CallbackQueryHandler(aimharder_bot.book_class)],
            END: [CallbackQueryHandler(aimharder_bot.end, pattern=f'^{str(END)}$')],
        },
        fallbacks=[CommandHandler("booktraining", aimharder_bot.start)]
    )

    application.add_handler(book_training_handler)
    application.add_handler(booked_training_handler)
    application.add_handler(cancel_handler)

    application.run_polling()
