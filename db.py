import os
from tinydb import TinyDB, Query
from exchange.exchangetype import ExchangeType

db_folder = os.path.join(os.path.dirname(__file__))
db_file = os.path.join(db_folder, 'data', 'optimus_db.json')
the_db = TinyDB(db_file)

User = Query()

def initialize():
    users = the_db.table('users')
    if users.get(User.username == 'nandhakumars') == None:
        users.insert({
            'username': 'nandhakumars',
            'exchange_type': ExchangeType.Binance.name,
            'api_key': '7LahfGm0mG1Wvl7J4QZ0UkaH3C6YiWym4LYR8DSPlNHyDYp8kOpLAzkkTnhOIlLL',
            'secret_key': 'mrhjlw2VPZUG3UgLPrCV2Ody4gTX17XdoFC5EwkaaavWXfaa7aXs3Ykqw4iRRkuh'
        })

def get_user(username):
    users = the_db.table('users')
    if users.get(User.username == username) == None:
        users.insert({
            'username': username,
            'exchange_type': ExchangeType.Others,
            'api_key': '',
            'secret_key': ''
        })
    return users.get(User.username == username)

def update_user(username, update):
    users = the_db.table('users')
    print("Updating user: {}".format(username))
    users.update(update, User.username == username)