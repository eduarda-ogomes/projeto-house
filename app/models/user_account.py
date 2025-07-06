class UserAccount:
    def __init__(self, fullname, username, birthdate, email, password_hash, gender, permissions=None, session_id=None):
        self.fullname = fullname
        self.username = username
        self.birthdate = birthdate
        self.email = email
        self.password_hash = password_hash
        self.gender = gender
        self.permissions = permissions if permissions is not None else []
        self.session_id = session_id

    def isAdmin(self):
        return False
    
    def to_dict(self):
        return {
            'fullname': self.fullname,
            'username': self.username,
            'birthdate': self.birthdate,
            'email': self.email,
            'password_hash': self.password_hash,
            'gender': self.gender,
            'session_id': self.session_id
        }

class SuperAccount(UserAccount):
    def __init__(self, fullname, username, birthdate, email, password_hash, gender, permissions=None, session_id=None):
        super().__init__(fullname, username, birthdate, email, password_hash, gender, permissions, session_id)

    def isAdmin(self):
        return True