from price_frame import Price_frame
from sqlite_driver import Sqlite
import pandas as pd
from scipy import stats
from tqdm import tqdm, trange
import numpy as np
from filters import *

class Bettas_alphas_creator():
    def __init__(self):
        self._price = Price_frame()
        print("################################")
        print("Bettas_alphas_creator object created")
        print("################################")


    @staticmethod
    def regression_summary(data_table, ticker_name):
        # print (data_table)
        try:
            if data_table[ticker_name].isna().sum() == 0 and len(data_table) != 0:
                data_table[['IMOEX', ticker_name]] = data_table.loc[:, ['IMOEX', ticker_name]].pct_change()
                data_table.dropna(inplace=True)
                data_table['IMOEX'] = data_table['IMOEX'] - data_table['Bonds']
                data_table[ticker_name] = data_table[ticker_name] - data_table['Bonds']
                X = data_table['IMOEX']
                y = data_table[ticker_name]
                slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
                return (slope, intercept, r_value ** 2)
            else:
                return (np.nan, np.nan, np.nan)
        except Exception:
            return (np.nan, np.nan, np.nan)

    def create_bettas(self, weeks, start_date='2000-01-01'):

        df_result = self._price.price_data.loc[pd.to_datetime(start_date) - pd.offsets.DateOffset(weeks=weeks):]
        date_range = pd.date_range(start=start_date,
                                   end=df_result.index[-1], freq='W-MON')
        bettas_frame = pd.DataFrame(index=date_range,
                                    columns=df_result.columns[2:])
        intercept_frame = pd.DataFrame(index=date_range,
                                       columns=df_result.columns[2:])
        bettas_frame.index.name = 'DATE'
        intercept_frame.index.name = 'DATE'

        for index in date_range:
            df_sliced = df_result.loc[index - pd.offsets.DateOffset(weeks=weeks):index, :].iloc[:-1]
            slope_arr = []
            intercept_arr = []
            for ticker in df_sliced.columns[2:]:
                slope, intercept, r_value = Bettas_alphas_creator.regression_summary(
                    df_sliced.loc[:, ['IMOEX', 'Bonds', ticker]], ticker)

                slope_arr.append(slope)
                intercept_arr.append(intercept)
            bettas_frame.loc[index, :] = slope_arr
            intercept_frame.loc[index, :] = intercept_arr
        bettas_frame.dropna(inplace=True, how='all')
        intercept_frame.dropna(inplace=True, how='all')
        return bettas_frame, intercept_frame

    def group_bettas_alphas(self):
        db = Sqlite('Bettas&alphas.db')
        conn = db.get_connection
        final_table_columns = pd.concat([pd.Series(['BETTA', 'DATE']), self._price.companies_list])
        df_result = pd.DataFrame(columns=final_table_columns)

        for week in range(1, 51):
            if db.check_table_exists(f'Bettas_{week}'):
                df = pd.read_sql(f"Select * from Bettas_{week}",
                                 con=conn)
                df = df.rename(columns={"index": "DATE"})
                df['BETTA'] = f'Bettas_{week}'
                df_result = df_result.append(df)
        df_result.reset_index(drop=True, inplace=True)
        df_result.to_sql('Bettas', con=conn, if_exists='replace')
        print("Table Bettas succesfully merged")

        final_table_columns = pd.concat([pd.Series(['ALPHA', 'DATE']), self._price.companies_list])
        df_result = pd.DataFrame(columns=final_table_columns)
        for week in range(1, 51):
            if db.check_table_exists(f'Alphas_{week}'):
                df = pd.read_sql(f"Select * from Alphas_{week}",
                                 con=conn)
                df = df.rename(columns={"index": "DATE"})
                df['ALPHA'] = f'Alphas_{week}'
                df_result = df_result.append(df)
        df_result.reset_index(drop=True, inplace=True)
        df_result.to_sql('Alphas', con=conn, if_exists='replace')
        print("Table Alphas succesfully merged")

    def update_bettas_lists(self):

        db = Sqlite('Bettas&alphas.db')
        conn = db.get_connection

        cursor = conn.cursor()

        if db.check_table_exists('Bettas'):
            df_bettas = pd.read_sql('SELECT * FROM Bettas',
                                    con=conn,
                                    parse_dates=['DATE'],
                                    index_col='index'
                                    )
            df_alphas = pd.read_sql('SELECT * FROM Alphas',
                                    con=conn,
                                    parse_dates=['DATE'],
                                    index_col='index'
                                    )
        else:
            df_bettas = pd.DataFrame(columns=pd.concat([pd.Series(['BETTA', 'DATE']), self._price.companies_list]))
            df_alphas = pd.DataFrame(columns=pd.concat([pd.Series(['ALPHA', 'DATE']), self._price.companies_list]))

        pbar = trange(5,51)

        for week in pbar:
            date_max = df_bettas[df_bettas['BETTA'] == f'Bettas_{week}']['DATE'].max()

            pbar.set_description(f"Creating Bettas and Alphas with week = {week}")
            if date_max not in [pd.NaT, np.nan]:
                bettas_frame, alphas_frame = self.create_bettas(week,
                                                                start_date=date_max + pd.offsets.DateOffset(weeks=1))
            else:
                bettas_frame, alphas_frame = self.create_bettas(week)

            bettas_frame.reset_index(inplace=True)
            bettas_frame['BETTA'] = f'Bettas_{week}'

            alphas_frame.reset_index(inplace=True)
            alphas_frame['ALPHA'] = f'Alphas_{week}'
            df_bettas = df_bettas.append(bettas_frame)
            df_alphas = df_alphas.append(alphas_frame)

        df_bettas.drop_duplicates(subset=['BETTA', 'DATE'], inplace=True)
        df_alphas.drop_duplicates(subset=['ALPHA', 'DATE'], inplace=True)

        df_bettas.reset_index(inplace=True, drop=True)
        df_alphas.reset_index(inplace=True, drop=True)

        df_bettas.to_sql(f"Bettas", con=conn, if_exists='replace')
        df_alphas.to_sql(f"Alphas", con=conn, if_exists='replace')


