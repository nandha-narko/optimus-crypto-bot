import logging

from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler, Filters, MessageHandler, Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from exchange.factory import Factory
from exchange.exchangetype import ExchangeType
from exception import AccountInvalidException
from functools import partial

import db

db.initialize()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

SETUP_TYPE, SETUP_APIKEY, SETUP_SECRETKEY = range(3)

(SETUP, PRICE, ACCOUNT, ORDERS, CURRENT_MENU, NEXT_STEP) = map(chr, range(6))

factory = Factory()

setup_text = "Step {}/3: You can skip this step using /skip or exit setup using /exit\n"


def start(update, context):
    main_menu(update, context)

def main_menu(update, context):
    keyboard = [[InlineKeyboardButton("Setup", callback_data=str(SETUP)),
                 InlineKeyboardButton(
                     "Account Info", callback_data=str(ACCOUNT)),
                 InlineKeyboardButton("Price", callback_data=str(PRICE))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    send_message(update, "Hey " + update.effective_user.first_name +
                              "!, What do you like to do today?", reply_markup)

def setup(update, context):
    chatid = update.effective_chat.id
    keyboard = [[InlineKeyboardButton("Binance", callback_data=ExchangeType.Binance.name),
                 InlineKeyboardButton("Others", callback_data=ExchangeType.Others.name)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # context.bot.send_message(
    #     chat_id=chatid, text="Select Account Type", reply_markup=reply_markup)
    send_message(update, setup_text.format(1) + "Select Exchange:", reply_markup)
    context.user_data[CURRENT_MENU] = "Setup"
    return SETUP_TYPE

def setup_type(skip, update, context):
    user = update.effective_user
    if not skip:
        logger.info("Exchange type of %s: %s", user.first_name,
                    update.callback_query.data)
        db.update_user(user.username, {
                       'exchange_type': ExchangeType[update.callback_query.data].name})
    send_message(update, setup_text.format(2) + "Please provide your Api Key:")
    return SETUP_APIKEY

def setup_apikey(skip, update, context):
    user = update.message.from_user
    if not skip:
        logger.info("Api Key of %s: %s", user.first_name, update.message.text)
        db.update_user(user.username, {'api_key': update.message.text})
    send_message(update, setup_text.format(3) + 'Please provide your Secret Key:')
    return SETUP_SECRETKEY

def setup_secretkey(skip, update, context):
    user = update.message.from_user
    if not skip:
        logger.info("Secret Key of %s: %s",
                    user.first_name, update.message.text)
        db.update_user(user.username, {'secret_key': update.message.text})
        send_message(update, 'Bingo! Your account is now ready.')

    context.user_data[CURRENT_MENU] = None
    return ConversationHandler.END

def price(update, context):
    tuser = update.effective_user
    user = db.get_user(tuser.username)
    exchange = factory.get_exchange(ExchangeType[user['exchange_type']])

    if update.callback_query != None:
        if update.callback_query.data != str(PRICE) and str(PRICE) in update.callback_query.data:
            if context.args == None:
                context.args = []
            context.args.append(
                update.callback_query.data.replace(str(PRICE), ""))

    if context.args != None and len(context.args) > 0:
        priceInfo = exchange.get_price(context.args[0])
        message = "Price not available at the moment"
        if priceInfo != None:
            if priceInfo['symbol'] not in user['symbols']:
                db.update_symbols(tuser.username, priceInfo['symbol'])
            message = 'Price of ' + \
                priceInfo['symbol'] + " is : " + priceInfo['price']
        send_message(update, message)
    else:
        keyboard = []
        for symbol in user['symbols']:
            keyboard.append(InlineKeyboardButton(
                symbol, callback_data=str(PRICE) + symbol))
        reply_markup = InlineKeyboardMarkup([keyboard])
        send_message(update, "Please select a Symbol", reply_markup)

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

def send_message(update, message: str, reply_markup: InlineKeyboardMarkup = None):
    if update.callback_query != None:
        if reply_markup != None:
            update.callback_query.edit_message_text(text=message, reply_markup=reply_markup)
        else:
            update.callback_query.edit_message_text(text=message)
    else:
        if reply_markup != None:
            update.message.reply_text(text=message, reply_markup=reply_markup)
        else:
            update.message.reply_text(text=message)

def exit(update, context):
    user = update.effective_user
    logger.info("User %s exited %s.", user.first_name,
                context.user_data[CURRENT_MENU])
    update.message.reply_text('You have exited {}.'.format(context.user_data[CURRENT_MENU]),
                              reply_markup=ReplyKeyboardRemove())
    context.user_data[CURRENT_MENU] = None
    return ConversationHandler.END

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
            SETUP_TYPE: [CallbackQueryHandler(partial(setup_type, True), pattern='^' + ExchangeType.Binance.name + '$|^' + ExchangeType.Others.name + '$'), CommandHandler('skip', partial(setup_type, True))],
            SETUP_APIKEY: [MessageHandler(Filters.text, setup_apikey), CommandHandler('skip', partial(setup_apikey, True))],
            SETUP_SECRETKEY: [MessageHandler(Filters.text, setup_secretkey), CommandHandler(
                'skip', partial(setup_secretkey, True))]
        },

        fallbacks=[CommandHandler('exit', exit)]
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
