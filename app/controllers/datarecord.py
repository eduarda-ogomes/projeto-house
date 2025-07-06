# datarecord.py
from app.models.user_account import UserAccount, SuperAccount
from app.models.user_message import UserMessage # Certifique-se de que este caminho está correto
from app.models.house import House
import json
import uuid
import datetime # Adicionado para o timestamp das mensagens

class MessageRecord():
    """Banco de dados JSON para o recurso: Mensagem"""

    def __init__(self):
        self.__user_messages = []
        self.read()

    def read(self):
        try:
            with open("app/controllers/db/user_messages.json", "r") as fjson:
                user_msg_data = json.load(fjson)
                # Garante que cada mensagem lida do JSON tenha um house_id
                # e um timestamp, se não existirem (para compatibilidade com dados antigos)
                self.__user_messages = [
                    UserMessage(
                        username=msg.get('username'),
                        content=msg.get('content'),
                        house_id=msg.get('house_id', 'general'), # Valor padrão 'general' para mensagens sem casa
                        timestamp=msg.get('timestamp')
                    ) for msg in user_msg_data
                ]
        except FileNotFoundError:
            print('Não existem mensagens registradas!')
        except json.JSONDecodeError: # Adiciona tratamento para JSON inválido
            print('Erro ao decodificar JSON de mensagens. Iniciando com lista vazia.')
            self.__user_messages = []


    def __write(self):
        try:
            with open("app/controllers/db/user_messages.json", "w") as fjson:
                # Usa o método to_dict() do UserMessage para garantir o formato correto
                user_msg_serializable = [msg.to_dict() for msg in self.__user_messages]
                json.dump(user_msg_serializable, fjson, indent=4) # Adicionado indent para legibilidade
                print(f'Arquivo gravado com sucesso (Mensagem)!')
        except FileNotFoundError:
            print('O sistema não conseguiu gravar o arquivo (Mensagem)!')


    def book(self, username, content, house_id): # Adicionado house_id
        new_msg = UserMessage(username, content, house_id) # Passa house_id para o construtor
        self.__user_messages.append(new_msg)
        self.__write()
        return new_msg


    def getUsersMessages(self): # Manter se ainda houver um chat "geral"
        return self.__user_messages

    def getHouseMessages(self, house_id): # Novo método para obter mensagens de uma casa específica
        return [msg for msg in self.__user_messages if msg.house_id == house_id]

# ------------------------------------------------------------------------------

