class UserAccount:
    def __init__(self, fullname, username, birthdate, email, password, gender, permissions=None):
        self.fullname = fullname
        self.username = username
        self.birthdate = birthdate
        self.email = email
        self.password = password
        self.gender = gender
        self.permissions = permissions if permissions is not None else []

    def isAdmin(self):
        return False

class SuperAccount(UserAccount):
    def __init__(self, fullname, username, birthdate, email, password, gender, permissions):
        super().__init__(fullname, username, birthdate, email, password, gender)
        self.permissions = permissions if permissions else ['user']

    def isAdmin(self):
        return True

