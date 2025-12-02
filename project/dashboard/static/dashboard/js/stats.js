document.addEventListener('DOMContentLoaded', function() {
    const activity_dropdown = document.getElementById('activity-range-dropdown');
    const frequency_dropdown = document.getElementById('frequency-range-dropdown');

    activity_dropdown.addEventListener('change', function() {
        const monthRange = this.value;
        
        fetch('/dashboard/ajax/load-stats', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ 
                month_range: monthRange,
                type: 'activity_dropdown'
             })
        })
        .then(response => response.json())
        .then(data =>{
            document.getElementById('intercourse-count').textContent = data.intercourse_count;
            document.getElementById('orgasm-percentage').textContent = (data.orgasm_percentage ? data.orgasm_percentage.toFixed(1) : '0');
            document.getElementById('protected-count').textContent = data.protected_count;
            document.getElementById('unprotected-count').textContent = data.unprotected_count;
        })
    });
    
    frequency_dropdown.addEventListener('change', function() {
        const monthRange = this.value;

        fetch('/dashboard/ajax/load-stats', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ 
                month_range: monthRange,
                type: 'frequency_dropdown'
            })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('frequency-intercourse').textContent = data.frequency_intercourse.toFixed(1);
            document.getElementById('frequency-orgasm').textContent = data.frequency_orgasm.toFixed(1);
        })
    });
});