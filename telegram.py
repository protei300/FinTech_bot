from telebot import TeleBot, types
from telegram_lib import *
from telebot_cfg import TOKEN
from telebot_msg import *
from sqlite_driver import Sqlite_telebot
from benchmark import Benchmark, FIGURE_BASE_DIR
import logging
import os
import glob
import datetime
import pandas as pd
import numpy as np
from telegram_controller import Telegram_controller



bot_controller = Telegram_controller()
#strategy_maker = Bettas_list(price_frame)
#portfolio_maker = Portfolio_maker(price_frame)
portfolios = {}
history = {}
users = {}
paid_user = None

logging.basicConfig(
                           filename=os.path.join('.','logs', 'logging.log'),
                           level=logging.INFO,
                           format=' %(asctime)s - %(levelname)s - %(message)s',
)

bot = TeleBot(TOKEN)

getme = bot.get_me()

@bot.message_handler(commands=['start'])
def start_send_welcome(message):
    cid = int(message.chat.id)
    db = Sqlite_telebot(TELEGRAM_DB)
    if db.is_user(cid):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_portfolio = types.KeyboardButton(text=Btn_names.PORTFOLIO_BUTTON)
        btn_history = types.KeyboardButton(text=Btn_names.HISTORY_BUTTON)
        btn_favorite = types.KeyboardButton(text=Btn_names.FAVORITE_BUTTON)
        btn_requests = types.KeyboardButton(text=Btn_names.REQUEST_BUTTON)
        markup.add(btn_portfolio, btn_history)
        #markup.add(btn_favorite, btn_requests)
        if db.is_admin(cid):
            btn_admin = types.KeyboardButton(text=Btn_names.ADMIN_BUTTON)
            markup.add(btn_admin)
        bot.send_message(cid, Typical_messages.GREET_REG_MESSAGE, reply_markup=markup)
    else:
        bot.send_message(cid, Typical_messages.GREET_UNREG_MESSAGE)
        bot.send_message(cid, Typical_messages.REGISTER_MESSAGE_FIO)
        bot.register_next_step_handler(message, start_register_fio)

def start_register_fio(message):
    cid = message.chat.id
    fio = message.text
    if all(x.isalpha() or x.isspace() for x in fio):
        user = User()
        user.chat_id = cid
        user.name = fio
        params = user.get_params()
        db = Sqlite_telebot(TELEGRAM_DB)
        if db.add_user(params):
            bot.send_message(cid, Typical_messages.REGISTER_MESSAGE_SUCCESS)
            if db.is_user(cid):
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                btn_portfolio = types.KeyboardButton(text=Btn_names.PORTFOLIO_BUTTON)
                btn_history = types.KeyboardButton(text=Btn_names.HISTORY_BUTTON)
                btn_favorite = types.KeyboardButton(text=Btn_names.FAVORITE_BUTTON)
                btn_requests = types.KeyboardButton(text=Btn_names.REQUEST_BUTTON)
                markup.add(btn_portfolio, btn_history)
                markup.add(btn_favorite, btn_requests)
                if db.is_admin(cid):
                    btn_admin = types.KeyboardButton(text=Btn_names.ADMIN_BUTTON)
                    markup.add(btn_admin)
                bot.send_message(cid, Typical_messages.GET_PAID, reply_markup=markup)

        else:
            bot.send_message(cid, Typical_messages.ADMIN_SET_UNSUCCESS)


    else:
        bot.send_message(message, Typical_messages.ERROR_MESSAGE + '\n' + Typical_messages.REGISTER_MESSAGE_FIO)
        bot.register_next_step_handler(message, start_register_fio)


##############################################################################################
###                             Админка                                                   ####
##############################################################################################

