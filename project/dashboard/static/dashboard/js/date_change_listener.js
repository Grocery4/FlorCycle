const dateInput = document.getElementById("id_date");
let originalValue = dateInput.value;

dateInput.addEventListener("change", () => {
    if (dateInput.value !== originalValue) {
        console.log("Date changed!");
    }
});