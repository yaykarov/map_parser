#/==================================================================\#
# handling.py                                         (c) Mtvy, 2022 #
#\==================================================================/#
#                                                                    #
# Copyright (c) 2022. Mtvy (Matvei Prudnikov, m.d.prudnik@gmail.com) #
#                                                                    #
#\==================================================================/#

#/-----------------------------/ Libs \-----------------------------\#
from utility         import c_logging, \
                            saveLogs , \
                            rmvFile  , \
                            saveText , \
                            set_keyboard
from database        import get_db, insert_db
from path            import IDS_FILE
from variables       import *
from emj             import *
from traceback       import format_exc
from time            import sleep
from telebot         import TeleBot
from typing          import Callable, Tuple, List, Dict, Any
from multiprocessing import Process
from schedule        import every       as set_delay
from schedule        import run_pending as proc_run
from requests        import get         as get_req
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
def get_orgs(bot  : TeleBot, 
             _id  : int, 
             file : str, 
             _ids : List[int], 
             cap  : str) -> None:

    saveText(f'Добавлено: {len(_ids)}\n', file)
    orgs = get_db('orgs_tb')

    for org in orgs:
        if int(org[1]) in _ids:
            txt = (f'#{org[0]} id: {org[1]}\n'
                   f'name: {org[2]}\n'
                   f'dscr: {org[3]}\n'
                   f'catg: {org[4]}\n'
                   f'addr: {org[5]}\n'
                   f'phne: {org[6]}\n'
                   f'hrs : {org[7]}\n'
                   f'avlb: {org[8]}\n\n')
            saveText(txt, file)

    bot.send_document(_id, open(file, 'rb'), caption=cap)

    rmvFile(file)
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
@c_logging
def init_proc(_func : Callable, _args) -> Process:
    return Process(target=_func, args=_args)


@c_logging
def start_proc(proc : Process) -> Process:
    proc.start()
    return proc

@c_logging
def kill_proc(proc : Process) -> Process:
    proc.kill()
    return proc
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
@c_logging
def start_handler(bot  : TeleBot, 
                  proc : Process, 
                  _id  : int, txt='Запрос мониторинга.') -> Process:

    keyboard = set_keyboard([f'{EMJ_CROSS} Остановить'])
    bot.send_message(_id, txt, reply_markup=keyboard)

    return start_proc(proc)


