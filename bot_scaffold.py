import csv
import requests
from datetime import date
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from decimal import getcontext
from bisect import bisect
import json

getcontext().prec = 8;

class CsvFileService:
    def __init__(self, delimiter=',', quotechar='\'', dialect=csv.excel):
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.dialect = dialect

    def readFile(self, name):
        data = []
        with open(name, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter=self.delimiter,
                quotechar=self.quotechar,
                dialect=self.dialect)
            for row in reader:
                data.append(row)
        return data

    def _write(self, f, data):
        writer = csv.writer(f, delimiter=self.delimiter,
            quotechar=self.quotechar, quoting=csv.QUOTE_MINIMAL,
            dialect=self.dialect)
        writer.writerows(data)

    def writeFile(self, name, data):
        with open(name, 'w', encoding='utf-8', newline='') as f:
            self._write(f, data)

    def appendFile(self, name, data):
        with open(name, 'a', encoding='utf-8', newline='') as f:
            self._write(f, data)

csvFileService = CsvFileService()

class CurrencyValue:
    def __init__(self, name, amount):
        self.name = name
        self.amount = amount

    def add(self, currencyValue):
        if self.name == currencyValue.name:
            self.amount += currencyValue.amount
        else:
            raise ValueError("Attempt to add {} to {}!".format(self.name, currencyValue.name))
        return self

    def convert(self, currname, currvalue):
        amount = self.amount * currvalue
        return CurrencyValue(currname, amount)

    def toTuple(self):
        return (self.name, self.amount)

    @staticmethod
    def fromTuple(tuple):
        return CurrencyValue(tuple[0], Decimal(tuple[1]))

class Wallet:
    def __init__(self, name):
        self.currencyValues = {}
        self.name = name
        self.fileName = name+'.csv'
        self.first = None

    def add(self, currencyValue):
        if not self.first:
            self.first = currencyValue
        self.currencyValues[currencyValue.name] = currencyValue

    def store(self):
        data = []
        for key in self.currencyValues:
            data.append(self.currencyValues[key].toTuple())

        csvFileService.writeFile(self.fileName, data)

    def load(self):
        data = csvFileService.readFile(self.fileName)
        for row in data:
            self.add(CurrencyValue.fromTuple(row))

    def get_currencies(self):
        list = []
        for key in self.currencyValues:
            list.append(self.currencyValues[key])
        return list

    def get_currency(self,name):
        return self.currencyValues[name]

class ExchangeProvider:
    def get_exchange_rates(self, date=None):
        return {}

class ExchangeRatesNBPHistoricProvider(ExchangeProvider):
    def __init__(self, currencyName, fileName, spread):
        self.spread = spread
        self.mindate = None
        self.maxdate = None
        self.currencyName = currencyName
        data = [(datetime.strptime(row[0], '%Y-%m-%d').date(), Decimal(row[1])) \
                    for row in (csvFileService.readFile(fileName)[1:])]
        self.data = sorted(data, key=lambda x: x[0])
        self.data_keys, _ = zip(*self.data)
        self._calculate_min_max()

    def _calculate_min_max(self):
       self.mindate = self.data[0][0]
       self.maxdate = self.data[-1][0]

    def _get_exchange_rate(self, row):
        price = row[1]
        bid = Decimal(1.0-self.spread)*price
        ask = Decimal(1.0+self.spread)*price
        return { self.currencyName: (bid,ask) }

    def get_exchange_rates(self, datestamp=None):
        if(datestamp != None and (datestamp<self.mindate or datestamp>self.maxdate)):
            raise ValueError("Cannot found requested date {}".format(datestamp))
        else:
            idx = bisect(self.data_keys, datestamp)
            if self.data_keys[idx] == datestamp:
                return self._get_exchange_rate(self.data[idx])
            else:
                return self._get_exchange_rate(self.data[idx-1])

#x = ExchangeRatesNBPHistoricProvider('GBP','gbp.csv',0.02)
#x.get_exchange_rates(x.mindate)

