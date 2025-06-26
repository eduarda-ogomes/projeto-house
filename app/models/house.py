import datetime

class House:
    def __init__(self, house_id, name, members=None, chores=None, last_member=0):
        self.id = house_id
        self.name = name
        self.members = members if members is not None else []
        self.chores  = chores if chores is not None else []
        self.last_member = last_member # Novo atributo para rotatividade

    def add_member(self, username):
        if username not in self.members:
            self.members.append(username)
            # Se um novo membro for adicionado, talvez você queira redefinir a rotação
            # ou ajustar o índice se o membro for adicionado no meio da lista.
            # Por simplicidade, vamos manter o índice atual.

    def add_chore(self, activity, date_str, rotation_days=None): # date_str para receber string do HTML
        if not self.members:
            # Não há membros para atribuir a tarefa
            self.chores.append({
                'activity': activity,
                'date': date_str,
                'assigned_to': 'Ninguém (sem moradores)',
                'next_due': date_str # Data inicial de vencimento
            })
            return

        # 1. Determinar o próximo morador
        num_members = len(self.members)
        if num_members == 0:
            assigned_member = "Ninguém (sem membros)"
            self.last_member = 0 # Reinicia se não tiver membros
        else:
            assigned_member = self.members[self.last_member]
            # Atualiza o índice para o próximo morador para a próxima tarefa
            self.last_member = (self.last_member + 1) % num_members

        # 2. Calcular a próxima data de rotatividade (se aplicável)
        next_due_date = date_str # Data inicial da tarefa
        if rotation_days is not None and rotation_days > 0:
            try:
                initial_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                next_due_date = (initial_date + datetime.timedelta(days=rotation_days)).strftime('%Y-%m-%d')
            except ValueError:
                print(f"Formato de data inválido: {date_str}. Usando a data original.")
                next_due_date = date_str

        # 3. Adicionar a tarefa com o morador atribuído e a data de próxima rotação
        self.chores.append({
            'activity': activity,
            'date': date_str, # Data inicial de cadastro/vencimento
            'assigned_to': assigned_member,
            'rotation_days': rotation_days, # Quantos dias para a próxima rotação
            'next_due': next_due_date # Próxima data em que a tarefa deve ser feita por outro
        })

    def remove_member(self, username):
        if username in self.members:
            self.members.remove(username)
            # Ajustar o índice se o membro removido afetar a rotação
            if self.last_member >= len(self.members) and len(self.members) > 0:
                self.last_member = 0 # Volta para o início se o índice exceder

            # Opcional: Reatribuir tarefas do membro removido ou marcá-las
            for chore in self.chores:
                if chore.get('assigned_to') == username:
                    chore['assigned_to'] = 'Não Atribuído' # Ou reatribua, mais complexo


    # Opcional: Método para "completar" uma tarefa e rotacionar
    def complete_chore(self, activity, current_date_str):
        for chore in self.chores:
            if chore['activity'] == activity:
                # Encontra o próximo membro para a rotatividade
                num_members = len(self.members)
                if num_members > 0:
                    current_assignee_index = self.members.index(chore['assigned_to']) if chore['assigned_to'] in self.members else -1
                    next_assignee_index = (current_assignee_index + 1) % num_members
                    chore['assigned_to'] = self.members[next_assignee_index]
                else:
                    chore['assigned_to'] = 'Ninguém (sem moradores)'

                # Atualiza a data de vencimento para a próxima rotação
                if chore.get('rotation_days') is not None and chore['rotation_days'] > 0:
                    try:
                        current_date = datetime.datetime.strptime(current_date_str, '%Y-%m-%d').date()
                        chore['next_due'] = (current_date + datetime.timedelta(days=chore['rotation_days'])).strftime('%Y-%m-%d')
                    except ValueError:
                        print(f"Data de conclusão inválida: {current_date_str}")
                return True
        return False

    def __repr__(self):
        return f"House(id='{self.id}', name='{self.name}', members={len(self.members)}, chores={len(self.chores)})"