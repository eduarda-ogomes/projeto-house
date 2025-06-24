from app.models.user_account import UserAccount, SuperAccount
from app.models.chore import Chore
from app.models.user_message import UserMessage
from app.models.house import House
import json
import uuid


class MessageRecord():
    """Banco de dados JSON para o recurso: Mensagem"""

    def __init__(self):
        self.__user_messages= []
        self.read()

    def read(self):
        try:
            with open("app/controllers/db/user_messages.json", "r") as fjson:
                user_msg = json.load(fjson)
                self.__user_messages = [UserMessage(**msg) for msg in user_msg]
        except FileNotFoundError:
            print('Não existem mensagens registradas!')


    def __write(self):
        try:
            with open("app/controllers/db/user_messages.json", "w") as fjson:
                user_msg = [vars(user_msg) for user_msg in \
                self.__user_messages]
                json.dump(user_msg, fjson)
                print(f'Arquivo gravado com sucesso (Mensagem)!')
        except FileNotFoundError:
            print('O sistema não conseguiu gravar o arquivo (Mensagem)!')


    def book(self,username,content):
        new_msg= UserMessage(username,content)
        self.__user_messages.append(new_msg)
        self.__write()
        return new_msg


    def getUsersMessages(self):
        return self.__user_messages


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
                json.dump(user_data, fjson)
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


    def book(self, fullname, username, birthdate, email, password, confirm_password, gender, permissions):
        account_type = 'super_accounts' if permissions else 'user_accounts'
        account_class = SuperAccount if permissions else UserAccount
        new_user = account_class(fullname, username, birthdate, email, password, gender, permissions) if permissions else account_class(fullname, username, birthdate, email, password, gender)
        self.__allusers[account_type].append(new_user)
        self.__write(account_type)
        return new_user.username


    def getUserAccounts(self):
        return self.__allusers['user_accounts']


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


    def logout(self, session_id):
        if session_id in self.__authenticated_users:
            del self.__authenticated_users[session_id] # Remove o usuário logado


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
                        members=house.get('members', [])
                    )
                    for house_id, house in houses_data.items()  # Corrigido para usar house_id e house
                }
        except (FileNotFoundError, json.JSONDecodeError):
            self.houses = {}

    def save(self):
        with open('app/controllers/db/houses.json', 'w') as f:
            houses_data = {
                house_id: {
                    'name': house.name,
                    'members': house.members
                }
                for house_id, house in self.houses.items()  # Corrigido para usar house_id e house
            }
            json.dump(houses_data, f, indent=4)

    def create_house(self, name, owner_username):
        house_id = str(uuid.uuid4())
        new_house = House(house_id=house_id, name=name, members=[owner_username])
        self.houses[house_id] = new_house
        self.save()
        return house_id

    def add_user_to_house(self, house_id, username):
        if house_id in self.houses:
            house = self.houses[house_id]
            if username not in house.members:
                house.add_member(username)
                self.save()
                return True
        return False

    def get_house_by_user(self, username):
        for house_id, house in self.houses.items():
            if username in house.members:
                return house  # Retorna o objeto House
        return None


    def house_exists(self, house_id):
        return house_id in self.houses

    def list_houses(self):
        """Retorna lista de casas com id e nome, para escolha do usuário"""
        return [{'id': house_id, 'name': house.name} for house_id, house in self.houses.items()]
# First, let's update the ChoreRecord class to match your model
class ChoreRecord:
    """Manages chores and their associations with houses and users"""

    def __init__(self):
        self.chores = {}
        self.load()

    def load(self):
        try:
            with open('app/controllers/db/chores.json', 'r') as f:
                chores_data = json.load(f)
                self.chores = {
                    chore_id: Chore(
                        activity=chore['activity'],
                        date=chore['date'],
                        status=chore['status'],
                        responsable=UserAccount(
                            username=chore['responsable'],
                            # Add other required UserAccount fields if needed
                        )
                    )
                    for chore_id, chore in chores_data.items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            self.chores = {}

    def save(self):
        with open('app/controllers/db/chores.json', 'w') as f:
            chores_data = {
                chore_id: {
                    'activity': chore.activity,
                    'date': chore.date,
                    'status': chore.status,
                }
                for chore_id, chore in self.chores.items()
            }
            json.dump(chores_data, f, indent=4)

    def create_chore(self, activity, date, status='pending'):
        chore_id = str(uuid.uuid4())
        new_chore = Chore(
            activity=activity,
            date=date,
            status=status,
        )
        self.chores[chore_id] = new_chore
        self.save()
        return chore_id

    def get_chores_by_house(self, house_id):
        # If you want to track chores per house, add house_id to Chore model
        return [chore for chore in self.chores.values()]

    def get_chores_by_user(self, username):
        return [
            {'id': cid, 'activity': chore.activity, 'date': chore.date, 'status': chore.status}
            for cid, chore in self.chores.items() 
            if chore.responsable == username
        ]
