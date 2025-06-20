from app.controllers.datarecord import UserRecord, MessageRecord,HouseRecord
from bottle import template, redirect, request, response, Bottle, static_file
import socketio


class Application:

    def __init__(self):

        self.pages = {
            'portal': self.portal,
            'pagina': self.pagina,
            'cadastro': self.cadastro,
            'homepage': self.homepage,
            'delete': self.delete,
            'chat': self.chat,
            'edit': self.edit
        }
        self.__users = UserRecord()
        self.__messages = MessageRecord()
        self.__houses = HouseRecord()

        self.edited = None
        self.removed = None
        self.created= None

        # Initialize Bottle app
        self.app = Bottle()
        self.setup_routes()

        # Initialize Socket.IO server
        self.sio = socketio.Server(async_mode='eventlet')
        self.setup_websocket_events()

        # Create WSGI app
        self.wsgi_app = socketio.WSGIApp(self.sio, self.app)


    # estabelecimento das rotas
    def setup_routes(self):
        @self.app.route('/static/<filepath:path>')
        def serve_static(filepath):
            return static_file(filepath, root='./app/static')

        @self.app.route('/favicon.ico')
        def favicon():
            return static_file('favicon.ico', root='./app/static')

        @self.app.route('/pagina', method='GET')
        def pagina_getter():
            return self.render('pagina')

        @self.app.route('/chat', method='GET')
        def chat_getter():
            return self.render('chat')

        @self.app.route('/')
        @self.app.route('/portal', method='GET')
        def portal_getter():
            return self.render('portal')
        

        @self.app.route('/edit', method='GET')
        def edit_getter():
            return self.render('edit')
        

        @self.app.route('/portal', method='POST')
        def portal_action():
            username = request.forms.get('username')
            password = request.forms.get('password')
            return self.authenticate_user(username, password)

        @self.app.route('/edit', method='POST')
        def edit_action():
            username = request.forms.get('username')
            password = request.forms.get('password')
            print(username + ' sendo atualizado...')
            self.update_user(username, password)
            return self.render('edit')

        @self.app.route('/cadastro', method='GET')
        def create_getter():
            return self.render('cadastro')
        
        @self.app.route('/cadastro', method='POST')
        def create_action():
            fullname = request.forms.get('fullname')
            username = request.forms.get('username')
            birthdate = request.forms.get('birthdate')
            email = request.forms.get('email')
            password = request.forms.get('password')
            confirm_password = request.forms.get('confirm_password')
            gender = request.forms.get('gender')
            self.insert_user(fullname,username,birthdate, email, password, confirm_password, gender)
            return self.render('portal')
        

        @self.app.route('/homepage', method='GET')
        def homepage_getter():
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal')  # Usuário não autenticado
            casa = self.__houses.get_house_by_user(current_user.username)
            if casa:
                # Usuário está em uma casa, renderiza informações da casa
                return template('app/views/html/homepage_in_house', user=current_user, casa=casa)
            else:
                # Usuário não está em casa, renderiza opções criar / entrar em casa
                houses_list = self.__houses.list_houses()
                return template('app/views/html/homepage_no_house', user=current_user, houses=houses_list)
            
        @self.app.route('/create_house', method='POST')
        def create_house():
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal')
            house_name = request.forms.get('house_name')
            if house_name:
                house_id = self.__houses.create_house(house_name, current_user.username)
                # Opcional: atualizar estado do usuário para associar house_id (pode ser com banco)
                return redirect('/homepage')
            return redirect('/homepage')
        # Rota para entrar numa casa existente

        @self.app.route('/join_house', method='POST')
        def join_house(self):
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal')
            house_id = request.forms.get('house_id')
            if house_id and self.__houses.house_exists(house_id):
                self.__houses.add_user_to_house(house_id, current_user.username)
                # Opcional: persistir que usuário entrou na casa
                return redirect('/homepage')
            return redirect('/homepage')

        @self.app.route('/logout', method='POST')
        def logout_action():
            self.logout_user()
            return self.render('portal')

        @self.app.route('/delete', method='GET')
        def delete_getter():
            return self.render('delete')

        @self.app.route('/delete', method='POST')
        def delete_action():
            self.delete_user()
            return self.render('portal')
    
    # método controlador de acesso às páginas:
    def render(self, page, parameter=None):
        content = self.pages.get(page, self.portal)
        if not parameter:
            return content()
        return content(parameter)

    # métodos controladores de páginas
    def getAuthenticatedUsers(self):
        return self.__users.getAuthenticatedUsers()

    def getCurrentUserBySessionId(self):
        session_id = request.get_cookie('session_id')
        return self.__users.getCurrentUser(session_id)

    def cadastro(self):
        return template('app/views/html/cadastro')

    def delete(self):
        current_user = self.getCurrentUserBySessionId()
        user_accounts= self.__users.getUserAccounts()
        return template('app/views/html/delete', user=current_user, accounts=user_accounts)

    def edit(self):
        current_user = self.getCurrentUserBySessionId()
        user_accounts= self.__users.getUserAccounts()
        return template('app/views/html/edit', user=current_user, accounts= user_accounts)

    def portal(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            portal_render = template('app/views/html/portal', \
            username=current_user.username, edited=self.edited, \
            removed=self.removed, created=self.created)
            self.edited = None
            self.removed= None
            self.created= None
            return portal_render
        portal_render = template('app/views/html/portal', username=None, \
        edited=self.edited, removed=self.removed, created=self.created)
        self.edited = None
        self.removed= None
        self.created= None
        return portal_render

    def pagina(self):
        self.update_users_list()
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            return template('app/views/html/pagina', transfered=True, current_user=current_user)
        return template('app/views/html/pagina', transfered=False)

    def homepage(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            return(template('app/views/html/homepage', user=current_user))
        return redirect('/portal')

    def is_authenticated(self, username):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            return username == current_user.username
        return False
    
    def authenticate_user(self, username, password):
            session_id = self.__users.checkUser (username, password)
            if session_id:
                self.logout_user()
                response.set_cookie('session_id', session_id, httponly=True, secure=True, max_age=3600)
                return redirect('/homepage')  # Redireciona para a página após login
            return redirect('/portal')  # Redireciona de volta para o portal se falhar

    def delete_user(self):
        current_user = self.getCurrentUserBySessionId()
        self.logout_user()
        self.removed= self.__users.removeUser(current_user)
        self.update_account_list()
        print(f'Valor de retorno de self.removed: {self.removed}')
        return redirect('/portal')

    def insert_user(self, fullname,username,birthdate, email, password, confirm_password, gender):
        self.created= self.__users.book(fullname,username,birthdate, email, password, confirm_password, gender,[])
        self.update_account_list()
        return redirect('/portal')

    def update_user(self, username, password):
        self.edited = self.__users.setUser(username, password)
        redirect('/portal')

    def logout_user(self):
        session_id = request.get_cookie('session_id')
        self.__users.logout(session_id)
        response.delete_cookie('session_id')
        self.update_users_list()

    def chat(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            messages = self.__messages.getUsersMessages()
            auth_users= self.__users.getAuthenticatedUsers().values()
            return template('app/views/html/chat', current_user=current_user, \
            messages=messages, auth_users=auth_users)
        redirect('/portal')

    def newMessage(self, message):
        try:
            content = message
            current_user = self.getCurrentUserBySessionId()
            return self.__messages.book(current_user.username, content)
        except UnicodeEncodeError as e:
            print(f"Encoding error: {e}")
            return "An error occurred while processing the message."


    # Websocket:
    def setup_websocket_events(self):

        @self.sio.event
        async def connect(sid, environ):
            print(f'Client connected: {sid}')
            self.sio.emit('connected', {'data': 'Connected'}, room=sid)

        @self.sio.event
        async def disconnect(sid):
            print(f'Client disconnected: {sid}')

        # recebimento de solicitação de cliente para atualização das mensagens
        @self.sio.event
        def message(sid, data):
            objdata = self.newMessage(data)
            self.sio.emit('message', {'content': objdata.content, 'username': objdata.username})

        # solicitação para atualização da lista de usuários conectados. Quem faz
        # esta solicitação é o próprio controlador. Ver update_users_list()
        @self.sio.event
        def update_users_event(sid, data):
            self.sio.emit('update_users_event', {'content': data})

        # solicitação para atualização da lista de usuários conectados. Quem faz
        # esta solicitação é o próprio controlador. Ver update_users_list()
        @self.sio.event
        def update_account_event(sid, data):
            self.sio.emit('update_account_event', {'content': data})

    # este método permite que o controller se comunique diretamente com todos
    # os clientes conectados. Sempre que algum usuários LOGAR ou DESLOGAR
    # este método vai forçar esta atualização em todos os CHATS ativos. Este
    # método é chamado sempre que a rota ''
    def update_users_list(self):
        print('Atualizando a lista de usuários conectados...')
        users = self.__users.getAuthenticatedUsers()
        users_list = [{'username': user.username} for user in users.values()]
        self.sio.emit('update_users_event', {'users': users_list})

    # este método permite que o controller se comunique diretamente com todos
    # os clientes conectados. Sempre que algum usuários se removerem
    # este método vai comunicar todos os Administradores ativos.
    def update_account_list(self):
        print('Atualizando a lista de usuários cadastrados...')
        users = self.__users.getUserAccounts()
        users_list = [{'username': user.username} for user in users]
        self.sio.emit('update_account_event', {'accounts': users_list})
