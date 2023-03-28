#/==================================================================\#
# user.py                                             (c) Mtvy, 2022 #
#\==================================================================/#
#                                                                    #
# Copyright (c) 2022. Mtvy (Matvei Prudnikov, m.d.prudnik@gmail.com) #
#                                                                    #
#\==================================================================/#

#/-----------------------------/ Libs \-----------------------------\#
from emj             import EMJ_RAISING_HAND
from path            import CTG_FILE, UORG_FILE
from utility         import set_keyboard, c_logging
from handling        import user_handle, init_proc, get_orgs     
from database        import get_db

from typing          import List, Literal
from telebot.types   import ReplyKeyboardRemove as rmvKey
from telebot         import TeleBot
from multiprocessing import Process
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
@c_logging
def init_user(bot : TeleBot, _id : int) -> None:

    txt = ('Вы вошли в аккаунт пользователя. '
           'Идёт получение документов. '
           'Подождите окончания загрузки.')
    bot.send_message(_id, txt, reply_markup=rmvKey())

    bot.send_document(_id, open(CTG_FILE, 'rb'), caption='Категории')

    _ids = [int(i[1]) for i in get_db('ids_tb')]

    get_orgs(bot, _id, UORG_FILE, _ids, 'Организации')
    
    key = set_keyboard([f'{EMJ_RAISING_HAND} Начать'])
    bot.send_message(_id, 'Документы получены.', reply_markup=key)
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
@c_logging
def proc_user(_id  : int, _ids : List[int]) -> Process | Literal[False]:
    return init_proc(user_handle, (_id, _ids))
#\------------------------------------------------------------------/#
