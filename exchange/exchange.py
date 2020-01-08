from abc import ABC, abstractmethod

class Exchange(ABC):

    baseUrl = ""

    def _url(self, path):
        return self.baseUrl + path

    @abstractmethod
    def get_price(self, symbol):
        pass

    @abstractmethod
    def get_symbols(self):
        pass

    @abstractmethod
    def get_account_info(self, user):
        pass