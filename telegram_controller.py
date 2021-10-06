from price_frame import Price_frame
from sqlite_driver import Sqlite
from betta_alpha import Bettas_list
from benchmark import Benchmark
from portfolio import Portfolio_maker
import matplotlib.pyplot as plt
import datetime
from telegram_lib import *
import os
import pickle as pl

class Telegram_controller():
    def __init__(self):
        self.price_frame = Price_frame()


    def make_history(self, history, cid):
        '''
        Метод просчитывает исторические результаты на основании данной стратегии
        :param history:
        :param cid:
        :return:
        '''
        strategy_maker = Bettas_list(self.price_frame)
        history_maker = Benchmark(self.price_frame)
        buy_bettas, sell_bettas = strategy_maker.make_history_purchase_list(
            weeks_for_betta=history.weeks_for_betta,
            weeks_for_filter=history.weeks_for_filter,
            filter_number=history.filter_type,
            listings=['Первый уровень'],
            date_start=history.from_date)
        history_maker.benchmark(buy_bettas, sell_bettas, hold_period=history.weeks_to_hold)
        result, portfolio = history_maker.make_statistics(history.from_date,
                                                      weeks_history=history.weeks_to_hold,
                                                      )

        files = []

        file_path = os.path.join(TMP_DIR, f'{cid}.png')
        income_fig_path = os.path.join(TMP_DIR, f'{cid}.pkl')
        if os.path.isfile(income_fig_path):
            with open(income_fig_path, 'rb') as f:
                income_fig = pl.load(f)
        else:
            income_fig = plt.figure(cid)
        income_fig.suptitle('Доход с учетом сложных процентов')
        ax = income_fig.gca()
        ((portfolio + 1).cumprod() * 100).plot(figsize=(10, 6), ax=ax, label=history.weeks_to_hold, grid=True)
        lines = ax.get_lines()
        for index, line in enumerate(lines):
            line.set_color(COLORS[index % len(COLORS)])
        ax.legend()
        ax.set_ylabel('Проценты')
        ax.set_xlabel('Дата')
        income_fig.savefig(file_path)
        with open(income_fig_path, 'wb') as f:
            pl.dump(income_fig, f)
        files.append(file_path)
        plt.close(income_fig)

        scatter_fig_path = os.path.join(TMP_DIR, f'{cid}_scatter.pkl')
        if os.path.isfile(scatter_fig_path):
            with open(scatter_fig_path, 'rb') as f:
                scatter_fig = pl.load(f)
        else:
            scatter_fig = plt.figure(f'{cid}_scatter', figsize=(10, 6))

        scatter_fig.suptitle('Разброс доходность по датам пересчета')
        ax = scatter_fig.gca()
        ax.set_ylabel('Проценты')
        ax.set_xlabel('Дата')
        ax.grid(True)
        file_path_scatter = os.path.join(TMP_DIR, f'{cid}_scatter.png')
        ax.scatter(portfolio.index, portfolio, label=history.weeks_to_hold,
                   c=COLORS[(len(lines) - 1) % len(COLORS)])
        ax.hlines(0, xmin=portfolio.index[0], xmax=portfolio.index[-1], color='k')
        ax.legend()
        scatter_fig.savefig(file_path_scatter)
        with open(scatter_fig_path, 'wb') as f:
            pl.dump(scatter_fig, f)
        files.append(file_path_scatter)
        plt.close(scatter_fig)

        return result,files

    def make_portfolio(self, portfolio_params):
        '''
        Метод создает портфель инвестиций на основании параметров
        :param portfolio_params:
        :return:
        '''
        strategy_maker = Bettas_list(self.price_frame)
        portfolio_maker = Portfolio_maker(self.price_frame)
        buy_bettas, sell_bettas = strategy_maker.make_history_purchase_list(
            weeks_for_betta=portfolio_params.weeks_for_betta,
            weeks_for_filter=portfolio_params.weeks_for_filter,
            filter_number=portfolio_params.filter_type,
            listings=['Первый уровень'],
            date_start=(datetime.datetime.today() - datetime.timedelta(days=31)).date())
        portfolio_text = portfolio_maker.make_portfolio(buy_bettas, sell_bettas, money=portfolio_params.money)
        return portfolio_text

    def make_followed_portfolio(self, params, cid):
        '''
        Метод считает доходность текущего портфеля
        :param params:
        :param cid:
        :return:
        '''
        strategy_maker = Bettas_list(self.price_frame)
        buy_bettas, sell_bettas = strategy_maker.make_history_purchase_list(
            weeks_for_betta=params[1],
            weeks_for_filter=params[3],
            filter_number=params[2],
            listings=['Первый уровень'],
            date_start=(params[4] - datetime.timedelta(days=params[4].weekday())).strftime(format='%Y-%m-%d'),
            date_end=datetime.datetime.now()
        )

        if len(buy_bettas) != 0:
            portfolio_maker = Portfolio_maker(self.price_frame)
            portfolio_result, portfolio_struct = portfolio_maker.portfolio_result(buy_bettas, sell_bettas, money=params[5])
            figure = plt.figure(f'portfolio_{cid}', figsize=(10,6))
            ax = figure.gca()
            portfolio_result.plot(ax=ax)
            ax.grid()

            figure.savefig(os.path.join(TMP_DIR,f'portfolio_{cid}.png'))
            plt.close(figure)
            return portfolio_struct
        else:
            return 0