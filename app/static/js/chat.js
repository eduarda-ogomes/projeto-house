const socket = io('http://localhost:8080'); // Endereço do servidor Socket.IO

// Seleciona o botão pelo ID
const button = document.getElementById('sendButton');

socket.on('connect', () => {
   console.log('Conexão estabelecida com o servidor Socket.IO');
});

socket.on('message', (data) => {
    displayMessage(data.content, data.username);
});

socket.on('updateUsers', (users) => {
    updateUserList(users);
});

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value;
    socket.emit('message', message);
    messageInput.value = '';
}

function displayMessage(message,user) {
   const messageDisplay = document.getElementById('messageDisplay');
   messageDisplay.innerHTML += `<li>${message} | escrita por: ${user}</li>`;
}

function updateUserList(users) {
    const usersDisplay = document.getElementById('usersDisplay');
    usersDisplay.innerHTML = '';

    users.forEach(user => {
        const listItem = document.createElement('li');
        listItem.textContent = user;
        usersDisplay.appendChild(listItem);
    });
}

button.addEventListener('click', sendMessage);
