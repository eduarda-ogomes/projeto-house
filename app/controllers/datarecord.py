import json
import uuid
import os # Importar para verificar existência de arquivos/diretórios

# Suas importações originais, sem modificações de caminho
from app.models.user_account import UserAccount, SuperAccount # Adicionado SuperAccount para completude
from app.models.user_message import UserMessage
from app.models.house import House # Mantido "House" como você tinha

import bcrypt # Adicionado para hashing de senhas, crucial para segurança

# Seus caminhos de arquivo originais
# Certifique-se de que o diretório 'app/controllers/db/' exista
USER_ACCOUNTS_FILE = "app/controllers/db/user_accounts.json"
MESSAGES_FILE = "app/controllers/db/user_messages.json"
HOUSES_FILE = "app/controllers/db/houses.json"

# --- Funções Auxiliares para Leitura/Escrita de JSON (Adaptadas) ---
# Estas funções ajudam a centralizar a lógica de arquivo para evitar repetição.

def _load_json_data(filepath, default_type):
    """
    Carrega dados de um arquivo JSON. Se o arquivo não existir ou estiver corrompido,
    retorna um valor padrão e tenta criar um arquivo vazio.
    """
    if not os.path.exists(filepath):
        print(f"Arquivo '{filepath}' não encontrado. Criando um novo.")
        _write_json_data(filepath, default_type()) # Cria o arquivo
        return default_type()
    
    try:
        with open(filepath, "r", encoding='utf-8') as f:
            content = f.read().strip()
            if not content: # Arquivo está vazio
                print(f"Arquivo '{filepath}' está vazio. Iniciando com {default_type.__name__} vazio.")
                return default_type()
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON de '{filepath}': {e}. Iniciando com {default_type.__name__} vazio.")
        # Opcional: Você pode querer renomear o arquivo corrompido aqui para backup
        return default_type()
    except Exception as e:
        print(f"Erro ao ler arquivo '{filepath}': {e}. Iniciando com {default_type.__name__} vazio.")
        return default_type()

def _write_json_data(filepath, data):
    """
    Escreve dados em um arquivo JSON. Garante que o diretório exista.
    """
    try:
        # Garante que o diretório 'app/controllers/db/' exista
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        # print(f"Dados salvos com sucesso em '{filepath}'") # Comentado para menos logs
    except Exception as e:
        print(f"Erro ao escrever dados em '{filepath}': {e}")


# --- Classes Record ---

class MessageRecord:
    """Banco de dados JSON para o recurso: Mensagem"""

    def __init__(self):
        self.__user_messages = []
        self.read()

    def read(self):
        user_msg_data = _load_json_data(MESSAGES_FILE, list)
        self.__user_messages = [
            UserMessage(
                username=msg.get('username'),
                content=msg.get('content'),
                house_id=msg.get('house_id'), # 'house_id' é carregado do JSON
                timestamp=msg.get('timestamp')
            ) for msg in user_msg_data
        ]

    def __write(self):
        user_msg_serializable = [msg.to_dict() for msg in self.__user_messages]
        _write_json_data(MESSAGES_FILE, user_msg_serializable)
        print(f'Arquivo de Mensagens gravado com sucesso!')

    def book(self, username, content, house_id):
        # O UserMessage agora espera house_id
        new_msg = UserMessage(username, content, house_id)
        self.__user_messages.append(new_msg)
        self.__write()
        return new_msg # Retorna o objeto completo para ser usado no Socket.IO

    def getUsersMessages(self):
        return self.__user_messages

    def getHouseMessages(self, house_id):
        return [msg for msg in self.__user_messages if msg.house_id == house_id]


