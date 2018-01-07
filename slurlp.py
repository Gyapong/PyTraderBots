from datetime import date
from datetime import timedelta
from datetime import datetime
import requests
import json
import pandas as pd

#parametry skryptu
currency = 'gbp'
unit = 1
startdate = date(2002,1,2)
enddate = date.today()

#parametry techniczne
outfiledir = './'
outfilename = outfiledir + currency+'.csv'
nbptable = 'A'
maxperiodlen = 93
baseurl = 'http://api.nbp.pl/api/exchangerates/rates/{table}/{code}/{startDate}/{endDate}/'

#procedury
def make_periods():
    periods = []
    currdate = startdate
    maxdelta = timedelta(maxperiodlen)
    nextday = timedelta(1)
    while(currdate < enddate):
        periodlen = min(enddate - currdate, maxdelta)
        periods.append( (currdate, currdate + periodlen) )
        currdate += periodlen + nextday
    return periods

def get_exchange_rates_for(period):
    currenturl = baseurl.format(table = nbptable, code = currency,
        startDate = period[0], endDate = period[1])
    headers = {"Accept": "application/json"}

    response = requests.get(url=currenturl, headers=headers)

    data = []
    if(response.ok):
        jData = json.loads(response.content)
        rates = jData['rates']
        for row in rates:
            data.append( (datetime.strptime(row['effectiveDate'], '%Y-%m-%d'), row['mid']) )
    else:
        print("Error reading data for {}".format(currenturl))

    return data

def save(data):
    labels = ['ds', 'y']
    df = pd.DataFrame.from_records(data, columns=labels)
    df.to_csv(outfilename, encoding='utf-8', index=False)

def slurlp():
    periods = make_periods()
    exchangerates = []
    i = 1
    exlen = len(periods)
    for period in periods:
        exchangerates.extend( get_exchange_rates_for(period) )
        print("downloading {} of {}".format(i, exlen))
        i += 1
    save(exchangerates)

#zasysamy
slurlp()
