#/==================================================================\#
# admin.py                                            (c) Yaykarov, 2022 #
#\==================================================================/#
#                                                                    #
# Copyright (c) 2022. Yaykarov (Timur Yaykarov, timmyya999@gmail.com) #
#                                                                    #
#\==================================================================/#

#/-----------------------------/ Libs \-----------------------------\#
from emj             import EMJ_RAISING_HAND
from path            import CTG_FILE, ORG_FILE
from utility         import set_keyboard, c_logging
from database        import get_db
from variables       import API_KEY_SET

from typing          import Literal
from telebot.types   import ReplyKeyboardRemove as rmvKey
from telebot         import TeleBot
from multiprocessing import Process
from handling        import get_orgs, admin_handle, init_proc     
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
def init_admin(bot : TeleBot, _id : int) -> None:
    txt = ('Вы вошли в аккаунт админа. '
           'Идёт получение документов. '
           'Подождите окончания загрузки.')

    bot.send_message(_id, txt, reply_markup=rmvKey())
        
    _api_keys = f'Используемые API ключи:'
    for _key, indx in zip(API_KEY_SET, range(len(API_KEY_SET))):
        _api_keys += f'\n{indx + 1}. {_key}'

    bot.send_message(_id, _api_keys)

    bot.send_document(_id, open(CTG_FILE, 'rb'), caption='Категории')
        
    _ids = [int(i[1]) for i in get_db('ids_tb')]
        
    get_orgs(bot, _id, ORG_FILE, _ids, 'Организации')
    
    key = set_keyboard([f'{EMJ_RAISING_HAND} Начать'])
    bot.send_message(_id, 'Документы получены.', reply_markup=key)
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
@c_logging
def proc_admin(_id  : int) -> Process | Literal[False]:
    return init_proc(admin_handle, [_id])
#\------------------------------------------------------------------/#
