import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from cycler import cycler
import os
import pickle as pl

FIGURE_BASE_DIR = 'tmp'
COLORS = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

class Benchmark:

    def __init__(self, price_frame):
        self.price_frame = price_frame
        print("################################")
        print("Benchmark object loaded")
        print("################################")
        self.weeks_history = 10
        self.hold_period = 10

    def benchmark(self, buy_bettas, sell_bettas, hold_period=10):
        use_short = True
        self.hold_period = hold_period
        buy_bettas = buy_bettas.loc[self.price_frame.price_data.index[0]:]
        sell_bettas = sell_bettas.loc[self.price_frame.price_data.index[0]:]

        df_price = self.price_frame.price_data_updated.loc[buy_bettas.index[0]:, buy_bettas.columns].resample('W').first()
        df_price.index = df_price.index + pd.offsets.DateOffset(days=-6)
        df_price = df_price.dropna(how='all')

        df_portfolio_change = pd.Series(index=df_price.index[hold_period:],
                                        dtype=np.dtype('float64'))

        for ix, i in enumerate(buy_bettas.index[hold_period:]):
            timeshift_past = buy_bettas.index[ix]
            price_change = ((df_price.loc[timeshift_past:i].pct_change(periods=1) + 1).cumprod() - 1).iloc[-1]
            buy_change = (price_change * buy_bettas.loc[timeshift_past]).sum()
            sell_change = (price_change * sell_bettas.loc[timeshift_past]).sum()

            # if i == pd.to_datetime('2014-03-24'):
            '''print(f"time: {i}, buy_change: {buy_change:.3f}, sell_change: {sell_change:.3f}, diff: {buy_change-sell_change:.3f}")
            print(price_change)
            print(buy_bettas.loc[timeshift_past])
            print(df_price.loc[timeshift_past:i, 'MSTT'])'''
            if use_short == True:
                df_portfolio_change[i] = buy_change - sell_change
            else:
                df_portfolio_change[i] = buy_change

        df_portfolio_change.sort_index(inplace=True)
        df_portfolio_change.dropna(inplace=True)
        self.portfolio = df_portfolio_change
        print("#########################################")
        print("Building history portfolio completed")
        print("#########################################")

    def make_statistics(self, date='2011-01-01', weeks_history=10):
        self.weeks_history = weeks_history
        # portfolio[date::HOLD_PERIOD].plot(figsize=(10,6))
        portfolio_sliced = self.portfolio[date::self.hold_period]

        simple_interest = portfolio_sliced.sum()
        compound_interest = (portfolio_sliced + 1).cumprod()[-1] - 1
        stdev_loss = portfolio_sliced[portfolio_sliced < 0].std()
        mean_loss = portfolio_sliced[portfolio_sliced < 0].mean()
        max_loss = portfolio_sliced.min()
        max_loss_idx = portfolio_sliced.idxmin()
        mean_profit = ((portfolio_sliced.mean() + 1) ** (52.179 / self.hold_period) - 1)
        result = f"Недель для расчета: {self.weeks_history}"
        result += '\n' + f"Недель удержания позиции: {self.hold_period}"
        result += 2*'\n' +f"Простые проценты: {simple_interest * 100:.2f}%"
        result += '\n' + f"Сложные проценты: {compound_interest * 100:.2f}%"
        result += '\n' + f"Максимальный убыток: {max_loss * 100:.2f}%"
        result += '\n' + f"Дата максимального убытка: {max_loss_idx.date()}"
        result += '\n' + f"Среднее значение убытков: {mean_loss * 100:.2f}%"
        result += '\n' + f"Стандартное отклонение убытков: {stdev_loss * 100:.2f}%"
        result += '\n' + f"Ожидаемая доходность в год: {mean_profit * 100:.2f}%"


        return result, portfolio_sliced

