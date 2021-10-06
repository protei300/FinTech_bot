from sqlite_driver import Sqlite
import datetime

class Price_frame():
    SPECIAL_TICKERS = ['IMOEX', '3-BONDS', '5-BONDS']

    def __init__(self):
        db = Sqlite("Bettas&alphas.db")
        df_companies = db.companies_df
        self.listing = df_companies.loc[~df_companies.index.isin(self.SPECIAL_TICKERS), ['LIST_SECTION']]
        self.listing.reset_index(inplace=True)
        self.create_prices_from_sql()

        # self.create_prices_from_file()

    def create_prices_from_sql(self):
        from_date = '2000-01-01'

        db = Sqlite("Bettas&alphas.db")
        df_quotations = db.quotations_table(from_date=from_date)
        df_companies = db.companies_df
        tickers_list = self.listing['TRADE_CODE']

        df_index = df_quotations[df_quotations['TRADE_CODE'] == 'IMOEX']
        df_index = df_index.loc[:, ['DATE', 'OPEN']]
        df_index.columns = ['DATE', 'IMOEX']
        df_index.set_index('DATE', inplace=True)
        df_index.sort_index(ascending=True, inplace=True)
        df_result = df_index.copy()


        df_bonds = df_quotations[df_quotations['TRADE_CODE'] == '3-BONDS']
        df_bonds = df_bonds.loc[:, ['DATE', 'OPEN']]
        df_bonds.columns = ['DATE', 'Bonds']
        df_bonds.set_index('DATE', inplace=True)
        df_bonds = pow(df_bonds / 100 + 1, 1 / 247) - 1

        df_result = df_result.join(df_bonds.copy(), how='inner')

        for ticker in tickers_list:
            df_ticker = df_quotations[df_quotations['TRADE_CODE'] == ticker]
            df_ticker = df_ticker.loc[:, ['DATE', 'OPEN']]
            df_ticker.set_index('DATE', inplace=True)
            df_ticker.columns = [ticker]

            df_result = df_result.join(df_ticker, how='left')
        df_result = df_result.loc[from_date:, :]
        self._price_data = df_result
        print("####################################")
        print("Данные цен инструментов сформированы")
        print("####################################")

    @property
    def companies_list(self):
        return (self.listing['TRADE_CODE'])

    @property
    def price_data(self):
        return self._price_data

    @property
    def price_data_updated(self):
        self.update_prices()
        return self._price_data


    def build_listings(self, listings):

        filtered_listing = self.listing[self.listing['LIST_SECTION'].isin(listings)]['TRADE_CODE'].values

        print("###################################################")
        print("          Листинг с фильтром сформирован")
        print("###################################################")
        return filtered_listing

    def update_prices(self):
        last_date = self._price_data.index[-1]

        db = Sqlite("Bettas&alphas.db")
        df_quotations = db.quotations_table(last_date + datetime.timedelta(days=1))
        tickers_list = self.listing['TRADE_CODE']

        df_index = df_quotations[df_quotations['TRADE_CODE'] == 'IMOEX']
        df_index = df_index.loc[:, ['DATE', 'OPEN']]
        df_index.columns = ['DATE', 'IMOEX']
        df_index.set_index('DATE', inplace=True)
        df_index.sort_index(ascending=True, inplace=True)
        df_result = df_index.copy()

        df_bonds = df_quotations[df_quotations['TRADE_CODE'] == '3-BONDS']
        df_bonds = df_bonds.loc[:, ['DATE', 'OPEN']]
        df_bonds.columns = ['DATE', 'Bonds']
        df_bonds.set_index('DATE', inplace=True)
        df_bonds = pow(df_bonds / 100 + 1, 1 / 247) - 1

        df_result = df_result.join(df_bonds.copy(), how='inner')

        for ticker in tickers_list:
            df_ticker = df_quotations[df_quotations['TRADE_CODE'] == ticker]
            df_ticker = df_ticker.loc[:, ['DATE', 'OPEN']]
            df_ticker.set_index('DATE', inplace=True)
            df_ticker.columns = [ticker]

            df_result = df_result.join(df_ticker, how='left')
        self._price_data.append(df_result)
        #print(self._price_data.tail())
        print("####################################")
        print("Данные цен инструментов обновлены")
        print("####################################")