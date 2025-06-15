class House:
    def __init__(self, house_id, name, members=None):
        self.id = house_id
        self.name = name
        self.members = members if members else []

    def add_member(self,username):
        if username not in self.members:
            self.members.append(username)

    def remove_member(self,username):
        if username in self.members:
            self.members.remove(username)