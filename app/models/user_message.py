import datetime

class UserMessage:
    def __init__(self, username, content, house_id, timestamp=None):
        self.username = username
        self.content = content
        self.house_id = house_id # Novo campo para a ID da casa
        self.timestamp = timestamp if timestamp else datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        """Retorna uma representação em dicionário do objeto, útil para JSON."""
        return {
            "username": self.username,
            "content": self.content,
            "house_id": self.house_id,
            "timestamp": self.timestamp
        }