#/==================================================================\#
# database.py                                         (c) Mtvy, 2022 #
#\==================================================================/#
#                                                                    #
# Copyright (c) 2022. Mtvy (Matvei Prudnikov, m.d.prudnik@gmail.com) #
#                                                                    #
#\==================================================================/#

#/-----------------------------/ Libs \-----------------------------\#
import json
import re
from psycopg2 import connect as connect_db

from typing       import Any, Dict, List, Literal, Tuple
from traceback    import format_exc
from json         import dump as dump_json
from json         import load as load_json
from sys          import argv as _dvars
from progress.bar import IncrementalBar

from utility   import c_logging, openfileforRead, saveLogs
from variables import CONN_ADRGS    , \
                      COUNT_DB      , \
                      IDS_TB_CREATE , \
                      INSERT_IDS_TB , \
                      ORGS_TB_CREATE, \
                      INSERT_ORGS_TB, \
                      TEST_INSERT
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
@c_logging
def __connect() -> Tuple[Any, Any]:
    """
    `This definition returns connection to database.`
    """
    con = connect_db(**CONN_ADRGS)        
    return con, con.cursor()


@c_logging
def __push_msg(msg : str) -> Any | bool:
    """
    `This definition sends message to database.`
    """
    con, cur = __connect()

    if con and cur:
        cur.execute(msg)

        con.commit()

        return cur.fetchall()

    return False
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
def get_db(table : str) -> str | bool:
    return __push_msg(f'SELECT * FROM {table};')


def insert_db(msg : str) -> str | bool:
    return __push_msg(f'{msg};')


def delete_db(_tb : str, msg : str) -> str | bool:
    return __push_msg(f'DELETE FROM {_tb} WHERE {msg}; {COUNT_DB} orgs_tb;')
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
def __test_database() -> None:

    __push_msg(ORGS_TB_CREATE)

    test = insert_db(TEST_INSERT)
    saveLogs(f'[DB_INSERT] [{test}] <- insert_db()\n\n')
    
    test = delete_db('orgs_tb', 'name = \'Grace SPA\'')
    saveLogs(f'[DB_DELETE] [{test}] <- delete_db()\n\n')


def __run_farm() -> None:

    from requests  import get as _get
    from variables import API_KEY_SET, RESULT_LIM , SEARCH_URL
    
    def __req(txt     : str, 
              res     : int, 
              skip    : int, 
              api_key : str) -> Dict | Literal[False] | List:
        try:
            req = _get(
                f'{SEARCH_URL}?text={txt}&type=biz&lang=ru_RU'
                f'&results={res}&skip={skip}&apikey={api_key}'
            ).json()
        except:
            return []

        return False if 'features' not in req.keys() else req['features']

    def __proc_req(category : str, 
                   api_key  : str, 
                   _ids     : List[str],
                   passes   : Tuple[int] = (0, 500, 1000), 
                   result   : int = RESULT_LIM):

        _st = {'added' : False, 'error' : False, 'over' : False}
        for skip in passes:
            data = __req(category, result, skip, api_key)

            if data:
                _ids = __add_items(data, _ids)

            elif data == [] and skip == 0:
                _st['over'] = True
                break
           
            if len(data) < 400:
                break
        
        if not _st['error'] and not _st['over']:
            _st['added'] = True

        return (_ids, _st)


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

        return [0, _id         , _name      ,
                   _description, _categories,
                   _address    , _phones    , 
                   _hours      , _available ]


    def __add_items(_its : List, _ids : List) -> List[int]:

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
                     ');                      '
                    f'{COUNT_DB} orgs_tb     ;'
                )
                insert_db(
                    f'{INSERT_IDS_TB} \'{_item[1]}\'); '
                    f'{COUNT_DB} orgs_tb     ;         '
                )
                _ids.append(int(_item[1]))

        return _ids


    __push_msg(ORGS_TB_CREATE)

    __push_msg(IDS_TB_CREATE)

    tup_ids = get_db('ids_tb')

    ids_set = [int(i[1]) for i in tup_ids]

    cat_added = []

    from variables import MAINCAT_CONST

    for api_key in API_KEY_SET:
        st = {'added' : False, 'error' : False, 'over' : False}
        
        for ctg in MAINCAT_CONST:
            if ctg not in cat_added:
                try:
                    ids_set, st = __proc_req(ctg, api_key, ids_set)

                    if st['added']:
                        cat_added.append(ctg)
                    if st['over']:
                        break
                except:
                    saveLogs(f'[__run_farm]-->{format_exc()}')
        
            st = {'added' : False, 'error' : False, 'over' : False}
         

def __is_eq() -> None:
    _f = False
    test = get_db('orgs_tb')

    ids = []

    for i in test:
        if i[1] not in ids:
            ids.append(i[1])
        else:
            saveLogs(f'[] [{i[1]}]\n\n')
            _f = True
    
    _ids = get_db('ids_tb')

    eq_ids = []

    for i in _ids:
        if i[1] not in eq_ids:
            eq_ids.append(i[1])
        else:
            saveLogs(f'[] [{i[1]}]\n\n')
            _f = True
    
    print(f'[EQ][{_f}]\n')
            

