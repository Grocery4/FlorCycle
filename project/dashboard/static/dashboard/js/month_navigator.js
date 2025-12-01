document.addEventListener("DOMContentLoaded", () => {
    const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    const buttonInputs = document.querySelectorAll(".nav_btn");

    function setNewCalendars(new_calendars){
        const calElements = document.querySelectorAll(".cal");
        new_calendars.forEach((new_cal, index) => {
            if (calElements[index]) {
                calElements[index].innerHTML = new_cal;
            }
        });

        document.dispatchEvent(new Event('calendars-updated'));
    };

    buttonInputs.forEach(button => {
        button.addEventListener("click", () => {
            buttonType = button.id;
            fetch("/dashboard/ajax/navigate-calendar/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken,
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: JSON.stringify({
                    reference_month: window.referenceMonth,
                    button_type: buttonType
                })
            })
            .then(response => response.json())
            .then(data => {
                setNewCalendars(data.calendars);
                window.referenceMonth = data.reference_month;
                
                document.getElementById('mo_start').innerHTML = data.rendered_month_start;
                document.getElementById('mo_end').innerHTML = data.rendered_month_end;
            })
        })
    });
})