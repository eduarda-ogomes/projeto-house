from app.controllers.datarecord import UserRecord, MessageRecord, HouseRecord
from bottle import template, redirect, request, response, Bottle, static_file, HTTPError, post
import socketio
import datetime
from datetime import date, timedelta

import eventlet
eventlet.monkey_patch() 

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
        self.created = None

        self.app = Bottle()
        self.setup_routes()

        self.sio = socketio.Server(async_mode='eventlet', cors_allowed_origins="*")
        self.setup_websocket_events()

        self.wsgi_app = socketio.WSGIApp(self.sio, self.app)

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
            
            required_fields = {
                'fullname': fullname,
                'username': username,
                'birthdate': birthdate,
                'email': email,
                'password': password,
                'confirm_password': confirm_password,
                'gender': gender
            }

            missing_fields = [field_name for field_name, value in required_fields.items() if not value or value.strip() == '']
            
            if missing_fields:
                print(f"Campos obrigatórios faltando ou vazios: {', '.join(missing_fields)}")
                return template(
                    'app/views/html/cadastro', 
                    error=f"Por favor, preencha todos os campos obrigatórios. Campos faltando: {', '.join(missing_fields).replace('_', ' ').title()}.",
                    # Opcional: passa de volta os dados que foram preenchidos (exceto senha)
                    # Para preencher o formulário novamente com os dados válidos
                    fullname=fullname, username=username, birthdate=birthdate, 
                    email=email, gender=gender
                )

            # --- VALIDAÇÃO DE SENHAS ---
            if password != confirm_password:
                print("Senhas não coincidem.")
                return template(
                    'app/views/html/cadastro', 
                    error="As senhas não coincidem. Por favor, digite-as novamente.",
                    fullname=fullname, username=username, birthdate=birthdate, 
                    email=email, gender=gender
                )
            
            if len(password) < 6:
                print("Senha muito curta.")
                return template(
                    'app/views/html/cadastro', 
                    error="A senha deve ter no mínimo 6 caracteres.",
                    fullname=fullname, username=username, birthdate=birthdate, 
                    email=email, gender=gender
                )

            # --- VALIDAÇÃO DE FORMATO DE E-MAIL (Exemplo) ---
            if '@' not in email or '.' not in email:
                print("Formato de e-mail inválido.")
                return template(
                    'app/views/html/cadastro', 
                    error="Por favor, insira um endereço de e-mail válido.",
                    fullname=fullname, username=username, birthdate=birthdate, 
                    email=email, gender=gender
                )

            # --- Continua com o processamento se todas as validações passarem ---
            fullname = fullname.title() # Aplica a formatação de título

            self.insert_user(fullname, username, birthdate, email, password, gender)
            # Redireciona para o portal após o cadastro bem-sucedido
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

                for chore in house.chores:
                    rotation_days = chore.get('rotation_days')
                    next_due_str = chore.get('next_due')
                    last_completed_date_str = chore.get('last_completed_date')

                    if (rotation_days is not None and rotation_days > 0 and
                        next_due_str):

                        try:
                            next_due_date = datetime.datetime.strptime(next_due_str, '%Y-%m-%d').date()
                            today = date.today()

                            if next_due_date <= today:
                                current_assignee = chore.get('assigned_to')
                                if current_assignee in members:
                                    current_index = members.index(current_assignee)
                                    next_index = (current_index + 1) % len(members)
                                    next_assignee = members[next_index]
                                else:
                                    next_assignee = members[0] if members else None

                                if next_assignee:
                                    chore['assigned_to'] = next_assignee
                                    chore['next_due'] = (next_due_date + timedelta(days=rotation_days)).strftime('%Y-%m-%d')

                                    if last_completed_date_str:
                                        chore['last_completed_date'] = None
                                        chore['last_completed_by'] = None
                                    
                                    self.__houses.save()
                                else:
                                    print(f"AVISO: Tarefa '{chore.get('activity', 'N/A')}' não rotacionada, sem próximos membros.")

                        except (ValueError, KeyError) as e:
                            print(f"Erro ao processar rotação da tarefa '{chore.get('activity', 'N/A')}': {e}")

                my_chores = []
                other_chores = []
                for chore in house.chores:
                    if chore.get('assigned_to') == current_user.username:
                        my_chores.append(chore)
                    else:
                        other_chores.append(chore)
                
                house_messages = self.__messages.getHouseMessages(house.id)

                return template(
                    'app/views/html/homepage_in_house',
                    user=current_user,
                    house=house,
                    my_chores=my_chores,
                    other_chores=other_chores,
                    messages=house_messages,
                    datetime=datetime
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
            if not house_name or house_name.strip() == '':
                return redirect('/homepage')
            for house_obj in self.__houses.houses.values():
                if house_obj.name.lower() == house_name.strip().lower():
                    print(f"AVISO: Tentativa de criar casa com nome duplicado: '{house_name}'")
                    return redirect('/homepage') 

            house_id = self.__houses.create_house(house_name.strip(), current_user.username)
            if house_id:
                print(f"Casa '{house_name}' criada com ID: {house_id} por {current_user.username}")
                return redirect('/homepage')
            else:
                print(f"ERRO: Falha ao criar a casa '{house_name}'.")
                return redirect('/homepage')


        @self.app.route('/join_house', method='POST')
        def join_house():
            current_user = self.getCurrentUserBySessionId()
            if not current_user:
                return redirect('/portal') 

            house_name_to_join = request.forms.get('house_name') 
            print(f"Tentativa de entrar na casa: '{house_name_to_join}' pelo usuário: '{current_user.username}'")

            if not house_name_to_join or house_name_to_join.strip() == '':
                print("ERRO: Nome da casa para entrar está vazio.")
            target_house = None
            for house_obj in self.__houses.houses.values(): 
                if house_obj.name.lower() == house_name_to_join.strip().lower(): 
                    target_house = house_obj
                    break 
            
            if not target_house:
                print(f"ERRO: Casa '{house_name_to_join}' não encontrada.")
                return redirect('/homepage')
            
            if current_user.username in target_house.members:
                print(f"AVISO: Usuário '{current_user.username}' já é membro da casa '{target_house.name}'.")
                return redirect('/homepage') 
            target_house.add_member(current_user.username) 
            self.__houses.save()
            print(f"Usuário '{current_user.username}' adicionado à casa '{target_house.name}' com sucesso!")
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
                    return redirect('/homepage')

                if not self.__users.user_exists(new_member_username):
                    print(f"AVISO: Usuário '{new_member_username}' não existe no sistema.")
                    return template('app/views/html/homepage_in_house',
                                    user=current_user,
                                    house=house,
                                    my_chores=[],
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

            house.add_chore(
                activity=activity,
                date_str=date_str,
                rotation_days=rotation_days,
                next_due=date_str
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
                return redirect('/portal')

            fullname = request.forms.get('fullname').strip()
            email = request.forms.get('email').strip()
            birthdate = request.forms.get('birthdate').strip()
            gender = request.forms.get('gender').strip()
            new_password = request.forms.get('password')
            confirm_password = request.forms.get('confirm_password')

            if not fullname or not email or not birthdate or not gender:
                return template('profile', user=current_user, error="Todos os campos obrigatórios devem ser preenchidos.")

            if '@' not in email or '.' not in email:
                return template('profile', user=current_user, error="Formato de email inválido.")

            if new_password:
                if new_password != confirm_password:
                    return template('profile', user=current_user, error="As novas senhas não coincidem.")
                if len(new_password) < 6:
                    return template('profile', user=current_user, error="A nova senha deve ter no mínimo 6 caracteres.")

                self.__users.setUser(current_user.username, new_password)

            try:
                current_user.fullname = fullname
                current_user.email = email
                current_user.birthdate = birthdate
                current_user.gender = gender
                self.__users.updateUser(current_user)
                return template('profile', user=current_user, message="Perfil atualizado com sucesso!")

            except Exception as e:
                print(f"Erro ao atualizar perfil: {e}")
                return template('profile', user=current_user, error="Ocorreu um erro ao atualizar o perfil.")

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
                response.set_cookie('session_id', session_id, httponly=True, secure=False, max_age=3600, path='/')
                return redirect('/homepage')
            return redirect('/portal')

    def delete_user(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            self.logout_user()
            self.removed = self.__users.removeUser(current_user)
            self.update_account_list()
            print(f'Valor de retorno de self.removed: {self.removed}')
        return redirect('/portal')

    def insert_user(self, fullname,username,birthdate, email, password, gender):
        self.created = self.__users.book(fullname, username, birthdate, email, password, gender)
        self.update_account_list()
        return redirect('/portal')

    def update_user(self, username, password):
        self.edited = self.__users.setUser(username, password)
        redirect('/portal')

    def logout_user(self):
        session_id = request.get_cookie('session_id')
        if session_id:
            self.__users.logout(session_id)
            response.delete_cookie('session_id', path='/')
            self.update_users_list()
            print(f"DEBUG: Cookie de sessão {session_id} removido e usuário deslogado.")

    def chat(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            messages = self.__messages.getUsersMessages()
            auth_users= self.__users.getAuthenticatedUsers().values()
            return template('app/views/html/chat', current_user=current_user, \
            messages=messages, auth_users=auth_users)
        redirect('/portal')

    def newMessage(self, username, content, house_id):
        try:
            return self.__messages.book(username, content, house_id)
        except UnicodeEncodeError as e:
            print(f"Encoding error: {e}")
            return None

    def setup_websocket_events(self):

        @self.sio.event
        async def connect(sid, environ):
            print(f'Client connected: {sid}')

        @self.sio.event
        async def disconnect(sid):
            print(f'Client disconnected: {sid}')

        @self.sio.event
        def join_house_room(sid, data):
            house_id = data.get('house_id')
            if house_id:
                self.sio.enter_room(sid, house_id)
                print(f"Client {sid} joined room {house_id}")

        @self.sio.event
        def send_house_message(sid, data):
            message_content = data.get('content')
            house_id = data.get('house_id')
            username = data.get('username')

            if not message_content or not house_id or not username:
                print("Dados de mensagem incompletos recebidos via WebSocket.")
                return

            new_message_obj = self.newMessage(username, message_content, house_id)

            if new_message_obj:
                self.sio.emit('new_house_message', new_message_obj.to_dict(), room=house_id)
                print(f"Mensagem de '{username}' na casa '{house_id}' enviada: '{message_content}'")
            else:
                print(f"Falha ao processar e emitir mensagem: {message_content}")

        @self.sio.event
        def update_users_event(sid, data):
            self.sio.emit('update_users_event', {'content': data})

        @self.sio.event
        def update_account_event(sid, data):
            self.sio.emit('update_account_event', {'content': data})

    def update_users_list(self):
        print('Atualizando a lista de usuários conectados...')
        users = self.__users.getAuthenticatedUsers()
        users_list = [{'username': user.username} for user in users.values()]
        self.sio.emit('update_users_event', {'users': users_list})

    def update_account_list(self):
        print('Atualizando a lista de usuários cadastrados...')
        users = self.__users.getUserAccounts()
        users_list = [{'username': user.username} for user in users]
        self.sio.emit('update_account_event', {'accounts': users_list})