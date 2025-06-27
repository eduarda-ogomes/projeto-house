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
        print(f"\n--- DEBUG: add_member para {self.name} ---")
        print(f"Membros ANTES de adicionar: {self.members}")
        print(f"last_member ANTES de adicionar: {self.last_member}")

        if username not in self.members:
            self.members.append(username)
            num_members = len(self.members)

            if num_members > 0:
                if self.last_member >= num_members:
                    print(f"last_member ({self.last_member}) >= num_members ({num_members}). Resetando para 0.")
                    self.last_member = 0

                # Reatribuir tarefas sem atribuição ou com atribuição inválida
                # Esta parte garante que tarefas órfãs sejam reatribuídas
                for chore in self.chores:
                    # Se a tarefa está sem atribuição ou atribuída a alguém que não está mais na casa
                    if chore.get('assigned_to') == 'Ninguém' or chore.get('assigned_to') not in self.members:
                        print(f"DEBUG: Reatribuindo tarefa '{chore.get('activity')}' de '{chore.get('assigned_to')}'")
                        # Atribui ao próximo na rotação (considerando o novo membro para reatribuições)
                        assigned_member = self.members[self.last_member]
                        chore['assigned_to'] = assigned_member
                        print(f"DEBUG: Atribuído a: {assigned_member}")
                        self.last_member = (self.last_member + 1) % num_members
                        print(f"DEBUG: last_member APÓS reatribuição: {self.last_member}")
            else:
                self.last_member = 0
        
        print(f"Membros DEPOIS de adicionar: {self.members}")
        print(f"last_member DEPOIS de adicionar: {self.last_member}")
        print(f"--- FIM DEBUG: add_member ---\n")


    # --- MODIFICAÇÃO AQUI: add_chore para distribuição justa ---
    def add_chore(self, activity, date_str, rotation_days=0, next_due=None, last_completed_date=None, last_completed_by=None):
        print(f"\n--- DEBUG: add_chore para {self.name} (Distribuição Justa) ---")
        print(f"Membros atuais: {self.members}")
        print(f"last_member ANTES da atribuição: {self.last_member}")
        
        num_members = len(self.members)
        assigned_to = "Ninguém (sem moradores)"

        if num_members > 0:
            member_pending_chores = {member: 0 for member in self.members}
            for chore in self.chores:
                if chore.get('last_completed_date') is None:
                    assigned_member_chore = chore.get('assigned_to')
                    if assigned_member_chore in member_pending_chores:
                        member_pending_chores[assigned_member_chore] += 1
                else:
                    try:
                        next_due_date = datetime.datetime.strptime(chore.get('next_due', '9999-12-31'), '%Y-%m-%d').date()
                        if next_due_date <= datetime.date.today():
                            assigned_member_chore = chore.get('assigned_to')
                            if assigned_member_chore in member_pending_chores:
                                member_pending_chores[assigned_member_chore] += 1
                    except ValueError:
                        pass

            print(f"DEBUG: Tarefas pendentes por membro: {member_pending_chores}")

            min_chores = float('inf')
            for count in member_pending_chores.values():
                if count < min_chores:
                    min_chores = count
            
            least_busy_members = [
                member for member, count in member_pending_chores.items()
                if count == min_chores
            ]
            print(f"DEBUG: Membros com menos tarefas pendentes ({min_chores}): {least_busy_members}")

            start_index = self.last_member % num_members
            
            found_assignee = False
            for i in range(num_members):
                current_member_index = (start_index + i) % num_members
                candidate_member = self.members[current_member_index]
                
                if candidate_member in least_busy_members:
                    assigned_to = candidate_member
                    # --- AQUI ESTÁ A MUDANÇA ---
                    # Incrementa last_member para o PRÓXIMO DA FILA após a atribuição
                    # Isso garante que a próxima busca por "menos ocupados" comece de um novo ponto
                    self.last_member = (self.last_member + 1) % num_members 
                    found_assignee = True
                    break
            
            if not found_assignee:
                # Fallback, caso algo dê errado na lógica de menos ocupados (improvável com num_members > 0)
                assigned_to = self.members[self.last_member]
                self.last_member = (self.last_member + 1) % num_members
                print("DEBUG: Fallback para rotação simples, não encontrou menos ocupado.")


        print(f"Tarefa '{activity}' atribuída a: {assigned_to}")
        print(f"last_member APÓS incremento (para próxima tarefa): {self.last_member}")

        initial_due_date = date_str
        if rotation_days is not None and rotation_days > 0:
            try:
                initial_date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                next_due_calc = (initial_date_obj + datetime.timedelta(days=rotation_days)).strftime('%Y-%m-%d')
            except ValueError:
                print(f"Formato de data inválido para rotação: {date_str}. Usando a data original.")
                next_due_calc = date_str
        else:
            next_due_calc = date_str

        new_chore = {
            "activity": activity,
            "date": date_str,
            "assigned_to": assigned_to,
            "rotation_days": rotation_days,
            "next_due": next_due_calc,
            "last_completed_date": last_completed_date,
            "last_completed_by": last_completed_by
        }
        self.chores.append(new_chore)
        print(f"--- FIM DEBUG: add_chore ---\n")
        return True

    
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