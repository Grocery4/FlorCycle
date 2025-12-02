document.addEventListener('DOMContentLoaded', function() {
    
    function initializePeriodSelector() {
        const selectedDates = new Set(window.selectedDates || []);
        selectedDates.forEach(dateStr => {
            const checkbox = document.querySelector(`input[value="${dateStr}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    //Trigger on page-load, and on 'calendars-updated' event dispatch
    initializePeriodSelector();
    document.addEventListener('calendars-updated', initializePeriodSelector);
});