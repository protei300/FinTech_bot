import os

TELEGRAM_DB = os.path.join('.','db','telegram.db')
TMP_DIR = os.path.join('.','tmp')
COLORS = ['b', 'g', 'r', 'c', 'm', 'y', 'k']



def check_digit_range(value,range_tup):
    '''
    Проверяем находится ли введенная переменная в заданном диапазоне, и вообще числовая ли она
    :param value:
    :param range_tup:
    :return:
    '''
    range_list = [i for i in range(range_tup[0],range_tup[1]+1)]
    if value.isdigit():
        if int(value) in range_list:
            return True
    return False

class Data_saver:
    def __init__(self):
        self.strategy_type = 0
        self.weeks_for_filter = None
        self.weeks_for_betta = None
        self.filter_type = None
        self.weeks_to_hold = None


class Portfolio_data(Data_saver):
    def __init__(self):
        super().__init__()
        self.money = None
        self.inform = 0


class History_data(Data_saver):
    def __init__(self):
        super().__init__()
        self.from_date = None


class User:
    def __init__(self):
        self.chat_id = None
        self.name = None
        self.admin = 0

    def get_params(self):
        params = {
            'chat_id': self.chat_id,
            'name': self.name,
            'admin': self.admin
        }
        return params

class Paid_User:
    def __init__(self):
        self.index = None
        self.payment_date = None