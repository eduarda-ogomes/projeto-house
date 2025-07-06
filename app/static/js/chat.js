document.addEventListener('DOMContentLoaded', function() {
    const socket = io(); // Conecta ao servidor Socket.IO

    const messagesContainer = document.getElementById('messages-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const currentUsername = document.getElementById('current-username') ? document.getElementById('current-username').value : 'Usuário Desconhecido';
    const currentHouseId = document.getElementById('current-house-id') ? document.getElementById('current-house-id').value : null;

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function displayMessage(message) {
        const messageItem = document.createElement('div');
        messageItem.classList.add('message-item');

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

        scrollToBottom();
    }

    socket.on('connect', function() {
        console.log('Conectado ao servidor Socket.IO.');
        if (currentHouseId) {
            socket.emit('join_house_room', { house_id: currentHouseId });
            console.log('Entrou na sala da casa:', currentHouseId);
        } else {
            console.warn('ID da casa não encontrada. Chat pode não funcionar.');
        }
    });

    socket.on('new_house_message', function(msg) {
        console.log('Mensagem recebida:', msg);
        displayMessage(msg);
    });

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const content = messageInput.value.trim();
        if (content && currentHouseId && currentUsername) {
            socket.emit('send_house_message', {
                content,
                house_id: currentHouseId,
                username: currentUsername
            });
            messageInput.value = '';
        }
    }

    scrollToBottom();
});
