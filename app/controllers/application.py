from app.controllers.datarecord import UserRecord, MessageRecord
from bottle import template, redirect, request, response, Bottle, static_file
import socketio


class Application:
    def __init__(self):
        self.pages = {
            'portal': self.portal,
            'pagina': self.pagina,
            'chat': self.chat,
            'edit': self.edit
        }
        self.__users = UserRecord()
        self.__messages = MessageRecord()
        self.edited = False

        # Initialize Bottle app
        self.app = Bottle()
        self.setup_routes()

        # Initialize Socket.IO server
        self.sio = socketio.Server(async_mode='eventlet')
        self.setup_websocket_events()

        # Create WSGI app
        self.wsgi_app = socketio.WSGIApp(self.sio, self.app)

    def setup_routes(self):
        @self.app.route('/static/<filepath:path>')
        def serve_static(filepath):
            return static_file(filepath, root='./app/static')

        @self.app.route('/pagina', method='GET')
        def pagina_getter():
            return self.render('pagina')

        @self.app.route('/chat', method='GET')
        def chat_getter():
            return self.render('chat')

        @self.app.route('/')
        @self.app.route('/portal', method='GET')
        def login():
            return self.render('portal')

        @self.app.route('/edit', method='GET')
        def edit_getter():
            return self.render('edit')

        @self.app.route('/portal', method='POST')
        def portal_getter():
            username = request.forms.get('username')
            password = request.forms.get('password')
            self.authenticate_user(username, password)
            return self.render('portal')  # Adicione uma resposta apropriada

        @self.app.route('/edit', method='POST')
        def edit_post():
            username = request.forms.get('username')
            password = request.forms.get('password')
            self.update_user(username, password)
            return self.render('edit')  # Adicione uma resposta apropriada

        @self.app.route('/logout', method='POST')
        def logout_action():
            self.logout_user()
            return self.render('portal')

    def setup_websocket_events(self):
        @self.sio.event
        async def connect(sid, environ):
            print(f'Client connected: {sid}')
            self.sio.emit('connected', {'data': 'Connected'}, room=sid)

        @self.sio.event
        async def disconnect(sid):
            print(f'Client disconnected: {sid}')

        @self.sio.event
        def message(sid, data):
            print(f'SIO.EVENT: Fui disparada pelo chat com: {data}')
            objdata = self.newMessage(data)
            self.sio.emit('message', {'content': objdata.content, 'username': objdata.username})

        @self.sio.event
        def login(sid, data):
            print(f'Login event received from app: {data}')
            username = data.get('username')
            if username:
                self.broadcast_user_list()

    def broadcast_user_list(self):
        users = self.getAuthenticatedUsers()
        self.sio.emit('updateUsers', {'users': [user.username for user in users]})

    def render(self, page, parameter=None):
        content = self.pages.get(page, self.portal)
        if not parameter:
            return content()
        return content(parameter)

    def getAuthenticatedUsers(self):
        return self.__users.getAuthenticatedUsers()

    def getCurrentUserBySessionId(self):
        session_id = request.get_cookie('session_id')
        return self.__users.getCurrentUser(session_id)

    def edit(self):
        current_user = self.getCurrentUserBySessionId()
        return template('app/views/html/edit', user=current_user)

    def portal(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            portal_render = template('app/views/html/portal', username=current_user.username, edited=self.edited)
            self.edited = False
            return portal_render
        portal_render = template('app/views/html/portal', username=None, edited=self.edited)
        self.edited = False
        return portal_render

    def pagina(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            return template('app/views/html/pagina', transfered=True, current_user=current_user)
        return template('app/views/html/pagina', transfered=False)

    def is_authenticated(self, username):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            return username == current_user.username
        return False

    def authenticate_user(self, username, password):
        session_id = self.__users.checkUser(username, password)
        if session_id:
            self.logout_user()
            response.set_cookie('session_id', session_id, httponly=True, secure=True, max_age=3600)
            redirect('/pagina')
        redirect('/portal')

    def login(self):
        return template('app/views/html/login')

    def update_user(self, username, password):
        self.__users.setUser(username, password)
        self.edited = True
        redirect('/portal')

    def logout_user(self):
        session_id = request.get_cookie('session_id')
        self.__users.logout(session_id)
        response.delete_cookie('session_id')

    def chat(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            messages = self.__messages.getUsersMessages()
            return template('app/views/html/chat', current_user=current_user, messages=messages)
        redirect('/portal')

    def newMessage(self, message):
        try:
            content = message
            current_user = self.getCurrentUserBySessionId()
            return self.__messages.book(current_user.username, content)
        except UnicodeEncodeError as e:
            print(f"Encoding error: {e}")
            return "An error occurred while processing the message."