class UserRecord:
    """Banco de dados JSON para o recurso: Usuário"""

    def __init__(self):
        self.__all_users = {} 
        self.__authenticated_users = {}
        self.read_all_users()

    def read_all_users(self):
        user_data_dict = _load_json_data(USER_ACCOUNTS_FILE, dict)
        self.__all_users = {} 

        for username_key, data in user_data_dict.items():
            # Tenta pegar 'password_hash'. Se não existir, tenta 'password' (para compatibilidade)
            password_value = data.get('password_hash')
            if password_value is None:
                password_value = data.get('password') # Se 'password_hash' não existir, tenta 'password' original

            session_id_value = data.get('session_id') # Carrega session_id, pode ser None

            # Decide se é UserAccount ou SuperAccount baseado no username ou outra propriedade
            # 'admin' é um exemplo, você pode ter uma flag 'isAdmin' no JSON
            if username_key == 'admin' or data.get('isAdmin', False): 
                user_obj = SuperAccount(
                    fullname=data.get('fullname', 'Admin Default'),
                    username=data.get('username', username_key),
                    birthdate=data.get('birthdate', '2000-01-01'),
                    email=data.get('email', 'admin@example.com'),
                    password_hash=password_value, 
                    gender=data.get('gender', 'Outro'),
                    permissions=data.get('permissions', ['admin']),
                    session_id=session_id_value
                )
            else:
                user_obj = UserAccount(
                    fullname=data.get('fullname', 'Nome Desconhecido'),
                    username=data.get('username', username_key),
                    birthdate=data.get('birthdate', 'Data Desconhecida'),
                    email=data.get('email', 'Email Desconhecido'),
                    password_hash=password_value, 
                    gender=data.get('gender', 'Gênero Desconhecido'),
                    permissions=data.get('permissions', []),
                    session_id=session_id_value
                )
            self.__all_users[username_key] = user_obj
            
            # Se o usuário tiver um session_id salvo (e válido), considere-o autenticado
            if session_id_value: # Você pode adicionar uma validação de tempo/expiração aqui
                self.__authenticated_users[session_id_value] = user_obj

        # Adiciona um usuário padrão 'guest' se o sistema estiver vazio após carregar
        if not self.__all_users:
            guest_user = UserAccount('Guest User', 'guest', '2000-01-01', 'guest@example.com', self._hash_password('000000'), 'Outro', permissions=['guest'])
            self.__all_users[guest_user.username] = guest_user
            self.__write_all_users() # Salva o usuário guest no arquivo

    def __write_all_users(self):
        user_serializable_data = {
            username: user_account.to_dict() 
            for username, user_account in self.__all_users.items()
        }
        _write_json_data(USER_ACCOUNTS_FILE, user_serializable_data)
        print(f'Arquivo de Usuários gravado com sucesso!')

    def _hash_password(self, password):
        """Hasheia uma senha usando bcrypt."""
        # bcrypt.gensalt() gera um salt único para cada hash, tornando-o mais seguro.
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _check_password(self, password, stored_hash):
        """
        Verifica se uma senha fornecida corresponde ao hash armazenado.
        Inclui lógica de compatibilidade para senhas não hasheadas antigas.
        """
        if not stored_hash: # Se não há hash armazenado (usuário sem senha ou problema)
            return False
        
        try:
            # Tenta verificar como um hash bcrypt
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except ValueError:
            # Se ValueError, stored_hash não é um hash bcrypt válido.
            # Pode ser uma senha em texto puro de uma versão antiga.
            # ESTE BLOCO DEVE SER REMOVIDO APÓS A MIGRAÇÃO DE TODAS AS SENHAS.
            print("AVISO: Hash inválido encontrado (provavelmente senha antiga não hasheada). Comparando como texto puro.")
            return password == stored_hash # Apenas para compatibilidade de migração

    def book(self, fullname, username, birthdate, email, password, gender, permissions=None):
        """
        Registra um novo usuário. A senha é hasheada antes de ser armazenada.
        """
        if username in self.__all_users:
            print(f"Erro: O usuário com username '{username}' já existe.")
            return False
            
        hashed_password = self._hash_password(password)
        
        new_user = UserAccount(fullname, username, birthdate, email, hashed_password, gender, permissions)
        
        self.__all_users[new_user.username] = new_user 
        self.__write_all_users()
        print(f"Usuário '{new_user.username}' cadastrado com sucesso.")
        return True

    def setUser(self, username, new_password):
        """
        Edita a senha de um usuário existente. A nova senha é hasheada.
        """
        user = self.__all_users.get(username)
        if user:
            user.password_hash = self._hash_password(new_password)
            print(f'A senha do usuário {username} foi editada com sucesso.')
            self.__write_all_users()
            return username
        print('O método setUser foi chamado, porém sem sucesso (usuário não encontrado).')
        return None

    def removeUser(self, user_to_remove):
        """Remove um usuário do registro e de sessões ativas, se aplicável."""
        if user_to_remove.username in self.__all_users:
            # Se o usuário estiver autenticado, o desloga primeiro
            if user_to_remove.session_id and user_to_remove.session_id in self.__authenticated_users:
                del self.__authenticated_users[user_to_remove.session_id]
                print(f"Sessão {user_to_remove.session_id} do usuário '{user_to_remove.username}' encerrada.")
            
            del self.__all_users[user_to_remove.username]
            self.__write_all_users()
            print(f'O usuário {user_to_remove.username} foi removido do cadastro.')
            return user_to_remove.username
        print(f'O usuário {user_to_remove.username} não foi identificado para remoção!')
        return None

    def getUserAccounts(self):
        """Retorna a lista de todos os objetos UserAccount cadastrados."""
        return list(self.__all_users.values())

    def getCurrentUser(self, session_id):
        """Retorna o objeto UserAccount associado a um session_id."""
        return self.__authenticated_users.get(session_id)

    def getAuthenticatedUsers(self):
        """Retorna o dicionário de usuários autenticados (session_id -> UserAccount)."""
        return self.__authenticated_users

    def checkUser(self, username, password):
        """
        Verifica credenciais e autentica o usuário, retornando um novo session_id.
        Persiste o session_id no objeto UserAccount e no arquivo JSON.
        """
        user = self.__all_users.get(username)
        if user and self._check_password(password, user.password_hash):
            session_id = str(uuid.uuid4()) # Gera um novo UUID para a sessão
            user.session_id = session_id # Atribui o session_id ao objeto UserAccount
            self.__authenticated_users[session_id] = user
            self.__write_all_users() # Salva o session_id no arquivo JSON
            print(f"Usuário '{username}' autenticado. Session ID: {session_id}")
            return session_id
        print(f"Falha na autenticação para usuário '{username}'.")
        return None
    
    def updateUser(self, updated_user_obj):
        """
        Atualiza as informações de um usuário existente com base no objeto 'updated_user_obj'.
        Não altera a senha (use setUser para isso).
        """
        if updated_user_obj.username in self.__all_users:
            # Atualiza os atributos do objeto existente
            self.__all_users[updated_user_obj.username].fullname = updated_user_obj.fullname
            self.__all_users[updated_user_obj.username].birthdate = updated_user_obj.birthdate
            self.__all_users[updated_user_obj.username].email = updated_user_obj.email
            self.__all_users[updated_user_obj.username].gender = updated_user_obj.gender
            self.__all_users[updated_user_obj.username].permissions = updated_user_obj.permissions
            # password_hash e session_id não devem ser alterados aqui

            self.__write_all_users()
            print(f"Usuário {updated_user_obj.username} atualizado com sucesso.")
            return True
        print(f"Erro: Usuário {updated_user_obj.username} não encontrado para atualização de perfil.")
        return False

    def logout(self, session_id):
        """
        Desautentica um usuário, removendo seu session_id da memória e do arquivo.
        """
        if session_id in self.__authenticated_users:
            user = self.__authenticated_users.pop(session_id)
            user.session_id = None # Remove o session_id do objeto UserAccount
            self.__write_all_users() # Salva a remoção do session_id no arquivo
            print(f"Sessão {session_id} encerrada para '{user.username}'.")
            return True
        print(f"Sessão {session_id} não encontrada para deslogar.")
        return False

    def user_exists(self, username):
        """Verifica se um usuário com o dado username já existe no sistema."""
        return username in self.__all_users


