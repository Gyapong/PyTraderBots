from bot_scaffold import *
import sys

class DummyTraderBot(TraderBot):
    # for scheduled use
    #def load(self):
    #    print("{} loaded".format(self.name))

    #def store(self):
    #    print("{} stored".format(self.name))

    # for custom data structures initialization
    # only in sim mode
    #def init(self):
    #    pass

    def think(self):
        pass
        #you have self.currentExchangeRates and self.wallet at your disposal

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
name = 'dummy'

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
