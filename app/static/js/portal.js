document.addEventListener("DOMContentLoaded", function() {
    const image = document.querySelector("img");
    const statusMessageDiv = document.getElementById('status-message');

    // Função existente para a imagem
    if (image) {
        image.addEventListener("click", function() {
            document.body.style.backgroundColor = getRandomColor();
            // A função showAnimatedMessage() não é ideal aqui se você quer uma mensagem persistente
            // showAnimatedMessage("Você clicou na imagem!"); 
        });
    }

    function getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    // Função para exibir a mensagem de status (cadastro, remoção, etc.)
    function displayStatusMessage() {
        const message = localStorage.getItem('displayStatusMessage');
        const type = localStorage.getItem('statusMessageType'); // 'success', 'removed', etc.

        if (message && statusMessageDiv) {
            statusMessageDiv.textContent = message;
            statusMessageDiv.style.display = 'block';

            // Adiciona classe para estilização específica
            if (type) {
                statusMessageDiv.classList.add(`status-message-${type}`);
            }

            // Opcional: Remover a mensagem do localStorage após exibi-la
            // para que não reapareça em futuros recarregamentos da página
            localStorage.removeItem('displayStatusMessage');
            localStorage.removeItem('statusMessageType');

            // Opcional: Fazer a mensagem desaparecer automaticamente após alguns segundos
            setTimeout(() => {
                statusMessageDiv.style.display = 'none';
                statusMessageDiv.classList.remove(`status-message-${type}`); // Remove a classe de estilo
            }, 7000); // Mensagem some após 7 segundos
        }
    }

    // Chama a função para exibir a mensagem ao carregar a página
    displayStatusMessage();

    // Removi a função showAnimatedMessage porque ela era para mensagens temporárias no body.
    // Agora temos um local específico no HTML para mensagens de status.
    // Se você ainda quiser uma mensagem animada genérica para o clique da imagem,
    // precisará adaptar essa função para usar 'statusMessageDiv' ou criar outro div temporário.
});