def create_admin_btns():
    btn_show_users = types.InlineKeyboardButton(text=Btn_names.ADMIN_SHOW_USERS,
                                                callback_data=Btn_names.ADMIN_SHOW_USERS)
    btn_add_user = types.InlineKeyboardButton(text=Btn_names.ADMIN_ADD_USER,
                                              callback_data=Btn_names.ADMIN_ADD_USER)
    btn_remove_user = types.InlineKeyboardButton(text=Btn_names.ADMIN_REMOVE_USER,
                                                 callback_data=Btn_names.ADMIN_REMOVE_USER)
    btn_set_paid_user = types.InlineKeyboardButton(text=Btn_names.ADMIN_SET_PAID_USER,
                                                   callback_data=Btn_names.ADMIN_SET_PAID_USER)

    markup = types.InlineKeyboardMarkup()
    markup.add(btn_show_users)
    markup.add(btn_set_paid_user)
    markup.add(btn_add_user)
    markup.add(btn_remove_user)
    return markup



#Создаем админские инлайн кнопки####
@bot.message_handler(func= lambda message: Sqlite_telebot(TELEGRAM_DB).is_admin(message.chat.id),
                     regexp = Btn_names.ADMIN_BUTTON)
def admin_menu(message):

    cid = message.chat.id
    bot.send_message(cid, Typical_messages.ADMIN_MENU, reply_markup=create_admin_btns())

##### Показать всех пользователей в базе данных ##################
@bot.callback_query_handler(func=lambda call: Btn_names.ADMIN_SHOW_USERS in call.data and
                                              Sqlite_telebot(TELEGRAM_DB).is_admin(call.message.chat.id),)
def admin_show_users(call):
    cid = call.message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.ADMIN_SHOW_USERS} юзером с id: {cid}')
    db = Sqlite_telebot(TELEGRAM_DB)
    all_users = db.get_users()

    bot.send_message(cid, all_users.to_markdown(tablefmt="pipe"))
    bot.send_message(cid, Typical_messages.ADMIN_MENU, reply_markup=create_admin_btns())


#### Добавить пользователя в базу данных ##########
@bot.callback_query_handler(func=lambda call: Btn_names.ADMIN_ADD_USER in call.data and
                                              Sqlite_telebot(TELEGRAM_DB).is_admin(call.message.chat.id),)
def admin_add_user_begin(call):
    cid = call.message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.ADMIN_ADD_USER} юзером с id: {cid}')
    users[cid] = User()
    bot.send_message(cid, Typical_messages.ADMIN_SET_NAME)
    bot.register_next_step_handler(call.message, admin_add_user_name)

def admin_add_user_name(message):
    cid = message.chat.id
    users[cid].name = message.text
    bot.send_message(cid, Typical_messages.ADMIN_SET_CHAT_ID)
    bot.register_next_step_handler(message, admin_add_chat_id)

def admin_add_chat_id(message):
    cid = message.chat.id
    if message.text.isdigit():
        users[cid].chat_id = message.text
        params = users[cid].get_params()
        db = Sqlite_telebot(TELEGRAM_DB)
        if db.add_user(params):
            bot.send_message(cid, Typical_messages.ADMIN_SET_SUCCESS)
        else:
            bot.send_message(cid, Typical_messages.ADMIN_SET_UNSUCCESS)
    else:
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE)
        bot.send_message(cid, Typical_messages.ADMIN_SET_CHAT_ID)
        bot.register_next_step_handler(message, admin_add_chat_id)

##### Удалить пользователя из базы ##############
@bot.callback_query_handler(func=lambda call: Btn_names.ADMIN_REMOVE_USER in call.data and
                                              Sqlite_telebot(TELEGRAM_DB).is_admin(call.message.chat.id),)
def admin_remove_user_begin(call):
    cid = call.message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.ADMIN_REMOVE_USER} юзером с id: {cid}')


##### Установить оплату пользователю #############
@bot.callback_query_handler(func=lambda call: Btn_names.ADMIN_SET_PAID_USER in call.data and
                                              Sqlite_telebot(TELEGRAM_DB).is_admin(call.message.chat.id),)
