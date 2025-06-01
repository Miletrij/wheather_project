$("#city").on("keydown", function(e) {
    var items = $("#autocomplete-list div");
    if (items.length === 0) return;

    if (e.keyCode == 40) { // Стрелка вниз
        e.preventDefault();
        currentFocus = currentFocus >= items.length - 1 ? 0 : currentFocus + 1;
        setActive(items);
    } else if (e.keyCode == 38) { // Стрелка вверх
        e.preventDefault();
        currentFocus = currentFocus <= 0 ? items.length - 1 : currentFocus - 1;
        setActive(items);
    } else if (e.keyCode == 13) { // Enter
        e.preventDefault();
        if (currentFocus > -1) {
            $(items[currentFocus]).click();
        }
    }
});

function setActive(items) {
    items.removeClass("active");
    if (currentFocus >= 0) {
        $(items[currentFocus]).addClass("active");
        $(items[currentFocus])[0].scrollIntoView({
            block: 'nearest'
        });
    }
}