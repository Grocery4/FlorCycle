document.addEventListener('DOMContentLoaded', function () {
    const resetButtons = document.querySelectorAll('.reset-btn');

    resetButtons.forEach((button) => {
        button.addEventListener('click', function () {
            const fieldId = this.getAttribute('data-field');
            const fieldContainer = document.getElementById(fieldId);

            if (fieldContainer) {
                // Uncheck all checkboxes in this field
                const checkboxes = fieldContainer.querySelectorAll(
                    'input[type="checkbox"]',
                );
                checkboxes.forEach((checkbox) => {
                    checkbox.checked = false;
                });

                // Remove any inline styles to let CSS take over
                const labels = fieldContainer.querySelectorAll('label');
                labels.forEach((label) => {
                    label.removeAttribute('style');
                });
            }
        });
    });
});