class HouseRecord:
    """Gerencia as casas (ambientes) e suas associações com usuários"""

    def __init__(self):
        self.houses = {}
        self.load()

    def load(self):
        houses_data = _load_json_data(HOUSES_FILE, dict)
        self.houses = {
            house_id: House(
                house_id=house_id,
                name=house['name'],
                members=house.get('members', []),
                chores=house.get('chores', []),
                last_member=house.get('last_member', 0)
            )
            for house_id, house in houses_data.items()
        }
        print(f"Casas carregadas: {len(self.houses)}")

    def save(self):
        houses_data = {
            house.id: { # Use house.id como chave principal
                'id': house.id, # Inclua o ID dentro do dicionário também
                'name': house.name,
                'members': house.members,
                'chores': house.chores,
                'last_member': house.last_member
            }
            for house in self.houses.values()
        }
        _write_json_data(HOUSES_FILE, houses_data)
        print("Dados das casas salvos com sucesso.")

    def create_house(self, name, owner_username):
        house_id = str(uuid.uuid4())
        new_house = House(house_id=house_id, name=name, members=[owner_username])
        self.houses[house_id] = new_house
        self.save()
        print(f"Casa '{name}' ({house_id}) criada por '{owner_username}'.")
        return house_id
    
    def get_house_by_user(self, username):
        for house_id, house in self.houses.items():
            if username in house.members:
                return house
        return None

    def house_exists(self, house_id):
        return house_id in self.houses

    def list_houses(self):
        return [{'id': house_id, 'name': house.name} for house_id, house in self.houses.items()]