import pandas as pd
from sqlite_driver import Sqlite

class Filter:
    filter_name = 'Base_Filter'

    def __init__(self):
        print("################################")
        print(f"Filter {self.filter_name} loaded")
        print("################################")

    def set_filter_period(self, period):
        return pd.to_datetime("1970-01-01")

    def filter_columns(self, row):
        return row, row


class Alpha_filter(Filter):

    def __init__(self):
        self.filter_name = 'Alpha'
        super().__init__()

    def set_filter_period(self, period):
        db = Sqlite('Bettas&alphas.db')
        if db.check_table_exists('Alphas'):
            self.alphas_frame = db.get_alphas(period)
            return self.alphas_frame.index[0]

    def filter_columns(self, row):
        alphas = self.alphas_frame.loc[row.name, self.alphas_frame.columns.isin(row.index)]
        alpha_mean = alphas.mean()
        alphas_a_z = alphas[alphas > alpha_mean]
        alphas_b_z = alphas[alphas <= alpha_mean]

        # Определяем значение Бэтта относительно которого идут расчеты
        row_filter_a_z = row[alphas_a_z.index]
        row_filter_b_z = row[alphas_b_z.index]

        return row_filter_a_z, row_filter_b_z