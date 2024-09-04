class UserAccount():

    def __init__(self, username, password):

        self.username= username
        self.password= password



class SuperAccount(UserAccount):

    def __init__(self, username, password, permissions):

        super().__init__(username, password)
        self.permissions= permissions
