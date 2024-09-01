from app.controllers.application import Application
from app.config.server import HTTPBottleServer, WebsocketServer
from bottle import route, run, request, static_file
import eventlet
import socketio


# Inicialize o servidor HTTP e WebSocket

http_server = HTTPBottleServer()
websocket_server = WebsocketServer(http_server.app)
ctl = Application()


# Rotas HTTP

@http_server.app.route('/static/<filepath:path>')
def serve_static(filepath):
    return static_file(filepath, root='./app/static')

@http_server.app.route('/pagina', method='GET')
def pagina_getter():
    return ctl.render('pagina')

@http_server.app.route('/chat', method='GET')
def chat_getter():
    return ctl.render('chat')

@http_server.app.route('/')
@http_server.app.route('/portal', method='GET')
def login():
    return ctl.render('portal')

@http_server.app.route('/edit', method='GET')
def edit_getter():
    return ctl.render('edit')

@http_server.app.route('/portal', method='POST')
def portal_getter():
    username = request.forms.get('username')
    password = request.forms.get('password')
    ctl.authenticate_user(username, password)
    return ctl.render('portal')  # Adicione uma resposta apropriada

@http_server.app.route('/edit', method='POST')
def edit_post():
    username = request.forms.get('username')
    password = request.forms.get('password')
    ctl.update_user(username, password)
    return ctl.render('edit')  # Adicione uma resposta apropriada

@http_server.app.route('/logout', method='POST')
def logout_action():
    ctl.logout_user()
    return ctl.render('portal')


# Eventos WebSocket

@websocket_server.sio.event
async def connect(sid, environ):
    print(f'Client connected: {sid}')
    websocket_server.sio.emit('connected', {'data': 'Connected'}, room=sid)

@websocket_server.sio.event
async def disconnect(sid):
    print(f'Client disconnected: {sid}')

@websocket_server.sio.event
def message(sid, data):
    print(f'SIO.EVENT: Fui disparada pelo chat com: {data}')
    objdata = ctl.newMessage(data)
    websocket_server.sio.emit('message', {'content': objdata.content, 'username': objdata.username})

@websocket_server.sio.event
def login(sid, data):
    print(f'Login event received from app: {data}')
    username = data.get('username')
    if username:
        broadcast_user_list()

def broadcast_user_list():
    users = ctl.getAuthenticatedUsers()
    websocket_server.sio.emit('updateUsers', {'users': [user.username for user in users]})


if __name__ == '__main__':

    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8080)), websocket_server.wsgi_app)
