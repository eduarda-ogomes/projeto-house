from app.controllers.application import Application
from app.config.server import ServerHTTP
from bottle import route, run, request, static_file
from bottle import redirect, template
import eventlet
import socketio
import asyncio


server = ServerHTTP()
ctl = Application()


#-----------------------------------------------------------------------------
# Websocket


sio = socketio.Server(async_mode='eventlet')
wsgi_app = socketio.WSGIApp(sio, server.app)

#-----------------------------------------------------------------------------
# Rotas:

@server.app.route('/static/<filepath:path>')
def serve_static(filepath):
    return static_file(filepath, root='./app/static')


# ------------------------------------------------------------------------------
# Rota para Socket.IO WebSocket (não precisa de rota específica)

@sio.event
async def connect(sid, environ):
    print(f'Client connected: {sid}')
    sio.emit('connected', {'data': 'Connected'}, room=sid)

@sio.event
async def disconnect(sid):
    print(f'Client disconnected: {sid}')

@sio.event
def message(sid, data):
    print(f'SIO.EVENT: Fui disparada pelo chat com: {data}')
    objdata= ctl.newMessage(data)
    sio.emit('message', {'content': objdata.content, 'username': objdata.username})


#-----------------------------------------------------------------------------
# Suas rotas aqui:

@server.app.route('/pagina', method='GET')
def pagina_getter():
    return ctl.render('pagina')


@server.app.route('/chat', method='GET')
def chat_getter():
    return ctl.render('chat')


@server.app.route('/')
@server.app.route('/portal', method='GET')
def login():
    return ctl.render('portal')


@server.app.route('/edit', method='GET')
def login_getter():
    return ctl.render('edit')


@server.app.route('/portal', method='POST')
def portal_getter():
    username = request.forms.get('username')
    password = request.forms.get('password')
    ctl.authenticate_user(username, password)


@server.app.route('/edit', method='POST')
def login_getter():
    username = request.forms.get('username')
    password = request.forms.get('password')
    ctl.update_user(username, password)


@server.app.route('/logout', method='POST')
def logout_action():
    ctl.logout_user()
    return ctl.render('portal')



if __name__ == '__main__':

    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8080)), wsgi_app)
