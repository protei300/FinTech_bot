import sqlite3
import pandas as pd
import os
import datetime
from sqlalchemy.types import INTEGER, Float, Text, DateTime, Boolean

FILTERS = {
    0: 'Без фильтра',
    1: 'Альфа фильтр',
}

STRATEGIES = {
    0: 'BAB',
}

class Sqlite_base:

    def __init__(self, filename):
        self.filename = filename
        self.conn = sqlite3.connect(filename)
        self.cur = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    def __enter__(self):
        return self.conn

    def __exit__(self, type, value, traceback):
        self.conn.close()

    def check_table_exists(self, tablename):
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f'{tablename}',))
        if self.cur.fetchone() == None:
            return False
        else:
            return True

class Sqlite(Sqlite_base):


    def get_alphas(self, num):
        return pd.read_sql(f"SELECT * from Alphas WHERE ALPHA='Alphas_{num}'",
                           con=self.conn,
                           index_col='DATE',
                           parse_dates=['DATE']).iloc[:, 2:]

    def get_bettas(self, num):
        return pd.read_sql(f"SELECT * from Bettas WHERE BETTA='Bettas_{num}'",
                    con=self.conn,
                    index_col='DATE',
                    parse_dates=['DATE']).iloc[:, 2:]


    def get_quotes_table_by_name(self, table_name):
        res = self.cur.execute(f"SELECT * FROM Quotations WHERE TRADE_CODE='{table_name}'")
        df = pd.DataFrame(columns=['index', 'TRADE_CODE', 'DATE', 'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOL'],
                          data=res.fetchall(),
                          )
        df = df[df.columns[1:]]
        df['DATE'] = pd.to_datetime(df['DATE'], format="%Y-%m-%d")
        return df


    def quotations_table(self, from_date='2009-01-01'):
        return pd.read_sql(f"SELECT * FROM Quotations WHERE datetime(DATE)>='{from_date}'",
                           con=self.conn,
                           index_col='index',
                           parse_dates=['DATE']
                           )

    @property
    def create_quotations_table(self):
        if self.check_table_exists('Quotations'):
            return pd.read_sql("SELECT * FROM Quotations",
                               con=self.conn,
                               index_col='index',
                               parse_dates=['DATE']
                               )
        else:
            return pd.DataFrame(columns=['TRADE_CODE', 'DATE', 'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOL'],
                                )


    def companies_df_filtered(self, section):
        return pd.read_sql(f'SELECT * FROM TICKERS WHERE LIST_SECTION="{section}"',
                           con = self.conn,
                           )

    @property
    def companies_df(self):
        return pd.read_sql("SELECT * FROM Tickers",
                           con=self.conn,
                           index_col='TRADE_CODE')

    @property
    def get_connection(self):
        return self.conn

    def remove_quotations_duplicates(self):
        df = pd.read_sql("SELECT * FROM Quotations",
                         con=self.conn,
                         index_col='index',
                         parse_dates=['DATE']
                         )
        before = df.shape[0]
        df.drop_duplicates(inplace=True)
        df.to_sql("Quotations", self.conn, if_exists='replace')
        print(f"Removed {before - df.shape[0]} rows")

    def delete_table(self, table_name):

        try:
            self.cur.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"Table {table_name} deleted")
            self.conn.commit()
        except Exception:
            print(f"Smth went wrong with table {table_name}!")



class Sqlite_telebot(Sqlite_base):

    def __init__(self,filename):
        super().__init__(filename)
        if not self.check_table_exists('telebot_clients'):
            self.cur.execute('''CREATE TABLE IF NOT EXISTS 'telebot_clients' (
            'index' INTEGER PRIMARY KEY, 
            'reg_date' TEXT NOT NULL,
            'chat_id' INTEGER NOT NULL,
            'Name' TEXT NOT NULL,
            'payment_date' TEXT,
            'administrator' NUMERIC
            ) '''
            )
            self.conn.commit()
            params = {
                'chat_id': 418198005,
                'Name': 'Виталий Мельников',
                'administrator': 1,

            }
            self.add_user(params=params)

        if not self.check_table_exists('history'):
            self.cur.execute('''CREATE TABLE IF NOT EXISTS 'history' (
                        'index' INTEGER PRIMARY KEY, 
                        'request_date' TEXT NOT NULL,
                        'chat_id' INTEGER NOT NULL,
                        'strategy' INTEGER NOT NULL,
                        'strategy_period' INTEGER NOT NULL,
                        'filter'          INTEGER NOT NULL,
                        'filter_period'   INTEGER NOT NULL,
                        'duration'        INTEGER default 5 NOT NULL,
                        'start_date'   TEXT NOT NULL) 
                        '''
                        )


