document.addEventListener('DOMContentLoaded', function() {
    // Lógica para marcar tarefas como completas
    const checkboxes = document.querySelectorAll('.complete-chore-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                this.closest('.complete-chore-form').submit();
            }
        });
    });

    // --- Lógica do Chat em Tempo Real ---
    const socket = io(); // Conecta ao servidor Socket.IO
    const messagesContainer = document.getElementById('messages-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    // Recupera dados do usuário e da casa do HTML (passados pelo Bottle)
    // Você pode usar um elemento HTML escondido para armazenar esses dados ou usar variáveis JS globais
    // Exemplo: <input type="hidden" id="current-username" value="{{ user.username }}">
    //         <input type="hidden" id="current-house-id" value="{{ house.id }}">
    const currentUsername = document.getElementById('current-username') ? document.getElementById('current-username').value : 'Usuário Desconhecido';
    const currentHouseId = document.getElementById('current-house-id') ? document.getElementById('current-house-id').value : null;

    // Adiciona elementos escondidos para passar user.username e house.id para o JS
    // (Isso é uma correção para o HTML, mas podemos fazer o JS tentar buscá-los se eles forem renderizados diretamente no template)
    // Se você não adicionou os inputs hidden, o JS abaixo precisará ser ajustado.
    // Melhor prática: Incluir esses valores diretamente no script gerado pelo template se forem sensíveis ou sempre presentes.
    // Por simplicidade, vou assumir que você pode adicioná-los.

    // Exemplo de como adicionar os inputs hidden no homepage_in_house.html (dentro do body, em qualquer lugar visível para JS):
    /*
    <input type="hidden" id="current-username" value="{{ user.username }}">
    <input type="hidden" id="current-house-id" value="{{ house.id }}">
    */
    // Se a house.id for nula, o chat não funcionará.

    // Função para rolar o container de mensagens para o final
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Função para exibir uma nova mensagem no chat
    function displayMessage(message) {
        const messageItem = document.createElement('div');
        messageItem.classList.add('message-item');
        
        // Adiciona classe para diferenciar suas mensagens das outras
        if (message.username === currentUsername) {
            messageItem.classList.add('my-message');
        } else {
            messageItem.classList.add('other-message');
        }

        const usernameSpan = document.createElement('span');
        usernameSpan.classList.add('message-username');
        usernameSpan.textContent = message.username + ':';

        const contentSpan = document.createElement('span');
        contentSpan.classList.add('message-content');
        contentSpan.textContent = message.content;

        const timestampSpan = document.createElement('span');
        timestampSpan.classList.add('message-timestamp');
        timestampSpan.textContent = new Date(message.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

        messageItem.appendChild(usernameSpan);
        messageItem.appendChild(contentSpan);
        messageItem.appendChild(timestampSpan);
        messagesContainer.appendChild(messageItem);

        scrollToBottom(); // Rola para a nova mensagem
    }

    // Ao conectar ao Socket.IO, junte-se à sala da casa
    socket.on('connect', function() {
        console.log('Conectado ao servidor Socket.IO.');
        if (currentHouseId) {
            socket.emit('join_house_room', { house_id: currentHouseId });
            console.log('Tentando entrar na sala da casa:', currentHouseId);
        } else {
            console.warn('ID da casa não encontrada. O chat não funcionará corretamente.');
        }
    });

    // Evento para receber novas mensagens
    socket.on('new_house_message', function(msg) {
        console.log('Mensagem recebida:', msg);
        displayMessage(msg);
    });

    // Evento para receber mensagens antigas ao entrar na sala (opcional, se você implementar no backend)
    // socket.on('old_messages', function(data) {
    //     console.log('Mensagens antigas recebidas:', data.messages);
    //     data.messages.forEach(msg => displayMessage(msg));
    // });


    // Enviar mensagem quando o botão é clicado
    sendButton.addEventListener('click', function() {
        sendMessage();
    });

    // Enviar mensagem quando a tecla Enter é pressionada no campo de input
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const content = messageInput.value.trim();
        if (content && currentHouseId && currentUsername) {
            // Emite a mensagem para o servidor
            socket.emit('send_house_message', {
                content: content,
                house_id: currentHouseId,
                username: currentUsername
            });
            messageInput.value = ''; // Limpa o input
        }
    }

    // Rolagem inicial para o final do chat se já houver mensagens
    scrollToBottom();
});