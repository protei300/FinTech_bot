


class Typical_messages:
    GREET_UNREG_MESSAGE = '''
    Добро пожаловать в Финтех бота. Данные бот предназначен для формирования инвестиционного портфеля по различным прибыльным стратегиям.
    '''
    REGISTER_MESSAGE_FIO = '''Давайте будем с вами знакомиться.\n'''
    REGISTER_MESSAGE_FIO += "Как вас зовут?"

    REGISTER_MESSAGE_SUCCESS = "Вы были успешно зарегистрированы.\n"
    GET_PAID = "Для того чтобы пользоваться полным фукнционалом, вам необходимо связаться с администратором @Protei300"


    GREET_REG_MESSAGE = '''
    Спасибо что вернулись! Больших профитов вам!
    '''

    DEPO_SIZE = "Каков размер вашего депозита?"
    WEEKS_FOR_FILTER = "Сколько недель исторических данных использовать для расчета фильтра? [5:50]"
    WEEKS_FOR_BETTA = "Сколько недель исторических данных использовать для расчета Бетта? [5:50]"

    PORTFOLIO_MAKING = "Формирую портфель. Пожалуйста подождите!"
    PORTFOLIO_INFORM = "Отслеживать ли созданный вами портфель?"
    PORTFOLIO_MAIN_MESSAGE = "Вы находитесь в меню работы с портфелями. Выберите действие:"

    FILTER_TYPE = '''
    Выберите вариант фильтра:
    0 - Без фильтра
    1 - Фильтрация по показателю Альфа
    '''
    FROM_DATE = "Укажите дату в формате год-месяц-день, с которой построить исторические данные"
    HISTORY_MAKING = "Формирую отчет по исторической доходности. Пожалуйста подождите!"
    WEEKS_TO_HOLD = "Укажите число недель, в течение которых ожидается удержание позиции"
    HISTORY_MENU = "Выберите действие:"

    ERROR_MESSAGE = "Вы ввели неверное значение. Попробуйте снова"
    BREAK_MESSAGE = "Вы прервали введение данных"

    ADMIN_MENU = "Добро пожаловать в меню администратора. Выберите действие:"
    ADMIN_SET_NAME = "Введите ФИО пользователя"
    ADMIN_SET_CHAT_ID = "Введите ID пользователя"
    ADMIN_SET_SUCCESS = "Пользователь добавлен успешно"
    ADMIN_SET_UNSUCCESS = "Пользователь не был добавлен. Возникла ошибка"
    ADMIN_PAID_MESSAGE = "Укажите ID пользователей, которые оплатили"
    ADMIN_PAID_DATE = "Укажите дату по которую оплачена подписка"

class Btn_names:

    PORTFOLIO_BUTTON = "Работа с портфелем"
    HISTORY_BUTTON = "Работа с историей"
    FAVORITE_BUTTON = "Избранное"
    REQUEST_BUTTON = "Запросы"
    ADMIN_BUTTON = "Администраторское"

    HISTORY_CALC_BUTTON = 'Оценить стратегию'
    HISTORY_SHOW_BUTTON = 'Показать графики'
    HISTORY_CLEAR_BUTTON = 'Очистить графики'
    HISTORY_SHOW_REQUESTS = 'Показать запросы'

    ADMIN_SHOW_USERS = 'Показать пользователей'
    ADMIN_ADD_USER = 'Добавить пользователя'
    ADMIN_REMOVE_USER = 'Удалить пользователя'
    ADMIN_SET_PAID_USER = 'Установить оплату'


    PORTFOLIO_FOLLOWED = "Отслеживаемые портфели"
    PORTFOLIO_CALCULATE = "Cформировать портфель"



    def get_btn_names(self):
        return [self.PORTFOLIO_BUTTON, self.HISTORY_BUTTON, self.FAVORITE_BUTTON, self.REQUEST_BUTTON, self.ADMIN_BUTTON]