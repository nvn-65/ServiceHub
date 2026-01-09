// Основной JavaScript файл для ServiceHub

// Инициализация компонентов Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    // Включаем всплывающие подсказки
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Включаем всплывающие окна
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Автоматическое скрытие алертов через 5 секунд
    var alertList = document.querySelectorAll('.alert');
    alertList.forEach(function (alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});