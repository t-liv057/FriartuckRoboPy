
import logging
import pandas as pd
import numpy as np #needed for NaN handling
import math #ceil and floor are useful for rounding
from datetime import datetime, timedelta
from itertools import cycle
from get_stock_data import pipeliner as pipe
from friartuck.api import OrderType

import logging

log = logging.getLogger("friar_tuck")


def initialize(context, data):
    context.MaxCandidates=35
    context.MaxBuyOrdersAtOnce=6
    context.MyLeastPrice=.40
    context.MyMostPrice=1.99
    context.MyFireSalePrice=context.MyLeastPrice
    context.MyFireSaleAge=1

    # over simplistic tracking of position age
    context.age={}
    log.info(len(context.portfolio.positions))

    # Retrieve all open orders
    open_orders = get_open_orders()
    for stock_symbol in open_orders:
        log.info("open_order=%s" % open_orders[stock_symbol])

    context.assets = []
    context.symbol_metadata = {}

    if len(context.assets) <= 0:
        stock_boi = pipe()
        stock_frame = stock_boi.import_data()
        print (stock_frame.head(), stock_frame.info())
        context.assets = []
        context.symbol_metadata = {}

        for index, row in stock_frame.iterrows():
            if row['symbol'] not in context.portfolio.positions:
                asset = lookup_security(row['symbol'])
                context.symbol_metadata[asset] = row
                context.assets.append(asset)
                log.debug("symbol_metadata (%s)" % context.symbol_metadata)
    log.info(context.assets)
    my_account = context.account
    log.info(my_account)
    my_portfolio = context.portfolio
    log.info(my_portfolio)    


    #BuyFactor=.99
    SellFactor=1.01

    open_orders = get_open_orders()
    log.info(open_orders)

    # Order sell at profit target in hope that somebody actually buys it
    for stock in context.portfolio.positions:
        if not get_open_orders(stock):
            StockShares = context.portfolio.positions[stock].amount
            current_quote = data.current(stock, field='close')
            CostBasis = float(context.portfolio.positions[stock].cost_basis)

            PH = pd.DataFrame.from_dict(data.history([stock], frequency='1d', bar_count = 5, field='close'))
            PH_Avg = float(PH.mean())
            PH_Std = float(PH.std())
            if np.isnan(current_quote):
                pass # probably best to wait until nan goes away
            elif (
                datetime.today().strftime('%Y-%m-%d')>context.portfolio.positions[stock].created.strftime('%Y-%m-%d')
                and (
                    (current_quote<CostBasis*.98)
                    or
                    CostBasis*1.06<=current_quote
                    or 
                    (current_quote>CostBasis+.50*PH_Std)
                )
            ):
                try:
                    order_type = OrderType(price=current_quote*.98)
                    order_shares(stock, -StockShares, order_type=order_type, time_in_force='gtc')
                except Exception:
                    log.info(Exception)
                    pass

    # Buying when we have candidates and cash to spend 
    if len(context.assets) > 0 and context.portfolio.cash > 50:
        ThisBuyOrder = 0
        stock_number = 0
        while ThisBuyOrder <= context.MaxBuyOrdersAtOnce:
            if ThisBuyOrder < len(context.assets):
                valid_portfolio_value = context.portfolio.cash * .95
                stock_data = context.assets[stock_number]
                stock_number += 1
                if stock_data not in context.portfolio.positions:
                    stock = stock_data.symbol
                    current_quote = data.current(stock_data, field='close')
                    if np.isnan(current_quote):
                        pass # probably best to wait until nan goes away
                    else:
                        log.info(stock)
                        quote = stock_frame.loc[(stock_frame['Symbol'] == str(stock))]
                        quote_last = quote.iloc[0]['LastSale']
                        log.info(quote_last)
                        try:
                            cash_amount = .10*valid_portfolio_value
                            # If within 2%
                            shares = math.ceil(cash_amount/current_quote)
                            order_type = OrderType(price=current_quote*1.02)
                            #value_to_order = percent_to_order * valid_portfolio_value
                            order_shares(stock_data, shares, order_type=order_type, time_in_force='gtc')
                            ThisBuyOrder += 1
                        except Exception:
                            log.info(Exception)
        context.assets = []


def on_market_open(context, data):
    # (optional) is called when the market opens or after a restart of the process during the live market
    # Note: within this method "initialize", the parameter "data" should primarily be used to load historical data for initialization, the use of data.current(...) method is best within the handle_data(...) method.
    log.info(context.portfolio.positions)
def handle_data(context, data):
    # (optional) is called when the market opens or after a restart of the process during the live market
    # Note: within this method "initialize", the parameter "data" should primarily be used to load historical data for initialization, the use of data.current(...) method is best within the handle_data(...) method.
    log.info(context.assets)
    my_account = context.account
    log.info(my_account)
    my_portfolio = context.portfolio
    log.info(my_portfolio)    


    #BuyFactor=.99
    SellFactor=1.01

    open_orders = get_open_orders()
    log.info(open_orders)

    # Order sell at profit target in hope that somebody actually buys it
    for stock in context.portfolio.positions:
        if not get_open_orders(stock):
            StockShares = context.portfolio.positions[stock].amount
            current_quote = data.current(stock, field='close')
            CostBasis = float(context.portfolio.positions[stock].cost_basis)

            PH = pd.DataFrame.from_dict(data.history([stock], frequency='1d', bar_count = 5, field='close'))
            PH_Avg = float(PH.mean())
            PH_Std = float(PH.std())
            if np.isnan(current_quote):
                pass # probably best to wait until nan goes away
            elif (
                datetime.today().strftime('%Y-%m-%d')>context.portfolio.positions[stock].created.strftime('%Y-%m-%d')
                and (
                    (current_quote<CostBasis*.98)
                    or
                    CostBasis*1.06<=current_quote
                    or 
                    (current_quote>CostBasis+.50*PH_Std)
                )
            ):
                try:
                    order_type = OrderType(price=current_quote*.98)
                    order_shares(stock, -StockShares, order_type=order_type, time_in_force='gtc')
                except Exception:
                    log.info(Exception)
                    pass
def log_open_orders():
    oo = get_open_orders()
    if len(oo) == 0:
        return
    for stock, orders in oo.iteritems():
        for order in orders:
            message = 'Found open order for {amount} shares in {stock}'
            log.info(message.format(amount=order.amount, stock=stock))

def get_percent_held(context, security, portfolio_value):
    """
    This calculates the percentage of each security that we currently
    hold in the portfolio.
    """
    if security in context.portfolio.positions:
        position = context.portfolio.positions[security]
        value_held = position.last_sale_price * position.amount
        percent_held = value_held / float(portfolio_value)
        return percent_held
    else:
        # If we don't hold any positions, return 0%
        return 0.0
