from bot_scaffold import *
import sys

class DummyTraderBot(TraderBot):
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
                    if bid_rel_avg>1.05: #jeżeli zyskasz 5% to sprzedaj wszystko
                        self.sell(curr, bidrate, curr.amount)
                else: #kup trochę
                    abit = Decimal(round(free/bidrate*0.1,2))
                    self.buy(curr, bidrate, abit)

                askrate = float(self.currentExchangeRates[curr.name][1])
                if curr.selltotal > 0:
                    avgearn = float(curr.selltotalprice) / float(curr.selltotal)
                    ask_rel_avg = askrate / avgearn
                    if ask_rel_avg<0.95: #jeżeli kupisz o 5% taniej to kupuj za wszystko
                        buy = Decimal(int(free / askrate*100)/100)
                        self.buy(curr, askrate, buy)
                else: #sprzedaj trochę
                    abit = Decimal(round(free/askrate*0.1,2))
                    self.sell(curr, askrate, abit)

def make_bot(name, exchangeRatesProvider):
    return DummyTraderBot(name, exchangeRatesProvider)

def bot_initialize(name):
    bot = make_bot(name, ExchangeRatesNBPCurrentProvider())
    bot.initialize()

def next_move(name):
    bot = make_bot(name, ExchangeRatesNBPCurrentProvider())
    bot.make_move()

def simulate(name):
    prov = ExchangeRatesNBPHistoricProvider('GBP','gbp.csv',0.02)
    bot = make_bot(name+'-sim', prov)
    BotSimulator(bot, prov).simulate()

# name of the bot
name = 'eager'

# basic commands
if len(sys.argv)>1:
    command = sys.argv[1]
    if command=='init':
        bot_initialize(name)
    else:
        if command=='sim':
            simulate(name)
        else: next_move(name)
else: next_move(name)
