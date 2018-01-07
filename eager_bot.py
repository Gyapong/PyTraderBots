from bot_scaffold import *
import sys

class EagerTraderBot(TraderBot):
    # for scheduled use
    #def load(self):
    #    print("{} loaded".format(self.name))

    #def store(self):
    #    print("{} stored".format(self.name))

    def init(self):
        for curr in self.wallet.get_currencies():
            if(curr.name == self.baseCurrency.name):
                curr.buytotal = Decimal(curr.amount)
                curr.buytotalprice = Decimal(curr.amount)
                curr.selltotal = Decimal(0)
                curr.selltotalprice = Decimal(0)
            else:
                curr.buytotal = Decimal(0)
                curr.buytotalprice = Decimal(0)
                curr.selltotal = Decimal(0)
                curr.selltotalprice = Decimal(0)

    def buy(self, curr, askrate, amount):
        curr.buytotal += amount
        curr.buytotalprice += self.make_transaction(CurrencyValue(curr.name, amount))

    def sell(self, curr, bidrate, amount):
        curr.selltotal += amount
        curr.selltotalprice += self.make_transaction(CurrencyValue(curr.name, -amount))

    def think(self):
        # dla każdej waluty poza główną wylicz ile średnio zapłaciłeś za jednostkę waluty
        # oraz za ile średnio ją sprzedawałeś
        free = float(self.baseCurrency.amount)
        for curr in self.wallet.get_currencies():
            if curr.name != self.baseCurrency.name:
                bidrate = float(self.currentExchangeRates[curr.name][0])
                if curr.buytotal > 0:
                    avgpaid = float(curr.buytotalprice) / float(curr.buytotal)
                    bid_rel_avg = bidrate / avgpaid
                    if bid_rel_avg>1.10: #jeżeli zyskasz 10% to sprzedaj wszystko
                        self.sell(curr, bidrate, curr.amount)
                else: #kup trochę
                    abit = Decimal(round(free/bidrate*0.1,2))
                    self.buy(curr, bidrate, abit)

                askrate = float(self.currentExchangeRates[curr.name][1])
                if curr.selltotal > 0:
                    avgearn = float(curr.selltotalprice) / float(curr.selltotal)
                    ask_rel_avg = askrate / avgearn
                    if ask_rel_avg<0.90: #jeżeli kupisz o 10% taniej to kupuj za wszystko
                        buy = Decimal(int(free / askrate*100)/100)
                        self.buy(curr, askrate, buy)
                else: #sprzedaj trochę
                    abit = Decimal(round(free/askrate*0.1,2))
                    self.sell(curr, askrate, abit)

class EagerBotSandbox(Sandbox):
    def bot_name(self):
        return 'eager'
    def make_bot(self, name, exchangeRatesProvider):
        return EagerTraderBot(name, exchangeRatesProvider)

# execute
EagerBotSandbox().interpret_command(sys.argv)
