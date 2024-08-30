const socket = io('http://localhost:8080'); // Endereço do servidor Socket.IO

// Seleciona o botão pelo ID
const button = document.getElementById('sendButton');

socket.on('connect', () => {
   console.log('Conexão estabelecida com o servidor Socket.IO');
});

socket.on('message', (data) => {
    displayMessage(data.content, data.username);
});

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value;
    socket.emit('message', message);
    messageInput.value = ''; // Limpa o campo após o envio
}

function displayMessage(message,user) {
   const messageDisplay = document.getElementById('messageDisplay');
   messageDisplay.innerHTML += `<li>${message} | escrita por: ${user}</li>`;
}

// Adiciona o listener de evento ao botão
button.addEventListener('click', sendMessage);
