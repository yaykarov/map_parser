#/==================================================================\#
# utility.py                                          (c) Mtvy, 2022 #
#\==================================================================/#
#                                                                    #
# Copyright (c) 2022. Mtvy (Matvei Prudnikov, m.d.prudnik@gmail.com) #
#                                                                    #
#\==================================================================/#

#/-----------------------------/ Libs \-----------------------------\#
from io            import open   as _open
from os            import remove as _rmv
from os.path       import exists as _is_exist
from typing        import List, Tuple, Callable, Literal, Any
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime      import datetime as dt
from path          import LOG_FILE
from traceback     import format_exc
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
def c_logging(func : Callable) -> Any | Literal[False]:
    
    def wrap_func(*args, **kwargs) -> Any | Literal[False]:
        try:
            return func(*args, **kwargs)
        except:
            saveLogs(f"[{func.__name__}]-->{format_exc()}")
        return False

    return wrap_func
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
def saveLogs(txt : str, _f : str = LOG_FILE) -> int:
    return saveText(f'\nDate: {dt.now()}\n\n{txt}', _f)
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
def saveText(txt, _f, _md = 'a', _enc = 'utf-8') -> int:
    return open(file = _f, mode = _md, encoding = _enc).write(txt)
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
def openfileforRead(file = None, txt = '') -> str:
    return txt.join([i for i in _open(file, encoding='utf-8')])
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
@c_logging
def rmvFile(pth : str) -> bool:
    if _is_exist(pth):
        _rmv(pth)
        return True
    return False
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
@c_logging
def set_keyboard(btns : List[str]) -> ReplyKeyboardMarkup:
    """
    Making keyboard
    """

    def __get_keyboard(resize=True) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(resize_keyboard=resize)


    def __get_btn(txt : str) -> KeyboardButton:
        return KeyboardButton(txt)


    def __gen_btns(btns : List[str]) -> Tuple[KeyboardButton]:
        return (__get_btn(txt) for txt in btns)


    key = __get_keyboard()
    key.add(*__gen_btns(btns))

    return key
#\------------------------------------------------------------------/#


#\==================================================================/#
if __name__ == "__main__":
    ...
#\==================================================================/#
