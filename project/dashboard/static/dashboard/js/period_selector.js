document.addEventListener('DOMContentLoaded', function() {
    const selectedDates = new Set(window.selectedDates || []);

    function initializePeriodSelector() {
        selectedDates.forEach(dateStr => {
            const checkbox = document.querySelector(`input[value="${dateStr}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    //Trigger on page-load, and on 'calendars-updated' event dispatch
    initializePeriodSelector();
    document.addEventListener('calendars-updated', initializePeriodSelector);
});