class ExchangeRatesNBPCurrentProvider(ExchangeProvider):
    def __init__(self, url='http://api.nbp.pl/api/exchangerates/tables/c'):
        self.url = url

    def get_exchange_rates(self, date=None):
        headers = {"Accept": "application/json"}

        response = requests.get(url=self.url, headers=headers)

        data = {}
        if(response.ok):
            jData = json.loads(response.content)
            rates = jData[0]['rates']
            for rate in rates:
                bid = Decimal(int(round(rate['bid'] * 10000.0))) / 10000
                ask = Decimal(int(round(rate['ask'] * 10000.0))) / 10000
                data[rate['code']] = (bid, ask)

            return data
        else:
            raise ValueError(response.status_code)

class TraderBot:
    def __init__(self, name, exchangeProvider):
        self.name = name
        self.wallet = Wallet(name+"_wallet")
        self.exchangeProvider = exchangeProvider

    def init(self):
        pass

    def give(self, currencyValue):
        self.wallet.add(currencyValue)

    def _load(self):
        self.wallet.load()
        self.baseCurrency = self.wallet.first
        self.load()

    def load(self):
        pass

    def _store(self):
        self.wallet.store()
        self.store()

    def store(self):
        pass

    def getCurrentExchangeRates(self, date=None):
        self.currentExchangeRates = self.exchangeProvider.get_exchange_rates(date)

    def calculateWalletValue(self):
        value = Decimal(0.0)
        for currencyValue in self.wallet.get_currencies():
            if currencyValue.name in self.currentExchangeRates:
                value += currencyValue.amount * self.currentExchangeRates[currencyValue.name][1]
            else:
                if currencyValue.name==self.baseCurrency.name:
                    value += currencyValue.amount
                else:
                    raise ValueError("Unsupported currency of "+currencyValue.name)
        self.currentWalletValue = value

    def storeWalletValue(self, todayDate=None):
        name = self.name + "_wallet_value.csv"
        if todayDate==None:
            todayDate = date.today()
        entry = (todayDate, self.currentWalletValue)
        csvFileService.appendFile(name, [entry])

    def pay(self, price):
        if self.baseCurrency.amount > price:
            self.baseCurrency.amount -= price
        else: raise ValueError(
            "Insufficient funds left {} to pay {}".format(self.baseCurrency.amount, price))

    def make_transaction(self, currencyValue):
        if currencyValue.amount<Decimal(0.01):
            return
        if currencyValue.name in self.currentExchangeRates:
            unit_price_idx = 1
            if currencyValue.amount<0:
                unit_price_idx = 0
            price = self.currentExchangeRates[currencyValue.name][unit_price_idx] * currencyValue.amount
            self.pay(price)
            self.wallet.get_currency(currencyValue.name).add(currencyValue)
        else: raise ValueError("Cannot buy or sell " + currencyValue.name)

        entry = (datetime.today(), currencyValue.name, currencyValue.amount)
        csvFileService.appendFile(self.name+"_transactions.csv", [ entry ])

    def think(self):
        pass

    def make_move(self, serialize=True,todayDate=None):
        if serialize:
            self._load()
        self.getCurrentExchangeRates(todayDate)
        self.think()
        if serialize:
            self._store()
        self.calculateWalletValue()
        self.storeWalletValue(todayDate)

    def initialize(self):
        self.baseCurrency = CurrencyValue('PLN', 1000)
        self.give(self.baseCurrency)
        self.give(CurrencyValue('GBP', 0))
        self._store()
        self.init()

class BotSimulator:
    def __init__(self, bot, exchange_rates_provider):
        self.bot = bot
        self.exchange_rates_provider = exchange_rates_provider

    def simulate(self):
        self.bot.initialize()
        currdate = self.exchange_rates_provider.mindate
        maxdate = self.exchange_rates_provider.maxdate
        i=0
        cnt=(maxdate - self.exchange_rates_provider.mindate).days
        percent = max(int(cnt / 100.0), 1)
        while currdate<maxdate:
            self.bot.make_move(False, currdate)
            currdate += timedelta(1)
            i+=1
            if i % percent == 0:
                print("Simulation {}% {} till {}".format(int(i / cnt * 100.0),currdate, maxdate))
        print("Simulation {}% {} till {}".format(100,currdate, maxdate))
