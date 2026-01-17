document.addEventListener('DOMContentLoaded', function() {
    // Código existente para checkboxes - Mantenha se ainda for relevante
    const checkboxes = document.querySelectorAll('.complete-chore-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                this.closest('.complete-chore-form').submit();
            }
        });
    });

    // Referências aos elementos do formulário
    const registrationForm = document.getElementById('form');
    const fullnameInput = document.getElementById('fullname');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');

    /**
     * Aplica a animação de tremor (shake) ao campo de input.
     * Garante que a animação seja reiniciada a cada chamada.
     * @param {HTMLElement} inputElement - O elemento <input> que acionou o erro.
     */
    function applyShake(inputElement) {
        // Encontra o div pai com a classe 'input-field' que envolve o input e o ícone.
        const inputFieldDiv = inputElement.closest('.input-field'); 
        
        if (inputFieldDiv) {
            // 1. Remove a classe 'shake-input' para garantir que a animação possa ser reiniciada.
            inputFieldDiv.classList.remove('shake-input'); 

            // 2. Força o navegador a fazer um "reflow" (recalcular o layout).
            // Isso é um truque para garantir que a animação CSS seja reiniciada do zero.
            void inputFieldDiv.offsetWidth; 

            // 3. Adiciona a classe 'shake-input' para iniciar a animação.
            inputFieldDiv.classList.add('shake-input');

            // 4. Foca no campo para o usuário preencher.
            inputElement.focus(); 

            // 5. Remove a classe 'shake-input' após a animação terminar.
            // Isso permite que a animação possa ser acionada novamente se o erro persistir.
            inputFieldDiv.addEventListener('animationend', function() {
                inputFieldDiv.classList.remove('shake-input');
            }, { once: true }); // O evento é escutado apenas uma vez
        } else {
            // Se por algum motivo o '.input-field' não for encontrado, loga um erro no console.
            console.error("Não foi possível encontrar o elemento pai '.input-field' para:", inputElement);
        }
    }

    // Funcionalidade de alternar visibilidade da senha (ícone de olho)
    const passwordIcons = document.querySelectorAll('.password-icon');
    passwordIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            const inputField = this.previousElementSibling; // O input é o irmão anterior do ícone
            if (inputField.type === 'password') {
                inputField.type = 'text';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
            } else {
                inputField.type = 'password';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
            }
        });
    });

    // Adiciona o ouvinte para o evento de submit do formulário
    registrationForm.addEventListener('submit', function(event) {
        let formIsValid = true;
        let errorMessage = ''; // Para acumular as mensagens de erro

        // --- VALIDAÇÕES DOS CAMPOS ---

        // Validação de Nome Completo
        // Checa se o campo está vazio (ignorando espaços em branco)
        if (fullnameInput.value.trim() === '') {
            applyShake(fullnameInput); // Aplica o tremor
            errorMessage += '• O campo "Nome completo" é obrigatório.\n';
            formIsValid = false;
        }

        // Validação de Usuário
        // Checa se o campo está vazio (ignorando espaços em branco)
        if (usernameInput.value.trim() === '') {
            applyShake(usernameInput); // Aplica o tremor
            errorMessage += '• O campo "Usuário" é obrigatório.\n';
            formIsValid = false;
        }

        // Validação de Senha (mínimo de 6 caracteres)
        // Se a senha tiver menos de 6 caracteres E não estiver vazia
        if (passwordInput.value.length < 6) {
            applyShake(passwordInput); // Aplica o tremor
            errorMessage += '• A senha deve ter pelo menos 6 caracteres.\n';
            formIsValid = false;
        }

        // Validação de Confirmação de Senha
        // 1. Checa se o campo de confirmação está vazio
        if (confirmPasswordInput.value.trim() === '') {
            applyShake(confirmPasswordInput); // Aplica o tremor
            errorMessage += '• A confirmação de senha é obrigatória.\n';
            formIsValid = false;
        } 
        // 2. Checa se as senhas não coincidem (após verificar se não está vazio)
        else if (passwordInput.value !== confirmPasswordInput.value) {
            applyShake(passwordInput); // Tremer a senha original também para feedback
            applyShake(confirmPasswordInput); // Aplica o tremor na confirmação
            errorMessage += '• As senhas não coincidem.\n';
            formIsValid = false;
        }

        // --- CONTROLE DE SUBMISSÃO DO FORMULÁRIO ---
        // Se alguma validação falhar, impede o envio do formulário e mostra o alerta
        if (!formIsValid) {
            event.preventDefault(); // Impede o envio padrão do formulário
            alert('Por favor, corrija os seguintes erros:\n\n' + errorMessage);
        }
    });

    // --- VALIDAÇÃO EM TEMPO REAL (OPCIONAL, mas recomendado para boa UX) ---
    // Faz o campo tremer assim que o usuário sai dele (evento 'blur'), se houver erro.

    fullnameInput.addEventListener('blur', function() {
        if (fullnameInput.value.trim() === '') {
            applyShake(fullnameInput);
        }
    });

    usernameInput.addEventListener('blur', function() {
        if (usernameInput.value.trim() === '') {
            applyShake(usernameInput);
        }
    });

    passwordInput.addEventListener('blur', function() {
        // Só treme se a senha for inválida E não estiver vazia (para não tremer logo de cara)
        if (passwordInput.value.length > 0 && passwordInput.value.length < 6) {
            applyShake(passwordInput);
        }
        // Se a confirmação de senha já foi preenchida, verifica a correspondência
        if (confirmPasswordInput.value.length > 0 && passwordInput.value !== confirmPasswordInput.value) {
            applyShake(confirmPasswordInput);
        }
    });

    confirmPasswordInput.addEventListener('blur', function() {
        // Só treme se as senhas não coincidirem E a confirmação não estiver vazia
        if (confirmPasswordInput.value.length > 0 && passwordInput.value !== confirmPasswordInput.value) {
            applyShake(confirmPasswordInput);
        }
    });
});

registrationForm.addEventListener('submit', function(event) {
    let formIsValid = true;
    let errorMessage = '';

    // ... (suas validações de campos e senhas aqui) ...

    if (formIsValid) {
        // Se todas as validações no frontend passarem, armazena a mensagem
        localStorage.setItem('displayStatusMessage', 'Cadastro realizado com sucesso! Faça login.');
        localStorage.setItem('statusMessageType', 'success'); // Opcional: para estilizar diferentemente
        // O formulário será enviado, e seu backend deve redirecionar para /portal.
        // Não adicione window.location.href = '/portal'; aqui se o backend já faz isso.
    } else {
        event.preventDefault();
        alert('Por favor, corrija os seguintes erros:\n\n' + errorMessage);
    }
});