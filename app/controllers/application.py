# application.py
from app.controllers.datarecord import UserRecord, MessageRecord, HouseRecord
# Importe o UserMessage aqui também, já que ele é usado no WebSocket
from app.models.user_message import UserMessage
from bottle import template, redirect, request, response, Bottle, static_file, HTTPError, post
import socketio
import datetime
from datetime import date, timedelta
import time
import hashlib
from threading import Timer

# Certifique-se de que o eventlet está instalado: pip install eventlet
import eventlet
eventlet.monkey_patch() # Importante para Socket.IO assíncrono

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
        self.__houses = HouseRecord() # Garante que está ativo e inicializado

        self.edited = None
        self.removed = None
        self.created = None

        # Initialize Bottle app
        self.app = Bottle()
        self.setup_routes()

        # Initialize Socket.IO server
        # Permitir CORS para o Socket.IO se o frontend e backend estiverem em domínios diferentes
        self.sio = socketio.Server(async_mode='eventlet', cors_allowed_origins="*")
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
            # Esta rota de chat pode ser mantida para um chat geral ou removida se o chat for apenas na homepage
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

        @self.app.get('/profile')
        def profile_page():
            session_id = request.get_cookie("session_id")
            current_user = None
            if session_id:
                current_user = self.__users.getCurrentUser(session_id)

            if not current_user:
                return redirect('/portal')

            return template('profile', user=current_user)


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
            # Você precisa verificar se as senhas coincidem aqui, antes de chamar book
            if password != confirm_password:
                # Retorne uma mensagem de erro para o template de cadastro
                return template('app/views/html/cadastro', error="As senhas não coincidem.")
            self.insert_user(fullname, username, birthdate, email, password, confirm_password, gender)
            return self.render('portal')

        @self.app.route('/homepage', method='GET')
        def homepage_getter():
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal')

            house = self.__houses.get_house_by_user(current_user.username)
            if house:
                members = house.members
                if not isinstance(members, list):
                    members = []
                    print(f"AVISO: house.members não é uma lista para casa {house.id}. Resetando para lista vazia.")

                # Correção do erro no loop de chores - `rotation_days` era usado antes de ser definido
                for chore in house.chores:
                    rotation_days = chore.get('rotation_days')
                    next_due_str = chore.get('next_due')
                    last_completed_date_str = chore.get('last_completed_date')

                    if (rotation_days is not None and rotation_days > 0 and
                        next_due_str): # A rotação deve acontecer independentemente de ter sido completada ou não
                                      # pois next_due_date já indica a próxima data de vencimento.

                        try:
                            next_due_date = datetime.datetime.strptime(next_due_str, '%Y-%m-%d').date()
                            today = date.today()

                            # Se a data de vencimento passou ou é hoje
                            if next_due_date <= today:
                                current_assignee = chore.get('assigned_to')
                                if current_assignee in members:
                                    current_index = members.index(current_assignee)
                                    next_index = (current_index + 1) % len(members)
                                    next_assignee = members[next_index]
                                else:
                                    # Se o atribuído atual não está mais na casa, atribui ao primeiro membro
                                    next_assignee = members[0] if members else None

                                if next_assignee:
                                    chore['assigned_to'] = next_assignee
                                    chore['next_due'] = (next_due_date + timedelta(days=rotation_days)).strftime('%Y-%m-%d')

                                    # Limpa o status de conclusão para a nova rotação APENAS SE A TAREFA FOI COMPLETADA ANTERIORMENTE
                                    # Isso é importante para não resetar tarefas que nunca foram completadas.
                                    if last_completed_date_str: # Se tinha uma data de conclusão, reseta
                                        chore['last_completed_date'] = None
                                        chore['last_completed_by'] = None
                                    
                                    self.__houses.save() # Salva a rotação
                                else:
                                    print(f"AVISO: Tarefa '{chore.get('activity', 'N/A')}' não rotacionada, sem próximos membros.")

                        except (ValueError, KeyError) as e:
                            print(f"Erro ao processar rotação da tarefa '{chore.get('activity', 'N/A')}': {e}")
                # Fim da correção do loop de chores

                my_chores = []
                other_chores = []
                for chore in house.chores:
                    if chore.get('assigned_to') == current_user.username:
                        my_chores.append(chore)
                    else:
                        other_chores.append(chore)
                
                # Obter mensagens da casa
                house_messages = self.__messages.getHouseMessages(house.id)

                return template(
                    'app/views/html/homepage_in_house',
                    user=current_user,
                    house=house,
                    my_chores=my_chores,
                    other_chores=other_chores,
                    messages=house_messages, # Passa as mensagens da casa para o template
                    datetime=datetime # Passando datetime para o template
                )
            else:
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
                return redirect('/homepage')
            return redirect('/homepage')

        @self.app.route('/join_house', method='POST')
        def join_house():
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal')
            house_id = request.forms.get('house_id')
            if house_id and self.__houses.house_exists(house_id):
                house = self.__houses.houses.get(house_id)
                if house:
                    house.add_member(current_user.username)
                    self.__houses.save()
                return redirect('/homepage')
            return redirect('/homepage')

        @self.app.route('/add_member', method='POST')
        def add_member():
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal')
            new_member_username = request.forms.get('username').strip()

            house = self.__houses.get_house_by_user(current_user.username)
            if house:
                if new_member_username in house.members:
                    print(f"Tentativa de adicionar membro duplicado: '{new_member_username}' na casa {house.id}")
                    # Adicione um feedback visual para o usuário se preferir
                    return redirect('/homepage')

                if not self.__users.user_exists(new_member_username):
                    print(f"AVISO: Usuário '{new_member_username}' não existe no sistema.")
                    # Melhor redirecionar com uma mensagem de erro
                    return template('app/views/html/homepage_in_house',
                                    user=current_user,
                                    house=house,
                                    my_chores=[], # Passa listas vazias ou as reais
                                    other_chores=[],
                                    messages=self.__messages.getHouseMessages(house.id),
                                    error_add_member=f"Usuário '{new_member_username}' não encontrado no sistema.")

                house.add_member(new_member_username)
                self.__houses.save()
                return redirect('/homepage')
            return redirect('/homepage')

        @self.app.post('/add_chore')
        def add_chore():
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal')

            activity = request.forms.get('activity').strip()
            date_str = request.forms.get('date')
            rotation_days = request.forms.get('rotation_days')

            if not activity or not date_str:
                return HTTPError(400, "Atividade e data são campos obrigatórios.")

            try:
                rotation_days = int(rotation_days) if rotation_days else 0
            except ValueError:
                return HTTPError(400, "Dias de rotatividade inválidos.")

            house = self.__houses.get_house_by_user(current_user.username)
            if not house:
                return HTTPError(404, "Casa não encontrada para adicionar tarefa.")

            # Você precisa definir quem será o primeiro atribuído.
            # Uma boa lógica seria atribuir ao usuário atual ou ao primeiro membro da casa.
            assigned_to = current_user.username if current_user.username in house.members else (house.members[0] if house.members else None)
            if not assigned_to:
                return HTTPError(400, "Não há membros na casa para atribuir a tarefa.")

            house.add_chore(
                activity=activity,
                date_str=date_str,
                rotation_days=rotation_days,
                next_due=date_str,
                assigned_to=assigned_to # Adicionei o assigned_to aqui
            )
            self.__houses.save()

            return redirect('/homepage')

        @self.app.post('/complete_chore/<house_id>')
        def complete_chore_post(house_id):
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal')

            house_id_str = str(house_id)
            house = self.__houses.get_house_by_user(current_user.username)

            if not house or house.id != house_id_str:
                return HTTPError(403, "Acesso negado ou casa inválida.")

            activity_to_complete = request.forms.get('activity')

            if house.complete_chore(activity_to_complete, current_user.username):
                self.__houses.save()
            else:
                return HTTPError(404, "Tarefa não encontrada ou não atribuída a você.")

            return redirect('/homepage')

        @self.app.post('/remove_chore/<house_id>')
        def remove_chore(house_id):
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal')

            house_id_str = str(house_id)
            activity_to_remove = request.forms.get('activity')

            if not activity_to_remove:
                return HTTPError(400, "Atividade para remover não fornecida.")

            house = self.__houses.get_house_by_user(current_user.username)
            if not house or house.id != house_id_str:
                return HTTPError(403, "Acesso negado ou casa inválida.")

            initial_chore_count = len(house.chores)
            house.chores = [
                chore for chore in house.chores
                if chore['activity'] != activity_to_remove
            ]

            if len(house.chores) == initial_chore_count:
                return HTTPError(404, "Tarefa não encontrada para remover.")

            self.__houses.save()
            return redirect('/homepage')

        @self.app.post('/remove_member/<house_id>')
        def remove_member(house_id):
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal')

            house_id_str = str(house_id)
            member_to_remove = request.forms.get('username')

            if not member_to_remove:
                return HTTPError(400, "Usuário para remover não fornecido.")

            house = self.__houses.get_house_by_user(current_user.username)
            if not house or house.id != house_id_str:
                return HTTPError(403, "Acesso negado ou casa inválida.")

            if member_to_remove == current_user.username:
                return HTTPError(403, "Você não pode se remover da casa por aqui.")

            if len(house.members) == 1 and house.members[0] == member_to_remove:
                 return HTTPError(403, "Não é possível remover o único membro da casa.")


            initial_member_count = len(house.members)
            house.members = [
                member for member in house.members
                if member != member_to_remove
            ]

            if len(house.members) == initial_member_count:
                return HTTPError(404, "Membro não encontrado ou não pode ser removido.")

            for chore in house.chores:
                if chore.get('assigned_to') == member_to_remove:
                    # Reatribui a tarefa para o usuário atual, se ele ainda estiver na casa
                    # ou para o primeiro membro restante, ou None se não houver membros
                    chore['assigned_to'] = current_user.username if current_user.username in house.members else (house.members[0] if house.members else None)
                    if chore.get('last_completed_by') == member_to_remove:
                        chore['last_completed_by'] = None
                        chore['last_completed_date'] = None

            self.__houses.save()
            return redirect('/homepage')

        @self.app.post('/update_profile')
        def update_profile():
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal') # Redireciona se não estiver logado

            # Pega os dados do formulário
            fullname = request.forms.get('fullname').strip()
            email = request.forms.get('email').strip()
            birthdate = request.forms.get('birthdate').strip()
            gender = request.forms.get('gender').strip()
            new_password = request.forms.get('password')
            confirm_password = request.forms.get('confirm_password')

            # Validações básicas
            if not fullname or not email or not birthdate or not gender:
                return template('profile', user=current_user, error="Todos os campos obrigatórios devem ser preenchidos.")

            # Validação de email (básica)
            if '@' not in email or '.' not in email:
                return template('profile', user=current_user, error="Formato de email inválido.")

            # Validação de senhas
            if new_password: # Se uma nova senha foi fornecida
                if new_password != confirm_password:
                    return template('profile', user=current_user, error="As novas senhas não coincidem.")
                if len(new_password) < 6: # Exemplo de regra de senha
                    return template('profile', user=current_user, error="A nova senha deve ter no mínimo 6 caracteres.")

                # Atualiza a senha (no UserAccount e UserRecord)
                # O setUser já faz isso, então está correto.
                self.__users.setUser(current_user.username, new_password)

            try:
                # Atualiza os atributos do objeto user (que é o current_user)
                current_user.fullname = fullname
                current_user.email = email
                current_user.birthdate = birthdate
                current_user.gender = gender
                # Chama o updateUser no UserRecord para persistir as alterações
                self.__users.updateUser(current_user)
                return template('profile', user=current_user, message="Perfil atualizado com sucesso!")

            except Exception as e:
                print(f"Erro ao atualizar perfil: {e}")
                return template('profile', user=current_user, error="Ocorreu um erro ao atualizar o perfil.")


        @self.app.route('/logout', method='POST')
        def logout_action():
            self.logout_user()
            return self.render('portal')

        # Este método `logout_user` deve ser uma função de nível de classe ou um método estático,
        # ou ser acessado via `self.logout_user()` se for um método de instância.
        # Ajustei para `self.logout_user()` nas rotas que o chamam.
        # Removi o `def logout_user(self):` duplicado aqui.


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

    def homepage(self): # Este método homepage nunca é chamado, a rota chama homepage_getter
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            # Isso é um fallback, mas a rota principal (/homepage GET) chama homepage_getter
            return template('app/views/html/homepage_in_house', user=current_user, house=None, my_chores=[], other_chores=[], messages=[], datetime=datetime)
        return redirect('/portal')


    def is_authenticated(self, username):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            return username == current_user.username
        return False

    def authenticate_user(self, username, password):
            session_id = self.__users.checkUser (username, password)
            if session_id:
                # O logout_user limpa o cookie, então é importante definir o novo cookie DEPOIS
                # Removido o self.logout_user() daqui pois ele desloga antes de setar o novo cookie.
                # A lógica de invalidar sessões antigas deve estar no checkUser ou ser gerenciada de outra forma.
                response.set_cookie('session_id', session_id, httponly=True, secure=False, max_age=3600, path='/') # secure=True para HTTPS
                return redirect('/homepage')
            return redirect('/portal')

    def delete_user(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user: # Certifica-se de que há um usuário para remover
            self.logout_user() # Desloga antes de remover do registro
            self.removed = self.__users.removeUser(current_user)
            self.update_account_list()
            print(f'Valor de retorno de self.removed: {self.removed}')
        return redirect('/portal')


    def insert_user(self, fullname,username,birthdate, email, password, confirm_password, gender):
        # A validação de password == confirm_password deve ocorrer antes de chamar insert_user
        self.created = self.__users.book(fullname, username, birthdate, email, password, gender) # Removi confirm_password daqui, não é salvo
        self.update_account_list()
        # Redirecionar para o portal após o cadastro é OK
        return redirect('/portal')

    def update_user(self, username, password):
        self.edited = self.__users.setUser(username, password)
        redirect('/portal')

    def logout_user(self):
        session_id = request.get_cookie('session_id')
        if session_id: # Garante que há uma sessão para deslogar
            self.__users.logout(session_id)
            response.delete_cookie('session_id', path='/') # Assegura que o path do cookie é o mesmo da criação
            self.update_users_list()
            print(f"DEBUG: Cookie de sessão {session_id} removido e usuário deslogado.")


    def chat(self): # Este método de chat GET pode ser descontinuado se o chat for apenas na homepage
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            # Se for um chat geral, mantém. Se for de casa, precisa de house_id
            messages = self.__messages.getUsersMessages() # Ou getHouseMessages(house_id)
            auth_users= self.__users.getAuthenticatedUsers().values()
            return template('app/views/html/chat', current_user=current_user, \
            messages=messages, auth_users=auth_users)
        redirect('/portal')

    def newMessage(self, username, content, house_id): # Adicionado house_id
        try:
            return self.__messages.book(username, content, house_id) # Passa house_id para o book
        except UnicodeEncodeError as e:
            print(f"Encoding error: {e}")
            return None # Retorna None em caso de erro


    # Websocket:
    def setup_websocket_events(self):

        @self.sio.event
        async def connect(sid, environ):
            print(f'Client connected: {sid}')
            # Quando um cliente conecta, ele pode se juntar a uma sala (house_id)
            # A house_id pode vir de um cookie ou de um evento `join_room` do cliente
            # Por agora, faremos com que o cliente envie a house_id via um evento 'join'
            # self.sio.emit('connected', {'data': 'Connected'}, room=sid)

        @self.sio.event
        async def disconnect(sid):
            print(f'Client disconnected: {sid}')
            # Remover o sid da sala que ele estava, se você estiver controlando salas no servidor

        @self.sio.event
        def join_house_room(sid, data):
            """
            Evento para um cliente se juntar à sala de chat de uma casa específica.
            O cliente deve enviar {'house_id': 'ID_DA_CASA'}.
            """
            house_id = data.get('house_id')
            if house_id:
                self.sio.enter_room(sid, house_id)
                print(f"Client {sid} joined room {house_id}")
                # Opcional: Enviar mensagens antigas da casa para o novo membro
                # current_user = self.getCurrentUserBySessionId() # Não é fácil obter o user aqui no connect
                # house_messages = self.__messages.getHouseMessages(house_id)
                # self.sio.emit('old_messages', {'messages': [msg.to_dict() for msg in house_messages]}, room=sid)


        # Recebimento de solicitação de cliente para envio de mensagem
        @self.sio.event
        def send_house_message(sid, data): # Renomeado para clareza
            message_content = data.get('content')
            house_id = data.get('house_id') # Espera-se que o cliente envie a house_id
            username = data.get('username') # Espera-se que o cliente envie o username (ou você pode buscar pelo sid)

            if not message_content or not house_id or not username:
                print("Dados de mensagem incompletos recebidos via WebSocket.")
                return

            # Cria e salva a nova mensagem
            new_message_obj = self.newMessage(username, message_content, house_id)

            if new_message_obj:
                # Emite a mensagem para todos os clientes na sala (house_id)
                # Garanta que o objeto enviado seja serializável (use to_dict)
                self.sio.emit('new_house_message', new_message_obj.to_dict(), room=house_id)
                print(f"Mensagem de '{username}' na casa '{house_id}' enviada: '{message_content}'")
            else:
                print(f"Falha ao processar e emitir mensagem: {message_content}")


        # solicitação para atualização da lista de usuários conectados. Quem faz
        # esta solicitação é o próprio controlador. Ver update_users_list()
        @self.sio.event
        def update_users_event(sid, data):
            self.sio.emit('update_users_event', {'content': data})

        # solicitação para atualização da lista de usuários conectados. Quem faz
        # esta solicitação é o próprio controlador. Ver update_account_event()
        @self.sio.event
        def update_account_event(sid, data):
            self.sio.emit('update_account_event', {'content': data})


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