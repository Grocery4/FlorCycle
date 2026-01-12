document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('id_date');
    if (!dateInput) return;

    // gets CSRF Token
    const csrftoken = document.querySelector(
        '[name=csrfmiddlewaretoken]',
    ).value;

    const m2mFields = ['symptoms', 'moods', 'medications'];
    const mapping = {
        note: 'id_note',
        flow: 'id_flow',
        weight: 'id_weight',
        temperature: 'id_temperature',
        ovulation_test: 'id_ovulation_test',

        protected: 'id_protected',
        orgasm: 'id_orgasm',
        quantity: 'id_quantity',
    };

    // Render MultiCheckboxes
    function setMultiple(name, values) {
        document.querySelectorAll(`input[name="${name}"]`).forEach((box) => {
            box.checked = values.includes(parseInt(box.value));
        });
    }

    // Render Form values
    function setFormValues(mapping, data) {
        // Render on Form template
        for (const [key, id] of Object.entries(mapping)) {
            const el = document.getElementById(id);
            if (el) el.value = data[key] ?? '';
        }
    }

    // Clear form errors
    function clearFormErrors() {
        // Remove all error messages
        document.querySelectorAll('.error-message').forEach((error) => {
            error.remove();
        });

        // Remove error classes from form fields
        document.querySelectorAll('.form-field').forEach((field) => {
            field.classList.remove('error');
        });

        // Clear the main form errors container
        const formErrors = document.querySelector('.form-errors');
        if (formErrors) {
            formErrors.remove();
        }
    }

    function clearForm(mapping) {
        for (const id of Object.values(mapping)) {
            const el = document.getElementById(id);
            if (el) el.value = '';
        }

        m2mFields.forEach((name) => {
            document
                .querySelectorAll(`input[name="${name}"]`)
                .forEach((box) => {
                    box.checked = false;
                });
        });
    }

    // Listen for date changes
    dateInput.addEventListener('change', () => {
        const selectedDate = dateInput.value;

        clearFormErrors();

        if (!selectedDate) {
            clearForm(mapping);
            return;
        }

        // Fetch for data to update into Form
        fetch('/dashboard/ajax/load-log/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                date: dateInput.value,
            }),
        })
            .then((response) => response.json())
            .then((data) => {
                // Save DailyLog and IntercourseLog. values will be empty if the day has no log.

                setFormValues(mapping, data);

                setMultiple('symptoms', data.symptoms);
                setMultiple('moods', data.moods);
                setMultiple('medications', data.medications);
            })
            .catch((err) => {
                console.error('Error fetching log:', err);
            });
    });
});
