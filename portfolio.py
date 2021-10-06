from sqlite_driver import Sqlite
from price_frame import Price_frame
from betta_alpha import Bettas_list
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class Portfolio_maker:

    def __init__(self, price_frame):
        self.price_frame = price_frame
        db = Sqlite('Bettas&alphas.db')
        self.lot_size = db.companies_df.iloc[:-3, -1]

    def buy_sell_portfolio(self, date, buy_list, sell_list):
        '''
        Метод генерирует в текстовом виде структуру портфеля
        :param date:
        :param buy_list: список тикеров на покупку
        :param sell_list:  список тикеров на продажу
        :return: возвращаем текстовую строку
        '''

        buy_list_stocks = buy_list*self.lot_size
        sell_list_stocks = sell_list*self.lot_size


        result = f"Портфель сформирован на дату {date.date()}"
        result += 2 * "\n" + "Необходимо купить:"
        for index in buy_list.index:
            result += f"\nТикер: {index} - {buy_list_stocks[index]:.0f} шт"
        result += 2 * '\n' + "Необходимо продать:"
        for index in sell_list.index:
            result += f"\nТикер: {index} - {sell_list_stocks[index]:.0f} шт"
        return result


    def make_portfolio(self, buy_bettas, sell_bettas, money = 100000):
        '''
        Метод формирует портфель инвестиций
        :param buy_bettas: доли тикеров на покупку по датам
        :param sell_bettas: доли тикеров на продажу по датам
        :param money: количество денег для распределения
        :return: возвращает текстовое описание портфеля
        '''
        date = buy_bettas.index[-1]
        buy_bettas = buy_bettas.iloc[-1]
        sell_bettas = sell_bettas.iloc[-1]

        df_price = (self.price_frame.price_data_updated.loc[self.price_frame.price_data.index[-1], buy_bettas.index] * self.lot_size).dropna()

        buy_bettas = buy_bettas * money /  df_price
        sell_bettas = sell_bettas * money /  df_price

        buy_tickers = buy_bettas.dropna().astype('float').apply(np.round)
        sell_tickers = sell_bettas.dropna().astype('float').apply(np.round)

        result = self.buy_sell_portfolio(date,buy_list=buy_tickers,
                                         sell_list=sell_tickers)

        result += 2*'\n' + f"Для этого вам потребуется {(buy_tickers*df_price).dropna().sum().round()} руб."
        result += '\n' + f"Шортовые сделки вам дадут дополнительно {(sell_tickers*df_price).dropna().sum().round()} руб."
        return result
        #print((buy_bettas*df_price).dropna().sum(), (sell_bettas*df_price).dropna().sum())

    def portfolio_result(self, buy_bettas, sell_bettas, money = 100000):
        '''
        Метод считает изменение размера счета между периодами реструктуризации портфеля
        :param buy_bettas: доли тикеров на покупку по датам
        :param sell_bettas: доли тикеров на продажу по датам
        :param money: количество средств, относительно которых считаем доходность
        :return: возвращает DataSeries изменения размера счета, и текстовое описание структуры портфеля
        '''

        date = buy_bettas.index[0]
        buy_bettas = buy_bettas.iloc[0]
        sell_bettas = sell_bettas.iloc[0]

        tickers_prices = self.price_frame.price_data_updated

        df_price = (tickers_prices.loc[date, buy_bettas.index] * self.lot_size).dropna()
        buy_bettas = buy_bettas * money / df_price
        sell_bettas = sell_bettas * money / df_price


        tickers_to_buy = buy_bettas.dropna().astype('float').apply(np.round)
        tickers_to_sell = sell_bettas.dropna().astype('float').apply(np.round)

        result = self.buy_sell_portfolio(date, tickers_to_buy, tickers_to_sell)


        df_price = (tickers_prices.loc[date:, buy_bettas.index] * self.lot_size).dropna(axis=1)
        cash = money - (df_price.iloc[0]*tickers_to_buy).sum() + (df_price.iloc[0]*tickers_to_sell).sum()
        portfolio_res = cash + (df_price*tickers_to_buy).sum(axis=1) - (df_price*tickers_to_sell).sum(axis=1)

        return portfolio_res, result


def main():
    price_frame = Price_frame()
    bettas_list = Bettas_list(price_frame)
    buy_bettas, sell_bettas =  bettas_list.make_history_purchase_list(weeks_for_betta=35,
                                                                      weeks_for_filter=35,
                                                                      filter_number=1,
                                                                      listings=['Первый уровень'],
                                                                      date_start='2020-10-01')
    portfolio = Portfolio_maker(price_frame)

    print(portfolio.make_portfolio(buy_bettas,sell_bettas, money=100000))


if __name__ == '__main__':
    main()