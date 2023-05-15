import logging
import time
import uuid
from pathlib import Path

import socketio
from aiohttp import web

from chatidea import extractor, caller

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    cors_allowed_origins=[])  # Only for SSL workaround so that socketio works with requests from other origins.
# sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)


async def index(request):
    """Serve the client-side application."""
    with open(Path(__file__).resolve().parent / 'index.html', "r") as f:
        return web.Response(text=f.read(), content_type='text/html')


# START SOCKET CONNECTION
@sio.event
def connect(sid, environ):
    logger.info("connect %s", sid)


@sio.event
def disconnect(sid):
    logger.info('disconnect %s', sid)


@sio.on('session_request')
async def session_request(sid, data):
    if data is None:
        data = {}
    if 'session_id' not in data or data['session_id'] is None:
        data['session_id'] = uuid.uuid4().hex
    logger.info('session_confirm: %s', data['session_id'])
    await sio.emit("session_confirm", data['session_id'], room=sid)


# END SOCKET CONNECTION


@sio.on('user_uttered')  # ON USER MESSAGE
async def handle_message(sid, message_dict):
    all_quick_replies = []
    message = message_dict['message']
    parsed_message = extractor.parse(message)
    response = caller.run_action_from_parsed_message(parsed_message,
                                                     "WEBCHAT_" + str(sid))
    print(response.get_printable_string())
    for x in response.get_telegram_or_webchat_format():
        text = x['message']
        if text == 'Pie chart':
            send_message = {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "title": "Category table",
                        "src": f"/static/pie.png?{time.time()}"
                    }
                }
            }
            await sio.emit('bot_uttered', send_message, room=sid)
        else:
            all_quick_replies = [{
                'title': b['title'],
                'payload': b['payload']
            } for b in x.get('buttons', [])]
            send_message = {"text": text, "quick_replies": all_quick_replies}
            await sio.emit('bot_uttered', send_message, room=sid)


Path('./static').mkdir(parents=True, exist_ok=True)
app.router.add_static('/static', './static')
app.router.add_get('/', index)


def start():
    # cert_path = os.path.dirname(os.path.realpath(__file__))
    # context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    # context.load_cert_chain(certfile=cert_path+ "/certificate.crt", keyfile= cert_path+"/private.key")
    # web.run_app(app, port=5080,ssl_context=context)
    web.run_app(app, port=5080)
