document.addEventListener('click', function (event) {
    const slide = event.target.closest('.js_href-on-click');
    if (!slide) {
        return;
    }

    const link = slide.querySelector(
        '.js_href-on-click__data[data-external-link="true"]',
    );
    if (!link || !link.dataset.href) {
        return;
    }

    event.preventDefault();
    event.stopImmediatePropagation();

    const newWindow = window.open(link.dataset.href, '_blank', 'noopener');
    if (newWindow) {
        newWindow.opener = null;
    }
}, true);
