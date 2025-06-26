# app/models/house.py
import datetime

class House:
    def __init__(self, house_id, name, members=None, chores=None, last_member=0):
        self.id = house_id
        self.name = name
        self.members = members if members is not None else []
        self.chores = chores if chores is not None else [] # Agora armazena dicionários
        self.last_member = last_member # Índice do último membro que completou uma tarefa rotativa

    def add_member(self, username):
        if username not in self.members:
            self.members.append(username)

    # Revertido para usar dicionário para a tarefa
    def add_chore(self, activity, date, assigned_to, rotation_days=0, next_due=None, last_completed_date=None, last_completed_by=None):
        new_chore = {
            "activity": activity,
            "date": date, # Data original de criação/vencimento
            "assigned_to": assigned_to,
            "rotation_days": rotation_days,
            "next_due": next_due if next_due else date, # Próximo vencimento, se não especificado, é a data inicial
            "last_completed_date": last_completed_date,
            "last_completed_by": last_completed_by
        }
        self.chores.append(new_chore)
        return True # Sempre retorna True, já que a verificação de duplicidade foi removida

    def remove_member(self, username):
        if username in self.members:
            self.members.remove(username)
            # Ajustar o índice se o membro removido afetar a rotação
            if self.last_member >= len(self.members) and len(self.members) > 0:
                self.last_member = 0

            # Reatribuir tarefas do membro removido
            for chore in self.chores:
                if chore.get('assigned_to') == username:
                    # Reatribui ao primeiro membro restante ou a 'Ninguém'
                    chore['assigned_to'] = self.members[0] if self.members else 'Ninguém'
                    # Limpa informações de conclusão se foi ele quem concluiu
                    if chore.get('last_completed_by') == username:
                        chore['last_completed_by'] = None
                        chore['last_completed_date'] = None


    def complete_chore(self, activity, completed_by_username):
        for chore in self.chores:
            if chore['activity'] == activity and chore.get('assigned_to') == completed_by_username:
                chore['last_completed_date'] = datetime.date.today().strftime('%Y-%m-%d')
                chore['last_completed_by'] = completed_by_username
                
                # Se a tarefa tem rotação, calcula o próximo vencimento
                if chore.get('rotation_days') and chore['rotation_days'] > 0:
                    current_next_due = datetime.datetime.strptime(chore['next_due'], '%Y-%m-%d').date()
                    chore['next_due'] = (current_next_due + datetime.timedelta(days=chore['rotation_days'])).strftime('%Y-%m-%d')
                return True
        return False

    def __repr__(self):
        return f"House(id='{self.id}', name='{self.name}', members={len(self.members)}, chores={len(self.chores)})"