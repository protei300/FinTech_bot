import pandas as pd
import numpy as np
from sqlite_driver import Sqlite
from datetime import timedelta, datetime
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import time

class Investing_downloader:

    SPECIAL_TICKERS = ['3-BONDS', '5-BONDS']
    TIMEOUT = 2
    COLUMNS = ['TRADE_CODE', 'DATE', 'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOL']

    def make_post_request(self, investing_id, start_date, end_date):

        params = {
            "curr_id" : f"{investing_id}",
            "smlID" : "1160000",
            "header": "test",
            "st_date": start_date,
            "end_date": end_date,
            "interval_sec": "Daily",
            "sort_col": "date",
            "sort_ord": "DESC",
            "action": "historical_data",
        }


        headers = {
            "Host": "ru.investing.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
            "Accept": "text/plain, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "https://ru.investing.com/equities/vtb_rts-historical-data",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Length": "156",
            "Connection": "close"
        }

        url = "https://ru.investing.com/instruments/HistoricalDataAjax"

        while True:
            try:
                result = requests.post(url=url, data=params, headers=headers)
            except requests.exceptions.SSLError:
                print("Trying again")
                time.sleep(self.TIMEOUT)
            except requests.exceptions.ConnectionError:
                print("Trying again")
                time.sleep(self.TIMEOUT)
            else:
                break
        if result.status_code == requests.codes.ok:
            return 0 ,result.text
        else:
            print(f"ERROR: {result}")
            return -1, result

    def parse_tickers_table(self, table_to_parse, ix):
        root = BeautifulSoup(table_to_parse, 'html.parser')
        table = root.find("table", {"class" :"historicalTbl"})

        output_rows = []
        for table_row in table.tbody.findAll('tr')[:]:
            columns = table_row.findAll('td')
            output_row = []
            output_row.append(ix)
            for i, column in enumerate(columns[:-1]):
                output_row.append(column.text)
                if i == 4 and ix in self.SPECIAL_TICKERS:
                    output_row.append('0')
            output_rows.append(output_row)

        try:
            output_df = pd.DataFrame(columns=self.COLUMNS,
                                     data=output_rows,
                                     )
        except Exception:
            return pd.DataFrame(columns=self.COLUMNS)

        for column in ['OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOL']:
            output_df[column] = output_df[column].str.replace('.' ,'').str.replace(',' ,'.')

        output_df = output_df.astype({'OPEN': float,
                                      'CLOSE': float,
                                      'HIGH': float,
                                      'LOW': float})
        output_df['DATE'] = pd.to_datetime(output_df['DATE'], format='%d.%m.%Y')
        return output_df


    def parse_history(self):
        db = Sqlite('Bettas&alphas.db')
        df_tickers = db.companies_df
        df_quotes = db.create_quotations_table
        print("###################################")
        print(f"Saving tickers history")
        print("###################################")

        pbar = tqdm(df_tickers.iterrows(), total=df_tickers.shape[0])

        for ix, row in pbar:
            pbar.set_description(f"Collecting: {ix}")

            if row['HREF'] is None:
                continue
            ticker_quotes = df_quotes[df_quotes['TRADE_CODE'] == ix]
            start_date = ticker_quotes['DATE'].max()
            end_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

            if start_date is np.nan or start_date is pd.NaT:
                start_date = "01/01/1970"
            else:
                start_date = (start_date + timedelta(days=1)).strftime("%d/%m/%Y")

            code, table_parse = self.make_post_request(row['INVESTING_ID'], start_date = start_date, end_date = end_date)

            if code == 0:
                output_df = self.parse_tickers_table(table_parse, ix)
                df_quotes = df_quotes.append(output_df,  ignore_index=True)



        df_quotes.to_sql("Quotations", db.get_connection, if_exists='replace')