from bottle import Bottle
import socketio
import eventlet
import eventlet.wsgi


# Servidor HTTP
class HTTPBottleServer:

    def __init__(self):
        self.app = Bottle()
        self.setup_app()

    def setup_app(self):
        self.app.config['default_locale'] = 'pt_BR'
        self.app.config['charset'] = 'utf-8'



# Servidor WebSocket
class WebsocketServer:

    def __init__(self, app):
        self.app = app
        self.setup_socketio()
        self.setup_wsgi()

    def setup_socketio(self):
        self.sio = socketio.Server(async_mode='eventlet')

    def setup_wsgi(self):
        self.wsgi_app = socketio.WSGIApp(self.sio, self.app)