def __dump_tables() -> None:
    try:
        dump_json(get_db('orgs_tb'), open('orgs_tb.json', 'w'))
        print(f'[DUMP][True]\n')
    except:
        print(f'[DUMP][False]\n')
    

def __load_tables() -> None:

    orgs = load_json(open('orgs_tb.json'))
    bar = IncrementalBar('Loading', max = len(orgs))

    for org in orgs:
        bar.next()
        org[2] = org[2].replace("'", "''")
        org[3] = org[3].replace("'", "''")
        org[5] = org[5].replace("'", "''")
        if not insert_db(f'    {INSERT_ORGS_TB}  '
                         f'     \'{org[1]}\'   , '
                         f'     \'{org[2]}\'   , '
                         f'     \'{org[3]}\'   , '
                         f' ARRAY {org[4]}     , '
                         f'     \'{org[5]}\'   , '
                         f' ARRAY {org[6]}     , '
                         f'     \'{org[7]}\'   , '
                         f'     \'{org[8]}\'     '
                          ');                    '
                         f'{COUNT_DB} orgs_tb   ;'):
            print('[LOAD][False]\n')
            return

        if not insert_db(f'{INSERT_IDS_TB} \'{org[1]}\'); '
                         f'{COUNT_DB} orgs_tb           ; '):
            print('[LOAD][False]\n')
            return
            
    bar.finish()
    print(f'[LOAD][True]')


def __help_msg():
    print(f"'-t' Database testing\n"
          f"'-s' Get database tables json\n"
          f"'-l' Load tables into clear database (json needed)\n"
          f"'-c' Create database tables\n"
          f"'-h' Get help message\n"
          f"'-f' Run organisations farming\n"
          f"'-e' Fing equal variables\n")


def __cr_tables():
    print(f'[ORGS_TB_CREATE][{__push_msg(ORGS_TB_CREATE)}]\n',
          f'[IDS_TB_CREATE][{__push_msg(IDS_TB_CREATE)}]\n')

def __file_load_tables() -> None:
    """
    #1 id: 86935271260
    name: Ptm Care
    dscr: ул. Хачатуряна, 8, корп. 5, Москва, Россия
    catg: ['Автомойка', 'Детейлинг', 'Шиномонтаж']
    addr: Россия, Москва, улица Хачатуряна, 8, корп. 5
    phne: ['', '+7 (915) 057-85-85']
    hrs : пн-чт 09:00–22:00; пт 14:00–22:00; сб,вс 09:00–22:00
    avlb: None
    """

    def __add_items(_its : List, _ids : List, _tb : str, _ks : str) -> List[int]:

        txt_tb = ''
        txt_ks = ''

        for _it in _its:
            
            if _it[1] not in _ids:

                txt_tb += f"('{_it[1]}',      '{_it[2]}'," \
                          f" '{_it[3]}', ARRAY {_it[4]} ," \
                          f" '{_it[5]}', ARRAY {_it[6]} ," \
                          f" '{_it[7]}', ARRAY {_it[8]}),"
                txt_ks += f"('{_it[1]}'),"

                _ids.append(int(_it[1]))
                
        if txt_tb:
            insert_db(f'{INSERT_ORGS_TB} {txt_tb[:-1]}; {COUNT_DB} {_tb};')
            insert_db(f'{INSERT_IDS_TB} {txt_ks[:-1]}; {COUNT_DB} {_ks};')

        return _ids
    
    
    orgs = []; org = []
    txt = openfileforRead('org.txt')

    for line in txt.split('\n')[1:]:
        line = line.split(':'); msg = ''
        if ('#' in line[0] ) and ('id' in line[0]):
            org = [0]
            for i in line[1:]:
                msg += i[1:]
            org.append(msg)
        elif not line[0]:
            orgs.append(org)
        elif '#' not in line[0]:
            if '[' in line[1]:
                msg = line[1][1:].strip('[]').replace(' ', '').replace("'", '').split(',')
            else:
                for i in line[1:]:
                    msg += i[1:]
            org.append(msg)
    
    __add_items(orgs, [], 'orgs_tb', 'ids_tb')

#\------------------------------------------------------------------/#


#\==================================================================/#
if __name__ == "__main__":

    DB_CONTROL_METHODS = {
        '-t' : __test_database,
        '-s' : __dump_tables,
        '-l' : __load_tables,
        '-c' : __cr_tables,
        '-h' : __help_msg,
        '-f' : __run_farm,
        '-e' : __is_eq
    }

    for _dvar in _dvars:
        if _dvar in DB_CONTROL_METHODS:
            DB_CONTROL_METHODS[_dvar]()
#\==================================================================/#
  