def admin_set_paid_user_begin(call):
    cid = call.message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.ADMIN_SET_PAID_USER} юзером с id: {cid}')
    db = Sqlite_telebot(TELEGRAM_DB)
    all_users = db.get_users()
    all_users = all_users.loc[:,~all_users.columns.isin(['adminsitrator'])]

    bot.send_message(cid, all_users.to_markdown(tablefmt="pipe"))
    bot.send_message(cid, Typical_messages.ADMIN_PAID_MESSAGE)
    bot.register_next_step_handler(call.message, admin_set_paid_till)

def admin_set_paid_till(message):
    global paid_user
    cid = message.chat.id
    user_id = message.text
    if user_id.isdigit():
        paid_user = Paid_User()
        paid_user.index = int(user_id)
        bot.send_message(cid, Typical_messages.ADMIN_PAID_DATE)
        bot.register_next_step_handler(message, admin_set_paid_id)
    elif message.text == '#':
        bot.clear_step_handler_by_chat_id(chat_id=cid)
        bot.send_message(cid, Typical_messages.BREAK_MESSAGE)
    else:
        bot.send_message(cid, Typical_messages.ADMIN_PAID_MESSAGE)
        bot.register_next_step_handler(message,admin_set_paid_till)


def admin_set_paid_id(message):
    global paid_user
    cid = message.chat.id
    try:
        paid_user.payment_date = pd.to_datetime(message.text).date()
        db = Sqlite_telebot(TELEGRAM_DB)
        db.update_paid_clients(paid_user)
        bot.send_message(cid, Typical_messages.ADMIN_MENU, reply_markup=create_admin_btns())
    except Exception as e:
        print(f"ERROR {e}")
        bot.send_message(cid, Typical_messages.ADMIN_PAID_DATE)
        bot.register_next_step_handler(message, admin_set_paid_id)


###############################################################################################
#                           Команда расчета портфеля для инвестиций                           #
###############################################################################################
def create_portfolio_btns():
    btn_make_portfolio = types.InlineKeyboardButton(text=Btn_names.PORTFOLIO_CALCULATE,
                                                callback_data=Btn_names.PORTFOLIO_CALCULATE)
    btn_show_followed_portfolio = types.InlineKeyboardButton(text=Btn_names.PORTFOLIO_FOLLOWED,
                                              callback_data=Btn_names.PORTFOLIO_FOLLOWED)

    markup = types.InlineKeyboardMarkup()
    markup.add(btn_make_portfolio)
    markup.add(btn_show_followed_portfolio)

    return markup

def create_portfolio_select_btns(start=0, end=10):
    markup = types.InlineKeyboardMarkup()


    for row in range(int(np.ceil((end)/3))):
        if row*3+3 <=end:
            btns = [types.InlineKeyboardButton(text=i+1,
                                               callback_data=Btn_names.PORTFOLIO_FOLLOWED + f'_{i}')
                    for i in range(row*3,row*3+3)]
        else:
            btns = [types.InlineKeyboardButton(text=i + 1,
                                               callback_data=Btn_names.PORTFOLIO_FOLLOWED + f'_{i}')
                    for i in range(row * 3, end)]
        markup.add(*btns)
    btn_left = types.InlineKeyboardButton(text='<<', callback_data=Btn_names.PORTFOLIO_FOLLOWED + '_<<')
    btn_right = types.InlineKeyboardButton(text='>>', callback_data=Btn_names.PORTFOLIO_FOLLOWED + '_>>')
    markup.add(btn_left,btn_right)
    return markup


@bot.message_handler(func= lambda message: Sqlite_telebot(TELEGRAM_DB).is_user(message.chat.id),
                     regexp=Btn_names.PORTFOLIO_BUTTON)
def portfolio_menu(message):
    cid = message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.PORTFOLIO_BUTTON} юзером с id: {cid}')
    markup = create_portfolio_btns()
    bot.send_message(cid, Typical_messages.PORTFOLIO_MAIN_MESSAGE, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: Btn_names.PORTFOLIO_FOLLOWED in call.data and
                                              Sqlite_telebot(TELEGRAM_DB).is_paid_user(call.message.chat.id),)
