document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('.complete-chore-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                this.closest('.complete-chore-form').submit();
            }
        });
    });

    const registrationForm = document.querySelector('form[action="/cadastro"]');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const passwordMatchError = document.getElementById('password-match-error');

    if (registrationForm && passwordInput && confirmPasswordInput && passwordMatchError) {
        function validatePasswords() {
            if (passwordInput.value !== confirmPasswordInput.value) {
                passwordMatchError.style.display = 'block';
                confirmPasswordInput.setCustomValidity('As senhas não coincidem.');
            } else {
                passwordMatchError.style.display = 'none';
                confirmPasswordInput.setCustomValidity('');
            }
        }

        passwordInput.addEventListener('input', validatePasswords);
        confirmPasswordInput.addEventListener('input', validatePasswords);

        registrationForm.addEventListener('submit', function(event) {
            validatePasswords();
            if (confirmPasswordInput.checkValidity() === false) {
                event.preventDefault();
                alert('Por favor, corrija os erros no formulário.');
            }
        });
    }
});