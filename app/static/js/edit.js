const socket = io('http://localhost:8080'); // Endereço do servidor Socket.IO

socket.on('connect', () => {
   console.log('Conexão estabelecida com o servidor Socket.IO');
});

// recebimento de uma nova lista de usuários conectados
socket.on('update_account_event', (data) => {
    updateUserRecordList(data.accounts)
});

function updateUserRecordList(users) {
    const editDisplay = document.getElementById('editDisplay');
    if (editDisplay) {
        editDisplay.innerHTML = '';
        users.forEach(user => {
            const listItem = document.createElement('li');
            listItem.textContent = user.username;
            editDisplay.appendChild(listItem);
        });
    } else {
        console.error('Elemento editDisplay não encontrado');
    }
}