class Bettas_list():
    def __init__(self, price_frame):
        self.price = price_frame
        print("################################")
        print("Bettas_list object loaded")
        print("################################")
        self.Filters = {
            0: Filter(),
            1: Alpha_filter(),
        }

    def make_history_purchase_list(self, weeks_for_betta=30,
                                   weeks_for_filter=30,
                                   filter_number=0,
                                   listings=["Первый уровень", "Второй уровень"],
                                   date_start = '1970-01-01',
                                   date_end = '2099-01-01',
                                   ):

        db = Sqlite('Bettas&alphas.db')
        conn = db.get_connection

        filtering_obj = self.Filters[filter_number]

        first_date = filtering_obj.set_filter_period(weeks_for_filter)
        listings = self.price.build_listings(listings)

        if db.check_table_exists('Bettas'):
            bettas_frame = db.get_bettas(weeks_for_betta)
            bettas_frame = bettas_frame.loc[first_date:, bettas_frame.columns.isin(listings)]


        else:
            print(f"Table Bettas_{weeks_for_betta} not exists!")
            return np.nan, np.nan

        bettas_frame = bettas_frame.loc[date_start:date_end,:]

        buy_bettas = pd.DataFrame(index=bettas_frame.index, columns=bettas_frame.columns)
        sell_bettas = pd.DataFrame(index=bettas_frame.index, columns=bettas_frame.columns)


        j = 0
        buying_num = 0
        selling_num = 0

        for i, row in bettas_frame.iterrows():

            # Getting companies with betta > -2

            row_filtered = row[row >= 0]
            row_filter_a_z, row_filter_b_z = filtering_obj.filter_columns(row_filtered)

            # Определяем значение Бэтта относительно которого идут расчеты
            betta_mean = 1  # row_filtered.mean()

            # Делает Betta с учетом фильтра
            bettas_b_1 = row_filter_a_z[row_filter_a_z <= betta_mean]
            weights_b_1 = betta_mean - bettas_b_1
            bettas_b_1 = weights_b_1 / (bettas_b_1 * weights_b_1).sum()

            bettas_a_1 = row_filter_b_z[row_filter_b_z > betta_mean]
            weights_a_1 = bettas_a_1 - betta_mean
            bettas_a_1 = weights_a_1 / (bettas_a_1 * weights_a_1).sum()

            sum_weight = bettas_b_1.sum()
            if sum_weight != 0:
                bettas_b_1 = bettas_b_1 / sum_weight
                bettas_a_1 = bettas_a_1 / sum_weight
            else:
                bettas_b_1 = bettas_b_1 * sum_weight
                bettas_a_1 = bettas_a_1 * sum_weight

            buy_bettas.loc[i, :] = bettas_b_1
            sell_bettas.loc[i, :] = bettas_a_1

            # Соберем статистику по покупающим и продающим инструментам
            j += 1
            selling_num += len(bettas_a_1)
            buying_num += len(bettas_b_1)
        if j!=0:
            print("Статистика по среднему распределению в шорт и лонг:")
            print(selling_num / j, buying_num / j)

        return (buy_bettas, sell_bettas)


    def make_history_purchase_list_zero(self, weeks_for_betta=30,
                                   weeks_for_filter=30,
                                   filter_number=0,
                                   listings=["Первый уровень", "Второй уровень"],
                                   date_start = '1970-01-01',
                                   date_end = '2099-01-01',
                                   ):

        db = Sqlite('Bettas&alphas.db')
        conn = db.get_connection

        filtering_obj = self.Filters[filter_number]

        first_date = filtering_obj.set_filter_period(weeks_for_filter)
        listings = self.price.build_listings(listings)

        if db.check_table_exists('Bettas'):
            bettas_frame = db.get_bettas(weeks_for_betta)
            bettas_frame = bettas_frame.loc[first_date:, bettas_frame.columns.isin(listings)]


        else:
            print(f"Table Bettas_{weeks_for_betta} not exists!")
            return np.nan, np.nan

        bettas_frame = bettas_frame.loc[date_start:date_end,:]

        buy_bettas = pd.DataFrame(index=bettas_frame.index, columns=bettas_frame.columns)
        sell_bettas = pd.DataFrame(index=bettas_frame.index, columns=bettas_frame.columns)


        j = 0
        buying_num = 0
        selling_num = 0

        for i, row in bettas_frame.iterrows():

            # Getting companies with betta > -2

            #row_filtered = row[row >= ]
            row_filter_a_z, row_filter_b_z = filtering_obj.filter_columns(row)

            # Определяем значение Бэтта относительно которого идут расчеты
            betta_mean = 0  # row_filtered.mean()

            print(row)

            # Делает Betta с учетом фильтра
            bettas_b_1 = row_filter_a_z[row_filter_a_z <= betta_mean]

            weights_b_1 = betta_mean - bettas_b_1
            bettas_b_1 = weights_b_1 / (bettas_b_1 * weights_b_1).sum()

            bettas_a_1 = row_filter_b_z[row_filter_b_z > betta_mean]
            weights_a_1 = bettas_a_1 - betta_mean
            bettas_a_1 = weights_a_1 / (bettas_a_1 * weights_a_1).sum()

            sum_weight = bettas_b_1.sum()
            if sum_weight != 0:
                bettas_b_1 = bettas_b_1 / sum_weight
                bettas_a_1 = bettas_a_1 / sum_weight
            else:
                bettas_b_1 = bettas_b_1 * sum_weight
                bettas_a_1 = bettas_a_1 * sum_weight

            buy_bettas.loc[i, :] = bettas_b_1
            sell_bettas.loc[i, :] = bettas_a_1

            # Соберем статистику по покупающим и продающим инструментам
            j += 1
            selling_num += len(bettas_a_1)
            buying_num += len(bettas_b_1)
            break
        if j!=0:
            print("Статистика по среднему распределению в шорт и лонг:")
            print(selling_num / j, buying_num / j)

        #return (buy_bettas, sell_bettas)