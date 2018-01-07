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

class DummyBotSandbox(Sandbox):
    def bot_name(self):
        return 'dummy'
    def make_bot(self, name, exchangeRatesProvider):
        return DummyTraderBot(name, exchangeRatesProvider)

# execute
DummyBotSandbox().interpret_command(sys.argv)
