import yfinance as yf
import pandas as pd
import numpy as np

def check_is_redempted(equity_names, start_date, end_date, kib):
    file_path = './materials/ticker_symbol.xlsx'
    df = pd.read_excel(file_path)

    equity_name_list = list(df['equity_name'])
    ticker_symbol_list = list(df['ticker_symbol'])

    ticker_db = {}
    for i in range(len(equity_name_list)):
        ticker_db[equity_name_list[i]] = ticker_symbol_list[i]

    tickers = []
    num_equities = len(equity_names)
    for i in range(num_equities):
        if equity_names[i] not in ticker_db:
            print(equity_names[i] + "의 Ticker가 DB에 없음")
            return None, None
        tickers.append(ticker_db[equity_names[i]])

    redemption_flag = True
    worst_performer = 100
    for i in range(num_equities):
        x = yf.Ticker(tickers[i])
        x_data = x.history(start=start_date, end=end_date)
        x_close = x_data['Close']
        x_initial = x_close.iloc[0]
        x_barrier = x_initial * (kib / 100)
        x_min = x_close.min()

        loss = x_min < x_barrier

        if loss:
            worst_performer = min(worst_performer, x_min / x_initial)
            redemption_flag = False

    if redemption_flag:
        return 1, 0
    else:
        loss_rate = (1 - worst_performer) * 100
        return 0, loss_rate