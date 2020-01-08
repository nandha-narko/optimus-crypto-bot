from exchange.exchange import Exchange
from binance.client import Client, BinanceAPIException
from exception import AccountInvalidException
import requests

class Binance(Exchange):

    baseUrl = 'https://api.binance.com'

    def get_client(self, user) -> Client:
        return Client(user['api_key'], user['secret_key'])

    def get_price(self, symbol):
        url = super()._url("/api/v3/ticker/price?symbol=" + symbol)
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def get_symbols(self) -> list:
        symbols = []
        url = super()._url("/api/v3/ticker/price")
        response = requests.get(url)
        if response.status_code == 200:
            for item in response.json():
                symbols.append(item['symbol'])
        return symbols

    def get_account_info(self, user):
        try:
            client = self.get_client(user)
            return client.get_account()
        except BinanceAPIException:
            raise AccountInvalidException