@c_logging
def kill_handler(bot  : TeleBot,
                 proc : Process, 
                 _id  : int, txt='Мониторинг отключен.') -> None:
    
    kill_proc(proc)
    key = set_keyboard([f'{EMJ_RAISING_HAND} Начать'])
    bot.send_message(_id, txt, reply_markup=key)
    del proc

    return None
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
_st = {'added' : False, 'error' : False, 'over' : False}
def admin_handle(_id  : int) -> None:
    global _st


    def _send_req(bot : TeleBot, 
                 _id  : int, 
                 ctg  : List[str], 
                 _ids : List[int]) -> None:
        
        global _st


        def __turn_tuple(_item : Dict) -> Tuple:

            buffer = _item['properties']['CompanyMetaData']

            _name        = _item['properties'][   'name'    ].replace("'", "''")
            _description = _item['properties']['description'].replace("'", "''")

            _id          = int(buffer['id'])

            _address     = buffer['address'   ].replace("'", "''")
            _categories  = []
            _phones      = ['']
            
            for cat in buffer['Categories']:
                _categories.append(cat['name'])

            _available = _hours = None
            

            if 'Hours' in buffer.keys():
                if 'text' in buffer['Hours'].keys():
                    _hours = buffer['Hours']['text']
                
            if 'Phones' in buffer.keys():
                for phone in buffer['Phones']:
                    _phones.append(phone['formatted'])

            del buffer

            return [0, _id      , _name      ,
                    _description, _categories,
                    _address    , _phones    , 
                    _hours      , _available ]

        def __add_items(_its      : List[Any], 
                        _ids      : List[int], 
                        added_ids : List[int]) -> tuple:

            for _it in _its:
                _item = __turn_tuple(_it)
                if _item[1] not in _ids:
                    insert_db(
                        f'    {INSERT_ORGS_TB}    '
                        f'     \'{_item[1]}\'   , '
                        f'     \'{_item[2]}\'   , '
                        f'     \'{_item[3]}\'   , '
                        f' ARRAY {_item[4]}     , '
                        f'     \'{_item[5]}\'   , '
                        f' ARRAY {_item[6]}     , '
                        f'     \'{_item[7]}\'   , '
                        f'     \'{_item[8]}\'     '
                        ');                       '
                        f'{COUNT_DB} orgs_tb     ;'
                    )
                    insert_db(
                        f'{INSERT_IDS_TB} \'{_item[1]}\'); '
                        f'{COUNT_DB} orgs_tb     ;         '
                    )
                    _ids     .append(int(_item[1]))
                    added_ids.append(int(_item[1]))

            return (_ids, added_ids)

        def __req(txt : str, res : int, skip : int, key : str) -> Dict:
            try:
                req : Dict = get_req(
                    f'{SEARCH_URL}?text={txt}&type=biz&lang=ru_RU'
                    f'&results={res}&skip={skip}&apikey={key}'
                ).json()
            except:
                return False

            return 'over' if 'features' not in req.keys() else req['features']

        def __proc_req(category  : str, 
                       api_key   : str, 
                       _ids      : List[int],
                       added_ids : List[int],
                       _st       : Dict[str, bool],
                       passes    : Tuple[int] = (0, 500, 1000), 
                       result    : int = RESULT_LIM):

            for skip in passes:
                data = __req(category, result, skip, api_key)

                if data:
                    _ids, added_ids = __add_items(data, _ids, added_ids)

                    if len(data) < 400:
                        break

                elif data == [] and skip == 0:
                    break 
                
                elif data == 'over':
                    _st['over'] = True
                    break
                
            if not _st['error'] and not _st['over']:
                _st['added'] = True

            return (_ids, added_ids, _st)
        

        try:
            apis_len = len(API_KEY_SET)
            
            cat_added = []

            added_ids : List[int] = []
        
            for api_key, indx in zip(API_KEY_SET, range(apis_len)):
                
                txt = f'Парсинг по {indx + 1} из {apis_len}...'
                bot.send_message(_id, txt)
                
                for ctg in MAINCAT_CONST:
                    if ctg not in cat_added:
                        _ids, added_ids, _st = __proc_req(
                            ctg, api_key, _ids, added_ids, _st)

                        if _st['added']:
                            cat_added.append(ctg)
                        if _st['over']:
                            break
                
                if len(cat_added) == len(MAINCAT_CONST):
                    get_orgs(bot, _id, IDS_FILE, added_ids, 'Добавлено')
                    break

        except:
            saveLogs(f"[_send_req]-->{format_exc()}")
            _st['error'] = True

    try:
        bot = TeleBot(TOKEN)

        ctg = MAINCAT_CONST

        _ids = [int(i[1]) for i in get_db('ids_tb')]

        set_delay(UPDATE_DELAY).hours.do(
            _send_req, bot, _id, ctg, _ids
        )

        bot.send_message(_id, 'Мониторинг инициализирован.')
        
        while not _st['error']:

            _st['added'] = False
            _st['over']  = False

            proc_run()
            sleep(1)

        if _st['error']:
            bot.send_message(_id, 'Ошибка мониторинга.')
        
    except:
        saveLogs(f"[run_pending]-->{format_exc()}")

    bot.send_message(_id, 'Выход из мониторинга.')


_u_st = {'error' : False}
u_ids = []
def user_handle(_id  : int, ids : List[int]) -> None:
    global _u_st, u_ids

    def _send_req(bot : TeleBot, _id  : int, ctg  : List[str]) -> None:
        global _u_st, u_ids

        try:
            orgs = get_db('orgs_tb')

            file = f'U{_id}.txt'
            
            saveText(f'Добавлено: {len(orgs) - len(u_ids)}\n', file)

            ind = 1

            for org in orgs:
                if int(org[1]) not in u_ids:
                    txt = (f'#{ind} id: {org[1]}\n'
                           f'name: {org[2]}\n'
                           f'dscr: {org[3]}\n'
                           f'catg: {org[4]}\n'
                           f'addr: {org[5]}\n'
                           f'phne: {org[6]}\n'
                           f'hrs : {org[7]}\n'
                           f'avlb: {org[8]}\n\n')
                    saveText(txt, file)
                    ind += 1
                    u_ids.append(int(org[1]))

            bot.send_document(_id, open(file, 'rb'), caption='Добавлено')

            rmvFile(file)
            

        except:
            saveLogs(f"[user_handle][_send_req]-->{format_exc()}")
            _u_st['error'] = True

    try:
        bot = TeleBot(TOKEN)

        ctg = MAINCAT_CONST

        u_ids = ids

        set_delay(30).minutes.do(
            _send_req, bot, _id, ctg
        )

        bot.send_message(_id, 'Мониторинг инициализирован.')
        
        while not _u_st['error']:
            proc_run()
            sleep(1)

        if _u_st['error']:
            bot.send_message(_id, 'Ошибка мониторинга.')
        
    except:
        saveLogs(f"[run_pending]-->{format_exc()}")

    bot.send_message(_id, 'Выход из мониторинга.')
#\------------------------------------------------------------------/#


#\==================================================================/#
if __name__ == "__main__":
    ...
#\==================================================================/#
