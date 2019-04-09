from datetime import datetime, timedelta
import logging
import pandas as pd
from friartuck.api import OrderType
import numpy as np #needed for NaN handling
from numpy import random
import math #ceil and floor are useful for rounding
from iex import reference,Stock,market
from pandas import Series
import json


hist = pd.DataFrame(get_corporate_actions(output_format='pandas')[0])
intra = pd.DataFrame(get_stats_intraday(output_format='pandas'))

#action.set_index('date', inplace=True)

print (hist.head(),hist.head(),intra.info(),intra.head())
#stock.join(action, how='left')

stocks = stocks.loc[stocks['type']== 'cs']
stocks = stocks.loc[stocks['isEnabled'] == True]
stocks['marketCap'] = Series([])
stocks['latestPrice'] = Series([])
stocks['marketCap'].fillna(0)
stocks['latestPrice'].fillna(0)

print (stocks.head(),stocks.info())

for index, row in stocks.iterrows():
	stock = Stock(str(row['symbol']))
	stock_stats = pd.DataFrame(stock.get_quote(), index=[0])
	stock_stats = stock_stats[['marketCap','symbol','latestPrice']]
	stocks.loc[stocks['symbol'] == row['symbol']] = stock_stats.iloc[0]['marketCap']
	stocks.loc[stocks['symbol'] == row['symbol']] = stock_stats.iloc[0]['latestPrice']


	#print (row['symbol'])
	#$print (stock_stats.info(),stocks.info())


stocks = stocks.loc[stock['marketCap'] > 0]
stocks = stocks.loc[(stock['latestPrice'] > 0.40)& (stock['latestPrice'] <= 2.5) ]
print (stocks.head(),stocks.info())