def portfolio_followed(call):
    cid = call.message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.PORTFOLIO_FOLLOWED} юзером с id: {cid}')
    db = Sqlite_telebot(TELEGRAM_DB)
    return_values = db.read_portfolio(cid)
    if  '_' not in call.data :
        markup = create_portfolio_select_btns(end=return_values['total_count'])
        bot.send_message(cid, return_values['result_text'], reply_markup=markup)
    else:
        button_id = call.data.split('_')[1]
        markup = create_portfolio_select_btns(end=return_values['total_count'])
        if button_id.isdigit():
            portfolio = return_values['portfolios'][int(button_id)]
            portfolio_struct = bot_controller.make_followed_portfolio(portfolio, cid)
            if portfolio_struct != 0:
                text = "Получены следующие результаты по вашему портфелю"
                text += 2*"\n" + portfolio_struct
                bot.send_message(cid,text)
                with open(os.path.join(TMP_DIR,f'portfolio_{cid}.png'),'rb') as pic:
                    bot.send_photo(cid, pic, reply_markup=markup)
            else:
                text = "Не хватает данных для отображения"
                bot.send_message(cid, text, reply_markup=markup)
        else:
            text = 'Нажата какая то кнопка'
            bot.send_message(cid, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: Btn_names.PORTFOLIO_CALCULATE in call.data and
                                              Sqlite_telebot(TELEGRAM_DB).is_paid_user(call.message.chat.id),)
#@bot.message_handler(commands=['make_portfolio'])
def portfolio_begin(call):
    cid = call.message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.PORTFOLIO_CALCULATE} юзером с id: {cid}')
    if Sqlite_telebot(TELEGRAM_DB).is_paid_user(cid):
        bot.send_message(cid, Typical_messages.DEPO_SIZE)
        portfolios[cid] = Portfolio_data()
        bot.register_next_step_handler(call.message, portfolio_money)
    else:
        bot.send_message(cid, Typical_messages.GET_PAID)



def portfolio_money(message):
    cid = message.chat.id
    if message.text.isdigit():
        portfolios[cid].money = int(message.text)
        bot.send_message(cid, Typical_messages.WEEKS_FOR_BETTA)
        bot.register_next_step_handler(message, portfolio_weeks_for_betta)
    elif message.text == '#':
        bot.clear_step_handler_by_chat_id(chat_id=cid)
        bot.send_message(cid, Typical_messages.BREAK_MESSAGE)
    else:
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE + 2*'\n' + Typical_messages.DEPO_SIZE)
        bot.register_next_step_handler(message, portfolio_money)

def portfolio_weeks_for_betta(message):
    cid = message.chat.id
    if check_digit_range(message.text, (5,50)):
        portfolios[cid].weeks_for_betta = int(message.text)
        markup = types.InlineKeyboardMarkup()
        btns = [types.InlineKeyboardButton (text=i, callback_data=f'portfolio_f_{i}') for i in range(2)]
        markup.add(*btns)
        bot.send_message(cid, Typical_messages.FILTER_TYPE, reply_markup=markup)
    elif message.text == '#':
        bot.clear_step_handler_by_chat_id(chat_id=cid)
        bot.send_message(cid, Typical_messages.BREAK_MESSAGE)
    else:
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE + 2*'\n' + Typical_messages.WEEKS_FOR_BETTA)
        bot.register_next_step_handler(message, portfolio_weeks_for_betta)


@bot.callback_query_handler(func=lambda call: 'portfolio_f_' in call.data)
def portfolio_filter_type(call):
    cid = call.message.chat.id
    try:
        portfolios[cid].filter_type = int(call.data.split('_')[-1])
        bot.send_message(cid, Typical_messages.WEEKS_FOR_FILTER)
        bot.register_next_step_handler(call.message, portfolio_weeks_for_filter)

    except:
        markup = types.InlineKeyboardMarkup()
        btns = [types.InlineKeyboardButton(text=i, callback_data=f'portfolio_f_{i}') for i in range(2)]
        markup.add(*btns)
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE + 2*'\n' + Typical_messages.FILTER_TYPE, reply_markup=markup)

