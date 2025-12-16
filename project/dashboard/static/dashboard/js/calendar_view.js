document.addEventListener("DOMContentLoaded", function () {
  const container = document.querySelector(".calendar-page-container");
  const ajaxLoadLogUrl = container.dataset.ajaxUrl;
  const addLogUrl = container.dataset.addLogUrl;
  const csrfToken = container.dataset.csrfToken;

  const dateCells = document.querySelectorAll("td[data-date]");
  const sidebar = document.getElementById("daily-view-sidebar");
  const content = document.getElementById("daily-view-content");
  const selectedDateDisplay = document.getElementById("selected-date-display");

  // Indicators
  const periodInd = document.getElementById("period-indicator");
  const ovulInd = document.getElementById("ovulation-indicator");

  // Log fields
  const logNote = document.getElementById("log-note");
  const logFlow = document.getElementById("log-flow");
  const logWeight = document.getElementById("log-weight");
  const logTemperature = document.getElementById("log-temp");
  const logOvulationTest = document.getElementById("log-ovulation-test");

  const logSymptoms = document.getElementById("log-symptoms");
  const logMoods = document.getElementById("log-moods");

  // Intercourse fields
  const logQuantity = document.getElementById("log-quantity");
  const logProtected = document.getElementById("log-protected");
  const logOrgasm = document.getElementById("log-orgasm");

  const noLogData = document.getElementById("no-log-data");
  const logData = document.getElementById("log-data");
  const addLogBtn = document.getElementById("add-log-btn");

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
        undefined,
        { weekday: "long", year: "numeric", month: "long", day: "numeric" }
      );

      // Open sidebar
      sidebar.classList.add("open");
      content.classList.remove("hidden");

      // Update Edit Link
      const returnUrl = encodeURIComponent(`${window.location.pathname}?date=${date}`);
      addLogBtn.href = `${addLogUrl}?date=${date}&next=${returnUrl}`;

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

          if (data.exists) {
            logData.classList.remove("hidden");
            noLogData.classList.add("hidden");

            logNote.textContent = data.note || "-";
            // Map flow int to string if needed, or backend sends display value?
            // Backend sends int currently. Let's just show it or map it simply.
            const flowMap = {
              0: "Spotting",
              1: "Light",
              2: "Medium",
              3: "Heavy",
            };
            logFlow.textContent =
              data.flow !== null ? flowMap[data.flow] || data.flow : "-";

            logWeight.textContent = data.weight || "-";
            logTemperature.textContent = data.temperature || "-";
            logOvulationTest.textContent = data.ovulation_test || "-";

            // Lists
            const populateList = (element, items) => {
              element.innerHTML = "";
              if (items && items.length > 0) {
                 items.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = item;
                    element.appendChild(li);
                 });
              }
            };

            populateList(logSymptoms, data.symptoms);
            populateList(logMoods, data.moods);

            // Intercourse
            logQuantity.textContent =
              data.quantity !== null ? data.quantity : "-";
            logProtected.textContent =
              data.protected !== null ? (data.protected ? "Yes" : "No") : "-";
            logOrgasm.textContent =
              data.orgasm !== null ? (data.orgasm ? "Yes" : "No") : "-";
          } else {
            logData.classList.add("hidden");
            noLogData.classList.remove("hidden");
          }
        });
    });
  });
});