################ Работа с таблицей клиентов #####################
    @property
    def is_empty(self):
        result = self.cur.execute("SELECT * FROM telebot_clients")
        if result.fetchone() == None:
            return True
        else:
            return False

    def is_user(self, id):
        if self.is_empty:
            params = {
                'chat_id': id,
                'Name' : 'Виталий Мельников',
                'paid' : 1,
                'administrator': 1,
                'payment_date': '2099-01-01'
            }

            self.add_user(params)

        result = self.cur.execute("SELECT chat_id FROM telebot_clients WHERE chat_id=?", (f'{id}',))
        if result.fetchone() == None:
            return False
        else:
            return True

    def is_paid_user(self, id):
        result = self.cur.execute("SELECT chat_id FROM telebot_clients WHERE chat_id=? AND payment_date>=datetime('now','localtime')", (f'{id}',))
        if result.fetchone() == None:
            return False
        else:
            return True


    def is_admin(self, id):
        result = self.cur.execute("SELECT administrator FROM telebot_clients WHERE chat_id=? AND administrator=1", (f'{id}',))
        if result.fetchone() == None:
            return False
        else:
            return True

    def add_user(self, params):
        if 'payament_date' not in params.keys():
            params['payment_date']='1970-01-01'
        try:
            self.cur.execute("INSERT INTO telebot_clients (chat_id,reg_date,Name,payment_date,administrator) VALUES (?,?,?,?,?)",
                             (params['chat_id'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              params['name'], params['payment_date'], params['admin']))
            self.conn.commit()
            return True
        except Exception as e:
            print('Smth went wrong with adding users into DB')
            print(e)
            return False

    def get_users(self):
        try:
            df_users = pd.read_sql("SELECT rowid, chat_id, Name, payment_date, administrator FROM telebot_clients",
                                   con=self.conn,
                                   index_col= 'rowid'
                                   )
            #df_users = df_users.loc[:,['chat_id', 'Name', 'payment_date']]
            df_users.index.name = '#'
            df_users['chat_id'] = df_users['chat_id'].astype('str')
            df_users['payment_date'] = pd.to_datetime(df_users['payment_date']).dt.date
            return df_users
        except Exception as e:
            print(f'Что-то пошло не так, ошибка {e}')

    def update_paid_clients(self, paid_client):
        try:
            self.cur.execute("UPDATE telebot_clients SET payment_date=? WHERE ROWID=?",
                             (paid_client.payment_date, paid_client.index))
            self.conn.commit()
        except Exception as e:
            print(f"Что-то с обновление значений таблицы пошло не так. Ошибка {e}")

    def show_users(self):
        try:
            result = self.cur.execute("SELECT rowid, chat_id, Name, payment_date, administrator FROM telebot_clients")
            self.conn.commit()
            result_string = "№ | ID чата | Имя | Срок действия | Админ\n"
            for line in result.fetchall():
                result_string += f"{line[0]}: {line[1]} | {line[2]} | {line[3]} | {line[4]}\n"
            return result_string
        except Exception as e:
            print(f'Что-то пошло не так, ошибка {e}')

############################# Функции работы с таблицей портфолио ###########################

    def insert_portfolio(self, params):
        '''
        Метод вносит данные создаваемых портфолио в таблицу
        :param params:
        chat_id: номер собеседника
        strategy: код стратегии
        strategy_period: период расчета для стратегии
        filter: код фильтра
        filter_period: период для расчета фильтра
        duration: длительность удержания позиции
                inform: Информировать ли пользователя
        :return:
        Возвращает код 0 если все было хорошо,
        -1 если не верно
        '''
        chat_id = params['chat_id']
        strategy = params['strategy']
        strategy_period = params['strategy_period']
        filter = params['filter']
        filter_period = params['filter_period']
        duration = params['duration']
        inform = params['inform']
        calculus_date = params['calculus_date']
        money = params['money']

        try:
            self.cur.execute("INSERT INTO portfolios (chat_id, strategy, strategy_period, "
                             "filter, filter_period, duration, inform, calculus_date, money)"
                             "VALUES (?,?,?,?,?,?,?,?,?)", (chat_id, strategy, strategy_period, filter, filter_period,
                                                          duration, inform, calculus_date, money))
            self.conn.commit()
            return 0
        except Exception as e:
            print(f"Ошибка вставки в таблицу portfolios - {e}")
            print(params)
            return -1

    def read_portfolio(self, cid):
        '''
        Метод читает портфолио за которыми следит пользователь с chat_id
        :param cid: номер телеграм пользователя
        :return:
        Возвращает либо список отслеживаемых портфелей,
        либо пустую строку
        '''
        result_string = ''

        result = self.cur.execute("SELECT ROWID,strategy,strategy_period,filter,filter_period,duration,calculus_date,"
                                  "money FROM portfolios WHERE chat_id=? AND inform=1", (cid,))

        total_count = 0
        portfolios = []
        for i, portfolio in enumerate(result.fetchall()):
            next_inform_date = datetime.datetime.strptime(portfolio[6], '%Y-%m-%d %H:%M:%S')
            next_inform_date -= datetime.timedelta(days=next_inform_date.weekday())
            next_inform_date += datetime.timedelta(weeks=portfolio[5])
            next_inform_date = next_inform_date.strftime(format='%Y-%m-%d')
            result_string += f'Портфель №{i+1}\n'
            result_string += f'Стратегия: {STRATEGIES[portfolio[1]]}, Период: {portfolio[2]}\n'
            result_string += f'Фильтр: {FILTERS[portfolio[3]]}, Период: {portfolio[4]}\n'
            result_string += f'Длительность: {portfolio[5]}\n'
            result_string += f'Дата создания: {portfolio[6]}\n'
            result_string += f'Денежные средства: {portfolio[7]}\n'
            result_string += f'След дата пересчета: {next_inform_date}\n\n'
            total_count+=1
            portfolios.append((portfolio[1], portfolio[2], portfolio[3], portfolio[4],
                               datetime.datetime.strptime(portfolio[6], "%Y-%m-%d %H:%M:%S"), portfolio[7]))
        return_values = {
            'total_count': total_count,
            'result_text': result_string,
            'portfolios' : portfolios
        }

        #print(result_string[:-2])
        return return_values

################# Функции для работы с таблицей истории ####################

    def read_history(self, cid):
        '''
        Метод считывает данные из таблицы истории по chat_id
        :param cid:  chat_id  в телеграмм
        :return:
        '''
        result_string = ''
        result = self.cur.execute("SELECT request_date, chat_id, strategy, strategy_period, filter, filter_period, duration, start_date "
                                  "FROM history WHERE chat_id=?", (cid,)).fetchall()
        user_name = self.cur.execute("SELECT Name FROM telebot_clients WHERE chat_id=?", (cid,)).fetchone()[0]

        for i, history_request in enumerate(result[-10:]):
            result_string += f'Исторический запрос №{i + 1}\n\n'
            result_string += f'Чат ID: {cid}\n'
            result_string += f'Имя: {user_name}\n'
            result_string += f'Дата запроса: {datetime.datetime.strptime(history_request[0], "%Y-%m-%d %H:%M:%S")}\n'
            result_string += f'Стратегия: {STRATEGIES[history_request[2]]}, Период: {history_request[3]}\n'
            result_string += f'Фильтр: {FILTERS[history_request[4]]}, Период: {history_request[5]}\n'
            result_string += f'Длительность: {history_request[6]}\n'
            result_string += f'Дата создания: {history_request[7]}\n\n'

        return result_string



    def insert_history(self, params):
        '''
        Метод вставляет строчку в таблицу запросов исторических данных
        :param params:
        :return:
        '''
        request_date = params['request_date']
        chat_id = params['chat_id']
        strategy = params['strategy']
        strategy_period = params['strategy_period']
        filter = params['filter']
        filter_period = params['filter_period']
        duration = params['duration']
        start_date = params['start_date']

        try:
            self.cur.execute("INSERT INTO history (request_date, chat_id, strategy, strategy_period, "
                             "filter, filter_period, duration, start_date)"
                             "VALUES (?,?,?,?,?,?,?,?)", (request_date, chat_id, strategy, strategy_period, filter, filter_period,
                                                            duration, start_date))
            self.conn.commit()
            return 0
        except Exception as e:
            print(f"Ошибка вставки в таблицу history - {e}")
            print(params)
            return -1



class Tickers(Sqlite):

    def update_tickers_lotsize(self):
        df_lotsize = pd.read_csv(os.path.join('.', 'uploads', 'rates.csv'),
                         sep = ';',
                         index_col = 'SECID'


                        )
        self.companies_df.join(df_lotsize, how='left').to_sql("Tickers",
                                                              con=self.conn,
                                                              if_exists='replace')