def portfolio_weeks_for_filter(message):
    cid = message.chat.id
    if check_digit_range(message.text, (5,50)):
        portfolios[cid].weeks_for_filter = int(message.text)
        bot.send_message(cid, Typical_messages.WEEKS_TO_HOLD)
        bot.register_next_step_handler(message, portfolio_inform)
    elif message.text == '#':
        bot.clear_step_handler_by_chat_id(chat_id=cid)
        bot.send_message(cid, Typical_messages.BREAK_MESSAGE)
    else:
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE + 2 * '\n' + Typical_messages.WEEKS_FOR_FILTER)
        bot.register_next_step_handler(message, portfolio_weeks_for_filter)

def portfolio_inform(message):
    cid = message.chat.id
    if message.text.isdigit():
        portfolios[cid].weeks_to_hold = int(message.text)
        markup = types.InlineKeyboardMarkup()
        btns = [types.InlineKeyboardButton(text=i, callback_data=f'portfolio_inf_{i}') for i in ['Да','Нет']]
        markup.add(*btns)
        bot.send_message(cid, Typical_messages.PORTFOLIO_INFORM, reply_markup=markup)
        #bot.register_next_step_handler(message, portfolio_end)
    elif message.text == '#':
        bot.clear_step_handler_by_chat_id(chat_id=cid)
        bot.send_message(cid, Typical_messages.BREAK_MESSAGE)
    else:
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE + 2 * '\n' + Typical_messages.PORTFOLIO_INFORM)
        bot.register_next_step_handler(message, portfolio_inform)

@bot.callback_query_handler(func=lambda call: 'portfolio_inf_' in call.data)
def portfolio_end(call):
    cid = call.message.chat.id
    if call.data.split('_')[-1] == 'Да':
        portfolios[cid].inform = 1
    bot.send_message(cid, Typical_messages.PORTFOLIO_MAKING)
    portfolio_text = bot_controller.make_portfolio(portfolios[cid])
    bot.send_message(cid, portfolio_text)
    db = Sqlite_telebot(TELEGRAM_DB)
    params = {
        "calculus_date": datetime.datetime.now().strftime(format='%Y-%m-%d %H:%M:%S'),
        "chat_id": cid,
        "strategy": 0,
        "strategy_period": portfolios[cid].weeks_for_betta,
        "filter": portfolios[cid].filter_type,
        "filter_period": portfolios[cid].weeks_for_filter,
        "duration": portfolios[cid].weeks_to_hold,
        "inform": portfolios[cid].inform,
        "money" : portfolios[cid].money,
    }
    db.insert_portfolio(params)



###############################################################################################
#                           Меню расчета исторических результатов                          #
###############################################################################################


def create_history_btns():
    btn_history = types.InlineKeyboardButton(text=Btn_names.HISTORY_CALC_BUTTON, callback_data=Btn_names.HISTORY_CALC_BUTTON)
    btn_results = types.InlineKeyboardButton(text=Btn_names.HISTORY_SHOW_BUTTON, callback_data=Btn_names.HISTORY_SHOW_BUTTON)
    btn_requests = types.InlineKeyboardButton(text=Btn_names.HISTORY_SHOW_REQUESTS, callback_data=Btn_names.HISTORY_SHOW_REQUESTS)
    btn_clear = types.InlineKeyboardButton(text=Btn_names.HISTORY_CLEAR_BUTTON, callback_data=Btn_names.HISTORY_CLEAR_BUTTON)
    markup = types.InlineKeyboardMarkup()
    markup.add(btn_history, btn_results)
    markup.add(btn_requests, btn_clear)
    return markup



@bot.message_handler(func= lambda message: Sqlite_telebot(TELEGRAM_DB).is_user(message.chat.id),
                     regexp=Btn_names.HISTORY_BUTTON)
