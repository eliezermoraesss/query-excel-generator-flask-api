const themeStorageKey = "query-generator-theme";
const darkThemeLabel = "Tema branco";
const lightThemeLabel = "Tema escuro";

function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.setAttribute("data-bs-theme", theme);

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
        const isDark = theme === "dark";
        button.textContent = isDark ? darkThemeLabel : lightThemeLabel;
        button.setAttribute("aria-pressed", String(isDark));
    });
}

function setupThemeToggle() {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
    applyTheme(currentTheme);

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
        if (button.dataset.themeBound === "true") {
            return;
        }

        button.dataset.themeBound = "true";
        button.addEventListener("click", () => {
            const activeTheme = document.documentElement.getAttribute("data-theme") || "dark";
            const nextTheme = activeTheme === "dark" ? "light" : "dark";
            localStorage.setItem(themeStorageKey, nextTheme);
            applyTheme(nextTheme);
        });
    });
}

window.applyTheme = applyTheme;
window.setupThemeToggle = setupThemeToggle;

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupThemeToggle);
} else {
    setupThemeToggle();
}
