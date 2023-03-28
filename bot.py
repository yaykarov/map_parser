#/==================================================================\#
# bot.py                                              (c) Yaykarov, 2022 #
#\==================================================================/#
#                                                                    #
# Copyright (c) 2022. Yaykarov (Timur Yaykarov, timmyya999@gmail.com) #
#                                                                    #
#\==================================================================/#

#/------------------------/ installed libs \------------------------\#
from stun            import get_ip_info
from telebot         import TeleBot
from telebot.types   import Message, Update
from cherrypy        import HTTPError

import cherrypy
#--------------------------\ project files /-------------------------#
from emj       import EMJ_RAISING_HAND, EMJ_CROSS, EMJ_NOTE
from variables import TOKEN
from admin     import init_admin   , proc_admin
from user      import init_user    , proc_user
from handling  import start_handler, kill_handler
from utility   import c_logging
from database  import get_db
#\------------------------------------------------------------------/#

#\------------------------------------------------------------------/#
bot = TeleBot(TOKEN)
#\------------------------------------------------------------------/#

#\------------------------------------------------------------------/#
WEBHOOK_HOST   = get_ip_info()[1]
WEBHOOK_PORT   = 8443  
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'

WEBHOOK_URL_BASE = f'https://{WEBHOOK_HOST}:{WEBHOOK_PORT}'
WEBHOOK_URL_PATH = f'/{TOKEN}/'
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
#                               WebHook                              #
#\------------------------------------------------------------------/#
class WebhookServer(object):

    @cherrypy.expose
    def index(self):
        _hdrs = cherrypy.request.headers
        _body = cherrypy.request.body

        if 'content-length' in _hdrs and 'content-type' in _hdrs and \
            _hdrs['content-type'] == 'application/json':

            length      = int(_hdrs['content-length'])
            json_string = _body.read(length).decode("utf-8")
            update      = Update.de_json(json_string)

            bot.process_new_updates([update])

            return ''
        else:
            raise HTTPError(403)
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
admin_ID  = {281321076  : None}
users_IDS = {5472647497 : None, 298602990 : None}
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
@bot.message_handler(commands=['start'])
@c_logging
def start(msg : Message) -> None:
    _id = msg.chat.id
    if _id in users_IDS.keys():
        init_user(bot, _id)
    elif _id in admin_ID.keys():
        init_admin(bot, _id)
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
KEYBOARD_FUNC = {
    f'{EMJ_RAISING_HAND} Начать': start_handler,
    f'{EMJ_CROSS} Остановить'   : kill_handler
}

@bot.message_handler(content_types=['text'])
@c_logging
def input_keyboard(msg : Message):

    global admin_ID, users_IDS

    _id : int = msg.chat.id
    txt : str = msg.text

    if txt in KEYBOARD_FUNC: 
        if _id in users_IDS.keys():

            _ids = [int(i[1]) for i in get_db('ids_tb')]
            if not users_IDS[_id]:
                users_IDS[_id] = proc_user(_id, _ids)

            users_IDS[_id] = KEYBOARD_FUNC[
                txt](bot, users_IDS[_id], _id)


        elif _id in admin_ID.keys():

            if not admin_ID[_id]:
                admin_ID[_id] = proc_admin(_id)

            admin_ID[_id] = KEYBOARD_FUNC[
                txt](bot, admin_ID[_id], _id)

        else:
            bot.send_message(_id, f'{EMJ_NOTE} Нет доступа!')
#\------------------------------------------------------------------/#


#\------------------------------------------------------------------/#
@c_logging
def proc_bot() -> None:
    bot.remove_webhook()

    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                    certificate=open(WEBHOOK_SSL_CERT, 'r'))

    cherrypy.config.update({
        'server.socket_host'    : WEBHOOK_LISTEN,
        'server.socket_port'    : WEBHOOK_PORT,
        'server.ssl_module'     : 'builtin',
        'server.ssl_certificate': WEBHOOK_SSL_CERT,
        'server.ssl_private_key': WEBHOOK_SSL_PRIV,
        'log.access_file'       : 'access.log',
        'log.error_file'        : 'errors.log',
        'log.screen'            : False
    })
    cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
#\------------------------------------------------------------------/#

#\==================================================================/#
if __name__ == "__main__":
    proc_bot()
#\==================================================================/#