def history_menu(message):
    cid = message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.HISTORY_BUTTON} юзером с id: {cid}')
    if Sqlite_telebot(TELEGRAM_DB).is_paid_user(cid):
        markup = create_history_btns()
        bot.send_message(cid,text=Typical_messages.HISTORY_MENU, reply_markup=markup)
    else:
        bot.send_message(cid,Typical_messages.GET_PAID)


@bot.callback_query_handler(func=lambda call: Btn_names.HISTORY_SHOW_REQUESTS in call.data and
                                              Sqlite_telebot(TELEGRAM_DB).is_user(call.message.chat.id),)
def history_requests(call):
    cid = call.message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.HISTORY_SHOW_REQUESTS} юзером с id: {cid}')
    if Sqlite_telebot(TELEGRAM_DB).is_paid_user(cid):
        result = "Последние 10 запросов в истории" + 2*"\n"
        result += Sqlite_telebot(TELEGRAM_DB).read_history(cid)
        bot.send_message(cid, text=result, reply_markup=create_history_btns())
    else:
        bot.send_message(cid,Typical_messages.GET_PAID)



@bot.callback_query_handler(func=lambda call: Btn_names.HISTORY_CLEAR_BUTTON in call.data and
                                              Sqlite_telebot(TELEGRAM_DB).is_user(call.message.chat.id),)
def history_clear(call):
    cid = call.message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.HISTORY_CLEAR_BUTTON} юзером с id: {cid}')
    if Sqlite_telebot(TELEGRAM_DB).is_paid_user(cid):
        for f in [f'{cid}.pkl', f'{cid}.png', f'{cid}_scatter.pkl', f'{cid}_scatter.png']:
            if os.path.exists(os.path.join('.', FIGURE_BASE_DIR, f)):
                os.remove(os.path.join('.', FIGURE_BASE_DIR, f))

        bot.send_message(cid, text='Данные графиков очищены')
    else:
        bot.send_message(cid,Typical_messages.GET_PAID)

@bot.callback_query_handler(func=lambda call: Btn_names.HISTORY_SHOW_BUTTON in call.data and
                                              Sqlite_telebot(TELEGRAM_DB).is_user(call.message.chat.id),)
def history_results(call):
    cid = call.message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.HISTORY_SHOW_BUTTON} юзером с id: {cid}')
    if Sqlite_telebot(TELEGRAM_DB).is_paid_user(cid):
        files = glob.glob(os.path.join('.','tmp',f'{cid}*.png'))
        print(files)
        if len(files) == 2:
            with open(files[0],'rb') as pic:
                bot.send_photo(cid, pic)
            with open(files[-1], 'rb') as pic:
                bot.send_photo(cid, pic, reply_markup=create_history_btns())
        else:
            bot.send_message(cid, text=Typical_messages.HISTORY_MENU, reply_markup=create_history_btns())
    else:
        bot.send_message(cid, Typical_messages.GET_PAID)




@bot.callback_query_handler(func=lambda call: Btn_names.HISTORY_CALC_BUTTON in call.data and
                                              Sqlite_telebot(TELEGRAM_DB).is_user(call.message.chat.id),)
def history_calculate(call):
    cid = call.message.chat.id
    logging.info(f'Нажата кнопка {Btn_names.HISTORY_CALC_BUTTON} юзером с id: {cid}')
    if Sqlite_telebot(TELEGRAM_DB).is_paid_user(cid):
        bot.send_message(cid, Typical_messages.WEEKS_FOR_BETTA)
        history[cid] = History_data()
        bot.register_next_step_handler(call.message, history_weeks_to_count)
    else:
        bot.send_message(cid, Typical_messages.GET_PAID)

