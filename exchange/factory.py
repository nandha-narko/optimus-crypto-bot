from exchange.exchangetype import ExchangeType
from exchange.exchange import Exchange
from exchange.binance import Binance
from exchange.others import Others

class Factory():
    def get_exchange(self, type: ExchangeType) -> Exchange:
        if type == ExchangeType.Binance:
            return Binance()
        else:
            return Others()