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

    // --- Search & Analysis Logic ---
    const container = document.querySelector('.stats-container');
    const searchUrl = container.dataset.searchUrl;
    const getItemsUrl = container.dataset.getItemsUrl;
    const analyzeUrl = container.dataset.analyzeUrl;
    const csrfToken = container.dataset.csrfToken;

    // 1. Search
    const searchBtn = document.getElementById('log-search-btn');
    const searchInput = document.getElementById('log-search-input');
    const resultsContainer = document.getElementById('search-results-container');
    const resultsList = document.getElementById('search-results-list');

    const noResultsText = container.dataset.noResultsText || 'No matches found';
    
    searchBtn.addEventListener('click', () => {
        const query = searchInput.value;
        if (!query) return;

        fetch(searchUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
            body: JSON.stringify({query: query})
        })
        .then(res => res.json())
        .then(data => {
            resultsList.innerHTML = '';
            resultsContainer.classList.remove('hidden');
            if (data.results.length === 0) {
                resultsList.innerHTML = `<li>${noResultsText}</li>`;
            } else {
                data.results.forEach(log => {
                    const li = document.createElement('li');
                    li.innerHTML = `<a href="/dashboard/calendar/?date=${log.date}"><span>${log.date}</span></a> <span>${log.note}</span>`;
                    resultsList.appendChild(li);
                });
            }
        });
    });


    // 2. Analysis Items
    let allItems = {};
    let selectedItems = new Set(); // Stores item names for current tab

    function loadItems() {
        return fetch(getItemsUrl).then(res => res.json()).then(data => {
            allItems = data;
            renderChips('symptom'); // Default
        });
    }

    function renderChips(type) {
        const chipsContainer = document.getElementById('analysis-chips-container');
        chipsContainer.innerHTML = '';
        const items = allItems[type + 's'] || []; // key is plural 'symptoms', type is singular 'symptom'

        items.forEach(item => {
            const chip = document.createElement('div');
            chip.className = 'chip';
            if (selectedItems.has(item.id)) chip.classList.add('active');
            
            chip.textContent = item.name;
            chip.addEventListener('click', () => {
                toggleSelection(type, item.id);
                // Update visual state
                if (selectedItems.has(item.id)) chip.classList.add('active');
                else chip.classList.remove('active');
            });
            chipsContainer.appendChild(chip);
        });
    }

    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Clear selection on tab switch
            selectedItems.clear();
            document.getElementById('analysis-result-panel').classList.add('hidden');
            
            renderChips(this.dataset.type);
        });
    });

    function toggleSelection(type, id) {
        if (selectedItems.has(id)) {
            selectedItems.delete(id);
        } else {
            selectedItems.add(id);
        }
        analyzeItems(type);
    }

    // 3. Analyze Items (Multi)
    function analyzeItems(type) {
        const ids = Array.from(selectedItems);
        const resultPanel = document.getElementById('analysis-result-panel');
        
        if (ids.length === 0) {
            resultPanel.classList.add('hidden');
            return;
        }

        // Find translated names for display
        const displayNames = allItems[type + 's']
            .filter(item => selectedItems.has(item.id))
            .map(item => item.name);

        fetch(analyzeUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
            body: JSON.stringify({item_type: type, item_names: ids})
        })
        .then(res => res.json())
        .then(data => {
            resultPanel.classList.remove('hidden');
            document.getElementById('analysis-item-name').textContent = displayNames.join(', ');
            document.getElementById('analysis-total-count').textContent = data.total;
            
            // Occurrences
            const datesList = document.getElementById('analysis-dates-list');
            datesList.innerHTML = '';
            data.occurrences.slice(0, 10).forEach(date => {
                 const li = document.createElement('li');
                 // Link to Calendar View instead of Add Log
                 li.innerHTML = `<a href="/dashboard/calendar/?date=${date}">${date}</a>`;
                 datesList.appendChild(li);
            });
        });
    }

    // 4. Top Symptoms
    const topSymptomsUrl = container.dataset.topSymptomsUrl;
    
    function loadTopSymptoms() {
        fetch(topSymptomsUrl)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('top-symptoms-container');
            const emptyState = document.getElementById('top-symptoms-empty');
            
            if (data.top_symptoms.length === 0) {
                 emptyState.classList.remove('hidden');
                 return;
            }
            
            container.innerHTML = '';
            data.top_symptoms.forEach(item => {
                const card = document.createElement('div');
                card.className = 'stat-item';
                card.innerHTML = `
                    <h3 class="stat-title">${item.name}</h3>
                    <p class="stat-value">${item.count}</p>
                `;
                container.appendChild(card);
            });
        });
    }

    // Initial Load
    loadItems();
    loadTopSymptoms();

});