def history_weeks_to_count(message):
    cid = message.chat.id
    if check_digit_range(message.text, (5,50)):
        history[cid].weeks_for_betta = int(message.text)
        markup = types.InlineKeyboardMarkup()
        btns = [types.InlineKeyboardButton (text=i, callback_data=f'history_f_{i}') for i in range(2)]
        markup.add(*btns)
        bot.send_message(cid, Typical_messages.FILTER_TYPE, reply_markup=markup)
    elif message.text == '#':
        bot.clear_step_handler_by_chat_id(chat_id=cid)
        bot.send_message(cid, Typical_messages.BREAK_MESSAGE)
    else:
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE + 2*'\n' + Typical_messages.WEEKS_FOR_BETTA)
        bot.register_next_step_handler(message, history_weeks_to_count)

@bot.callback_query_handler(func=lambda call: 'history_f_' in call.data)
def history_filter_type(call):
    cid = call.message.chat.id
    try:
        history[cid].filter_type = int(call.data.split('_')[-1])
        bot.send_message(cid, Typical_messages.WEEKS_FOR_FILTER)
        bot.register_next_step_handler(call.message, history_weeks_for_filter)

    except:
        markup = types.InlineKeyboardMarkup()
        btns = [types.InlineKeyboardButton(text=i, callback_data=f'history_f_{i}') for i in range(2)]
        markup.add(*btns)
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE + 2 * '\n' + Typical_messages.FILTER_TYPE,
                         reply_markup=markup)



def history_weeks_for_filter(message):
    cid = message.chat.id
    if check_digit_range(message.text, (5,50)):
        history[cid].weeks_for_filter = int(message.text)
        bot.send_message(cid, Typical_messages.WEEKS_TO_HOLD)
        bot.register_next_step_handler(message, history_weeks_to_hold)
    elif message.text == '#':
        bot.clear_step_handler_by_chat_id(chat_id=cid)
        bot.send_message(cid, Typical_messages.BREAK_MESSAGE)
    else:
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE + 2 * '\n' + Typical_messages.WEEKS_FOR_FILTER)
        bot.register_next_step_handler(message, history_weeks_for_filter)

def history_weeks_to_hold(message):
    cid = message.chat.id
    if message.text.isdigit():
        history[cid].weeks_to_hold = int(message.text)
        bot.send_message(cid, Typical_messages.FROM_DATE)
        bot.register_next_step_handler(message, history_from_date)
    elif message.text == '#':
        bot.clear_step_handler_by_chat_id(chat_id=cid)
        bot.send_message(cid, Typical_messages.BREAK_MESSAGE)
    else:
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE + 2 * '\n' + Typical_messages.WEEKS_TO_HOLD)
        bot.register_next_step_handler(message, history_weeks_to_hold)


def history_from_date(message):
    cid = message.chat.id
    if len(message.text.split('-'))==3:
        history[cid].from_date = message.text
        bot.send_message(cid, Typical_messages.HISTORY_MAKING)
        result, files = bot_controller.make_history(history[cid], cid)
        ###### Вставляем данные запроса в таблицу history #################



        bot.send_message(cid, result)
        for file_path in files:
            with open(file_path, 'rb') as img:
                bot.send_photo(cid, img)
        bot.send_message(cid, text=Typical_messages.HISTORY_MENU, reply_markup=create_history_btns())
        params = {
            "request_date": datetime.datetime.now().strftime(format='%Y-%m-%d %H:%M:%S'),
            "chat_id": cid,
            "strategy": history[cid].strategy_type,
            "strategy_period": history[cid].weeks_for_betta,
            "filter": history[cid].filter_type,
            "filter_period": history[cid].weeks_for_filter,
            "duration": history[cid].weeks_to_hold,
            "start_date": history[cid].from_date,
        }
        db = Sqlite_telebot(TELEGRAM_DB)
        db.insert_history(params)


    elif message.text == '#':
        bot.clear_step_handler_by_chat_id(chat_id=cid)
        bot.send_message(cid, Typical_messages.BREAK_MESSAGE)
    else:
        bot.send_message(cid, Typical_messages.ERROR_MESSAGE + 2 * '\n' + Typical_messages.FROM_DATE)
        bot.register_next_step_handler(message, history_from_date)

try:
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Error found - {e}")
