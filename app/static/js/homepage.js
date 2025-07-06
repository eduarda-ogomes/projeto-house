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
});
