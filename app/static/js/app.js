const root = document.documentElement;
const themeToggle = document.getElementById("themeToggle");
const storedTheme = localStorage.getItem("uat-theme");

if (storedTheme) {
    root.setAttribute("data-bs-theme", storedTheme);
}

if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        const nextTheme = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
        root.setAttribute("data-bs-theme", nextTheme);
        localStorage.setItem("uat-theme", nextTheme);
    });
}

const roleSelect = document.getElementById("roleSelect");
const linkedStudentWrapper = document.getElementById("linkedStudentWrapper");

function toggleLinkedStudentField() {
    if (!roleSelect || !linkedStudentWrapper) {
        return;
    }
    linkedStudentWrapper.style.display = roleSelect.value === "parent" ? "block" : "none";
}

if (roleSelect) {
    toggleLinkedStudentField();
    roleSelect.addEventListener("change", toggleLinkedStudentField);
}

const chartCanvas = document.getElementById("performanceChart");
if (chartCanvas && window.performanceChartData) {
    new Chart(chartCanvas, {
        type: "line",
        data: {
            labels: window.performanceChartData.labels,
            datasets: [
                {
                    label: "Average Grade Point",
                    data: window.performanceChartData.values,
                    borderColor: "#0d6efd",
                    backgroundColor: "rgba(13, 110, 253, 0.18)",
                    borderWidth: 3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.35,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 4
                }
            }
        }
    });
}

const gpaCanvas = document.getElementById("gpaChart");
if (gpaCanvas && window.gpaChartData) {
    new Chart(gpaCanvas, {
        type: "bar",
        data: {
            labels: window.gpaChartData.labels,
            datasets: [
                {
                    label: "Semester GPA",
                    data: window.gpaChartData.values,
                    backgroundColor: ["#2fb380", "#0d6efd", "#ffc107", "#dc3545", "#6f42c1", "#20c997"]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 4
                }
            }
        }
    });
}
