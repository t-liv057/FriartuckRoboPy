from datetime import datetime, timedelta, date
import pandas as pd
from iexfinance import Stock, get_historical_data,get_available_symbols
from pandas import Series
import csv 
import urllib.request
import os
import requests 
import time
import matplotlib.pyplot as plt


class pipeliner:

    stock_list_path = "stock_list.csv"
    final_list_path = "stocklist.csv.csv"
    finald_list_no_filter_path = "stocks_before_filter.csv"



    def download(self): 
        #Pull stock list to scan through
        r = requests.get("https://www.nasdaq.com/screening/companies-by-industry.aspx?region=North+America&marketcap=Nano-cap&render=download") 
        with open("stock_list.csv", 'wb') as fd: 
            for chunk in r.iter_content(chunk_size=10*1024*1024): 
                fd.write(chunk) 
        while os.stat("stock_list.csv").st_size == 0:
            time.sleep(3)

    def prev_weekday(adate):
        while adate.weekday() > 4:
            adate -= timedelta(days=1)
        return adate

    def import_data(self):
        self.download()
        stock_list = pd.read_csv("stock_list.csv")
        os.remove("stock_list.csv")


        stocks = pd.DataFrame(get_available_symbols(output_format='pandas'))
        stocks = stocks.loc[stocks['type']== 'cs']

        stocks = stocks.merge(stock_list, how='inner',left_on='symbol',right_on='Symbol')


        #Plainly filter list to reduce further analysis load
        stocks = stocks.loc[(stocks['MarketCap'] > 0) & stocks['MarketCap'].notnull()]
        stocks = stocks.loc[stocks['Industry'].notnull()]
        stocks = stocks.loc[(stocks['LastSale'] > .25)& (stocks['LastSale'] <= 5.0) ]

        #add columns to df that we will go through and fill for analysis
        stocks['profitMargin'] = Series([])
        stocks['day50MovingAvg'] = Series([])
        stocks['beta'] = Series([])

        stocks['avg_daily_change_30'] = Series([])
        stocks['avg_change_over_time_30'] = Series([])
        stocks['avg_daily_change_5'] = Series([])
        stocks['avg_change_over_time_5'] = Series([])
        stocks['last_change_percent'] = Series([])
        stocks['avg_close_30'] = Series([])
        stocks['std_close_30'] = Series([])
        stocks['avg_close_5'] = Series([])
        stocks['std_close_5'] = Series([])

        stocks['avg_volume_30'] = Series([])
        stocks['avg_volume_5'] = Series([])
        stocks['last_volume'] = Series([])

        stocks['shortRatio'] = Series([])




        
        stocks.reset_index(inplace=True,drop=True)
        print (stocks.head(), stocks.info())

        for index, row in stocks.iterrows():
            #print (index, row)
            #Pause so api doesn't kick us out
            if index%7==0 and index != 0:
                print ("Waiting 3 seconds")
                time.sleep(3)

            stock = Stock(str(row['symbol']))

            stock_stats = pd.DataFrame(stock.get_key_stats(),index=[0])
            #Five day timeseries avg for values
            stock_book = pd.DataFrame(stock.get_time_series(output_format='pandas'))
            stock_book_3 = stock_book.tail(3)
            #Close to real time
            #stock_quote = pd.DataFrame(stock.get_quote(), index=[0])
            
            #print (stock_move.head(), stock_move.info())
            #print (stock_stats)
            print (index)
            #print (stock_stats)

            stock_stats = stock_stats[['profitMargin','day50MovingAvg','beta','shortRatio']]

            stocks.loc[index,'profitMargin'] = stock_stats.iloc[0]['profitMargin']
            stocks.loc[index,'day50MovingAvg'] = stock_stats.iloc[0]['day50MovingAvg']
            stocks.loc[index,'beta'] = stock_stats.iloc[0]['beta']
            stocks.loc[index,'shortRatio'] = stock_stats.iloc[0]['shortRatio']


            stocks.loc[index,'avg_daily_change_30'] = stock_book['changePercent'].mean()
            stocks.loc[index,'avg_change_over_time_30'] = stock_book['changeOverTime'].mean()

            stocks.loc[index,'avg_daily_change_5'] = stock_book_3['changePercent'].mean()
            stocks.loc[index,'avg_change_over_time_5'] = stock_book_3['changeOverTime'].mean()
            stocks.loc[index,'last_change_percent'] = stock_book.loc[len(stock_book)-1,'changePercent']

            stocks.loc[index,'avg_close_30'] = stock_book['close'].mean()
            stocks.loc[index,'std_close_30'] = stock_book['close'].std()
            stocks.loc[index,'avg_close_5'] = stock_book_3['close'].mean()
            stocks.loc[index,'std_close_5'] = stock_book_3['close'].std()

            stocks.loc[index,'avg_volume_30'] = stock_book['volume'].mean()
            stocks.loc[index,'avg_volume_5'] = stock_book_3['volume'].mean()
            stocks.loc[index,'last_volume'] = stock_book.loc[len(stock_book)-1,'volume']
            #if index > 50:
                #break

        stocks.to_csv('stocks_before_filter.csv')
        stocks = stocks.loc[(stocks['LastSale'] < (stocks['avg_close_30'] - (1.40*stocks['std_close_30']))) &(stocks['LastSale'] >= (stocks['avg_close_30'] - (2.00*stocks['std_close_30'])))]
        stocks = stocks.loc[((stocks['avg_volume_5']/stocks['avg_volume_30']) > 1.02)]

        stocks.sort_values('shortRatio', inplace=True)

        stocks.reset_index(inplace=True,drop=True)
        #print (stocks.head(20),stocks.info())
        stocks.to_csv('stocklist.csv')
        return (stocks)