import logging

from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler, Filters, MessageHandler, Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from exchange.factory import Factory
from exchange.exchangetype import ExchangeType
from exception import AccountInvalidException

import db

db.initialize()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

SELECT_TYPE, ENTER_APIKEY, ENTER_SECRETKEY = range(3)

(SETUP, PRICE, ACCOUNT, ORDERS) = map(chr, range(4))

factory = Factory()

def start(update, context):
    main_menu(update, context)

def main_menu(update, context):
    keyboard = [[InlineKeyboardButton("Setup", callback_data=str(SETUP)),
                 InlineKeyboardButton("Account Info", callback_data=str(ACCOUNT)),
                 InlineKeyboardButton("Price", callback_data=str(PRICE))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Hey " + update.effective_user.first_name + "!, What do you like to do today?", reply_markup=reply_markup)

def setup(update, context):
    chatid = update.effective_chat.id
    keyboard = [[InlineKeyboardButton("Binance", callback_data=ExchangeType.Binance.name),
                 InlineKeyboardButton("Others", callback_data=ExchangeType.Others.name)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # context.bot.send_message(
    #     chat_id=chatid, text="Select Account Type", reply_markup=reply_markup)
    update.callback_query.edit_message_text(
        text="Please provide your Api Key:", reply_markup=reply_markup)
    return SELECT_TYPE


def select_type(update, context):
    user = update.effective_user
    logger.info("Exchange type of %s: %s", user.first_name,
                update.callback_query.data)
    db.update_user(user.username, { 'exchange_type': ExchangeType[update.callback_query.data].name })
    update.callback_query.edit_message_text(text="Please provide your Api Key:")
    return ENTER_APIKEY


def enter_apikey(update, context):
    user = update.message.from_user
    logger.info("Api Key of %s: %s", user.first_name, update.message.text)
    db.update_user(user.username, { 'api_key': update.message.text })
    update.message.reply_text('Please provide your Secret Key:')
    return ENTER_SECRETKEY


def enter_secretkey(update, context):
    user = update.message.from_user
    logger.info("Secret Key of %s: %s",
                user.first_name, update.message.text)
    db.update_user(user.username, { 'secret_key': update.message.text })
    update.message.reply_text('Bingo! Your account is now ready.')

    return ConversationHandler.END

def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled conversation.", user.first_name)
    update.message.reply_text('Bye!.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

def price(update, context):
    tuser = update.effective_user
    user = db.get_user(tuser.username)
    exchange = factory.get_exchange(ExchangeType[user['exchange_type']])

    if update.callback_query != None:
        if update.callback_query.data != str(PRICE) and str(PRICE) in update.callback_query.data:
            if context.args == None: context.args = []
            context.args.append(update.callback_query.data.replace(str(PRICE), ""))

    if context.args != None and len(context.args) > 0:
        priceInfo = exchange.get_price(context.args[0])
        message = "Price not available at the moment"
        if priceInfo != None: message = 'Price of ' + priceInfo['symbol'] + " is : " + priceInfo['price']

        if update.callback_query != None:
            update.callback_query.edit_message_text(text=message)
        else:
            update.message.reply_text(text=message)
    else:
        keyboard = []
        for symbol in exchange.get_symbols():
            keyboard.append(InlineKeyboardButton(
                symbol, callback_data=str(PRICE) + symbol))
        reply_markup = InlineKeyboardMarkup([keyboard])
        if update.callback_query != None:
            update.callback_query.edit_message_text(text="Please select a Symbol", reply_markup=reply_markup)
        else:
            update.message.reply_text(text="Please select a Symbol", reply_markup=reply_markup)

def account(update, context):
    message = ""
    tuser = update.effective_user
    user = db.get_user(tuser.username)
    exchange = factory.get_exchange(ExchangeType[user['exchange_type']])
    try:
        accountinfo = exchange.get_account_info(user)
        message = "Your account type is " + accountinfo['accountType']
    except AccountInvalidException:
        message = "Your account seems to be invalid. Please configure your account using /m or /s"
    send_message(update, message)

def send_message(update, message: str):
    if update.callback_query != None:
        update.callback_query.edit_message_text(text=message)
    else:
        update.message.reply_text(text=message)

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Invalid command!. Please try /help to view the supported commands")


def help(update, context):
    update.message.reply_text(
        'Try these commands:\n' +
        '/m - view the main menu\n' +
        '/s - configure your account\n' +
        '/a - get account information\n' +
        '/p - get price ticker'
    )

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Error occured "%s"', context.error)


def main():
    updater = Updater(
        '911403126:AAG54z4cojDzqVJlpbqoGzudgDBBFTrzZ10', use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(CommandHandler("m", main_menu))

    setup_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('s', setup), CallbackQueryHandler(
            setup, pattern='^(' + str(SETUP) + ')$')],

        states={
            SELECT_TYPE: [CallbackQueryHandler(select_type, pattern='^' + ExchangeType.Binance.name + '$|^' + ExchangeType.Others.name + '$')],
            ENTER_APIKEY: [MessageHandler(Filters.text, enter_apikey)],
            ENTER_SECRETKEY: [MessageHandler(Filters.text, enter_secretkey)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(setup_conv_handler)

    dp.add_handler(CommandHandler("p", price))
    dp.add_handler(CallbackQueryHandler(
        price, pattern='^(' + str(PRICE) + '.*)$'))

    dp.add_handler(CommandHandler("a", account))
    dp.add_handler(CallbackQueryHandler(
        account, pattern='^(' + str(ACCOUNT) + '.*)$'))
    # on /help call help function and respond to anyone
    dp.add_handler(CommandHandler("help", help))

    dp.add_handler(MessageHandler(Filters.command, unknown))

    # log all errors
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
