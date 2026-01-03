document.addEventListener("DOMContentLoaded", function () {
  const container = document.querySelector(".calendar-page-container");
  const ajaxLoadLogUrl = container.dataset.ajaxUrl;
  const addLogUrl = container.dataset.addLogUrl;
  const csrfToken = container.dataset.csrfToken;
  const languageCode = container.dataset.languageCode;

  const dateCells = document.querySelectorAll("td[data-date]");
  const sidebar = document.getElementById("daily-view-sidebar");
  const content = document.getElementById("daily-view-content");
  const selectedDateDisplay = document.getElementById("selected-date-display");

  // Indicators
  const periodInd = document.getElementById("period-indicator");
  const ovulInd = document.getElementById("ovulation-indicator");

  // Form Elements
  const sidebarForm = document.getElementById("sidebar-log-form");
  const selectedDateInput = document.getElementById("selected-date-input");
  const saveBtn = document.getElementById("sidebar-save-btn");

  dateCells.forEach((cell) => {
    cell.addEventListener("click", function () {
      const date = this.getAttribute("data-date");
      if (!date) return;

      // Highlight selection
      document
        .querySelectorAll(".selected-date")
        .forEach((el) => el.classList.remove("selected-date"));
      this.classList.add("selected-date");

      selectedDateDisplay.textContent = new Date(date).toLocaleDateString(
        languageCode,
        { weekday: "long", year: "numeric", month: "long", day: "numeric" }
      );

      // Open sidebar
      sidebar.classList.add("open");
      content.classList.remove("hidden");

      // Set hidden date input
      selectedDateInput.value = date;

      // Fetch data
      fetch(ajaxLoadLogUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ date: date }),
      })
        .then((response) => response.json())
        .then((data) => {
          // Update Indicators
          periodInd.classList.toggle("hidden", !data.is_period);
          ovulInd.classList.toggle("hidden", !data.is_ovulation);

          // Populate Form Fields
          // Text/Select inputs
          setFieldValue("note", data.note);
          setFieldValue("flow", data.flow);
          setFieldValue("weight", data.weight);
          setFieldValue("temperature", data.temperature);
          setFieldValue("ovulation_test", data.ovulation_test);
          
          setFieldValue("quantity", data.quantity);

          // Checkboxes (Groups)
          setCheckboxGroup("symptoms", data.symptoms);
          setCheckboxGroup("moods", data.moods);
          setCheckboxGroup("medications", data.medications);

          // Single Checkboxes (Intercourse)
          setCheckbox("protected", data.protected);
          setCheckbox("orgasm", data.orgasm);
        });
    });
  });

  // Helper to set value of input by name
  function setFieldValue(name, value) {
      const input = sidebarForm.querySelector(`[name="${name}"]`);
      if (input) {
          input.value = (value === null || value === undefined) ? "" : value;
      }
  }

  // Helper for multiple choice checkboxes (name="symptoms")
  function setCheckboxGroup(name, activeIds) {
      const checkboxes = sidebarForm.querySelectorAll(`input[name="${name}"]`);
      checkboxes.forEach(cb => {
          // activeIds is array of ints, cb.value is string
          cb.checked = activeIds.includes(parseInt(cb.value));
      });
  }

  // Helper for single boolean checkboxes
  function setCheckbox(name, isChecked) {
      const input = sidebarForm.querySelector(`input[name="${name}"]`);
      if (input) {
          input.checked = !!isChecked;
      }
  }

  // Save Handler
  if (saveBtn) {
      saveBtn.addEventListener("click", function(e) {
          e.preventDefault();
          
          // Basic UI feedback
          const originalText = saveBtn.textContent;
          saveBtn.textContent = "Saving...";
          saveBtn.disabled = true;

          const formData = new FormData(sidebarForm);
          
          // Since we are posting to a standard view that might redirect, 
          // we can check if we want to handle it purely via fetch or allow form submission.
          // For now, let's use fetch and reload to ensure state consistency (calendars re-render).
          
          fetch(sidebarForm.action, {
              method: "POST",
              body: formData,
              headers: {
                "X-CSRFToken": csrfToken,
              },
          }).then(response => {
              // If success, reload to update calendar colors (simple approach)
              // Or if we returned JSON, we could update UI locally.
              // Given the backend returns a redirect, fetch follows it and returns the HTML of the new page.
              // We can just reload the window.
              window.location.reload();
          }).catch(err => {
              console.error("Error saving log:", err);
              alert("Error saving log.");
              saveBtn.textContent = originalText;
              saveBtn.disabled = false;
          });
      });
  }

});
