import datetime

class Chore:
    def __init__(self, activity, date, status="pending", assigned_to=None, rotation_days=0, next_due=None, last_completed_date=None, last_completed_by=None):
        self.activity = activity    
        self.date = date # Data original da tarefa (cadastro)
        self.status = status # 'pending', 'completed', etc.
        self.assigned_to = assigned_to
        self.rotation_days = rotation_days
        self.next_due = next_due if next_due else date # Data do próximo vencimento
        self.last_completed_date = last_completed_date # Data da última conclusão
        self.last_completed_by = last_completed_by # Quem completou por último

    def __repr__(self):
        return f"Chore(activity='{self.activity}', assigned_to='{self.assigned_to}', next_due='{self.next_due}')"

    def is_overdue(self):
        if self.next_due:
            try:
                due_date = datetime.datetime.strptime(self.next_due, '%Y-%m-%d').date()
                return due_date < datetime.date.today()
            except ValueError:
                return False
        return False

    def complete(self, completed_by_username):
        self.last_completed_date = datetime.date.today().strftime('%Y-%m-%d')
        self.last_completed_by = completed_by_username
        self.status = "completed" # Opcional: atualizar o status