class UserRecord():
    """Banco de dados JSON para o recurso: Usuário"""

    def __init__(self):
        self.__allusers= {'user_accounts': [], 'super_accounts': []}
        self.__authenticated_users = {}
        self.read('user_accounts')
        self.read('super_accounts')

    def read(self, database):
        account_class = SuperAccount if (database == 'super_accounts') else UserAccount
        try:
            with open(f"app/controllers/db/{database}.json", "r") as fjson:
                user_d = json.load(fjson)
                self.__allusers[database] = [
                    account_class(
                        fullname=data.get('fullname', 'Nome Desconhecido'),  # Valor padrão
                        username=data.get('username', 'Usuário Desconhecido'),  # Valor padrão
                        birthdate=data.get('birthdate', 'Data Desconhecida'),  # Valor padrão
                        email=data.get('email', 'Email Desconhecido'),  # Valor padrão
                        password=data.get('password', 'Senha Desconhecida'),  # Valor padrão
                        gender=data.get('gender', 'Gênero Desconhecido'),  # Valor padrão
                        permissions=data.get('permissions', None)  # Para SuperAccount
                    ) for data in user_d
                ]
        except FileNotFoundError:
            self.__allusers[database].append(account_class('Guest', '000000', '', '', '', '', ''))


    def __write(self,database):
        try:
            with open(f"app/controllers/db/{database}.json", "w") as fjson:
                user_data = [vars(user_account) for user_account in \
                self.__allusers[database]]
                json.dump(user_data, fjson, indent=4) # Adicionado indent para legibilidade
                print(f'Arquivo gravado com sucesso (Usuário)!')
        except FileNotFoundError:
            print('O sistema não conseguiu gravar o arquivo (Usuário)!')



    def setUser(self,username,password):
        for account_type in ['user_accounts', 'super_accounts']:
            for user in self.__allusers[account_type]:
                if username == user.username:
                    user.password= password
                    print(f'O usuário {username} foi editado com sucesso.')
                    self.__write(account_type)
                    return username
        print('O método setUser foi chamado, porém sem sucesso.')
        return None


    def removeUser(self, user):
        for account_type in ['user_accounts', 'super_accounts']:
            if user in self.__allusers[account_type]:
                print(f'O usuário {"(super) " if account_type == "super_accounts" else ""}{user.username} foi encontrado no cadastro.')
                self.__allusers[account_type].remove(user)
                print(f'O usuário {"(super) " if account_type == "super_accounts" else ""}{user.username} foi removido do cadastro.')
                self.__write(account_type)
                return user.username
        print(f'O usuário {user.username} não foi identificado!')
        return None


    def book(self, fullname, username, birthdate, email, password, confirm_password, gender, permissions=None): # permissions é opcional no cadastro
        account_type = 'super_accounts' if permissions else 'user_accounts'
        account_class = SuperAccount if permissions else UserAccount
        # O construtor UserAccount não aceita permissions, então passamos apenas se for SuperAccount
        if permissions:
            new_user = account_class(fullname, username, birthdate, email, password, gender, permissions)
        else:
            new_user = account_class(fullname, username, birthdate, email, password, gender)
        
        self.__allusers[account_type].append(new_user)
        self.__write(account_type)
        return new_user.username


    def getUserAccounts(self):
        # Combina e retorna todos os usuários (normais e super)
        return self.__allusers['user_accounts'] + self.__allusers['super_accounts']


    def getCurrentUser(self,session_id):
        if session_id in self.__authenticated_users:
            return self.__authenticated_users[session_id]
        else:
            return None


    def getAuthenticatedUsers(self):
        return self.__authenticated_users


    def checkUser(self, username, password):
        for account_type in ['user_accounts', 'super_accounts']:
            for user in self.__allusers[account_type]:
                if user.username == username and user.password == password:
                    session_id = str(uuid.uuid4())  # Gera um ID de sessão único
                    self.__authenticated_users[session_id] = user
                    return session_id  # Retorna o ID de sessão para o usuário
        return None
    
    def updateUser(self, updated_user_obj):
        """
        Atualiza as informações de um usuário existente (exceto a senha, que pode ter um método separado).
        Assume que updated_user_obj é uma instância de UserAccount ou SuperAccount
        com as informações mais recentes.
        """
        found = False
        for account_type in ['user_accounts', 'super_accounts']:
            for i, user in enumerate(self.__allusers[account_type]):
                if user.username == updated_user_obj.username:
                    # Atualiza os atributos do usuário existente no registro
                    self.__allusers[account_type][i].fullname = updated_user_obj.fullname
                    self.__allusers[account_type][i].birthdate = updated_user_obj.birthdate
                    self.__allusers[account_type][i].email = updated_user_obj.email
                    self.__allusers[account_type][i].gender = updated_user_obj.gender
                    # A senha é atualizada por setUser, não aqui, a menos que você queira consolidar.
                    
                    self.__write(account_type) # Salva o tipo de conta modificado
                    print(f"Usuário {updated_user_obj.username} atualizado com sucesso em {account_type}.")
                    found = True
                    break
            if found:
                break
        
        if not found:
            print(f"Erro: Usuário {updated_user_obj.username} não encontrado para atualização.")
            return False
        return True

    # --- Ajuste opcional no setUser para clareza (já existente, só para referência) ---
    def setUser(self, username, password):
        """Edita a senha de um usuário existente."""
        for account_type in ['user_accounts', 'super_accounts']:
            for user in self.__allusers[account_type]:
                if username == user.username:
                    user.password = password
                    print(f'O usuário {username} teve a senha editada com sucesso.')
                    self.__write(account_type) # Salva a alteração da senha
                    return username
        print('O método setUser foi chamado, porém sem sucesso.')
        return None


    def logout(self, session_id):
        if session_id in self.__authenticated_users:
            del self.__authenticated_users[session_id] # Remove o usuário logado

    def user_exists(self, username):
        """Verifica se um usuário com o dado username já existe no sistema."""
        for account_type in ['user_accounts', 'super_accounts']:
            for user in self.__allusers[account_type]:
                if user.username == username:
                    return True
        return False


class HouseRecord:
    """Gerencia as casas (ambientes) e suas associações com usuários"""

    def __init__(self):
        self.houses = {}
        self.load()

    def load(self):
        try:
            with open('app/controllers/db/houses.json', 'r') as f:
                houses_data = json.load(f)
                self.houses = {
                    house_id: House(
                        house_id=house_id,
                        name=house['name'],
                        members=house.get('members', []),
                        chores=house.get('chores', []), # Carrega dicionários diretamente
                        last_member=house.get('last_member',0)
                    )
                    for house_id, house in houses_data.items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            self.houses = {}

    def save(self):
        with open('app/controllers/db/houses.json', 'w') as f:
            houses_data = {
                house_id: {
                    'name': house.name,
                    'members': house.members,
                    'chores': house.chores, # Salva dicionários diretamente
                    'last_member': house.last_member
                }
                for house_id, house in self.houses.items()
            }
            json.dump(houses_data, f, indent=4)


    def create_house(self, name, owner_username):
        house_id = str(uuid.uuid4())
        new_house = House(house_id=house_id, name=name, members=[owner_username])
        self.houses[house_id] = new_house
        self.save()
        return house_id
    
    def get_house_by_user(self, username):
        for house_id, house in self.houses.items():
            if username in house.members:
                return house
        return None


    def house_exists(self, house_id):
        return house_id in self.houses

    def list_houses(self):
        """Retorna lista de casas com id e nome, para escolha do usuário"""
        return [{'id': house_id, 'name': house.name} for house_id, house in self.houses.items()]

