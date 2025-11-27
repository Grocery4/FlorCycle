document.addEventListener('DOMContentLoaded', function() {
    const selectedDates = new Set(window.selectedDates || []);

    selectedDates.forEach(dateStr => {
        const checkbox = document.querySelector(`input[value="${dateStr}"]`);
        if (checkbox) checkbox.checked = true;
    });
});