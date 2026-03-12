(function () {
    const root = document.documentElement;
    const body = document.body;

    function getCsrfToken() {
        return body.dataset.csrfToken || '';
    }

    function applySiteFont(fontName) {
        const nextFont = fontName === 'choco-recipes' ? 'choco-recipes' : 'choco-chips';
        root.dataset.siteFont = nextFont;
        localStorage.setItem('site-font', nextFont);
        document.querySelectorAll('[data-font-choice]').forEach((button) => {
            button.setAttribute('aria-pressed', String(button.dataset.fontChoice === nextFont));
        });
    }

    function updateCartBadge(cartCount) {
        const badge = document.getElementById('cart-badge');
        if (badge) {
            badge.innerText = cartCount;
            return;
        }
        window.location.reload();
    }

    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-8 left-1/2 transform -translate-x-1/2 bg-darkgray text-white px-6 py-3 rounded-full text-sm font-medium shadow-xl opacity-0 transition-opacity duration-300 z-50';
        toast.innerText = message;
        document.body.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.remove('opacity-0');
        });

        setTimeout(() => {
            toast.classList.add('opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    async function postJson(url, payload) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify(payload),
        });
        return response.json();
    }

    function autoHideFlashMessages() {
        setTimeout(() => {
            const flashes = document.querySelectorAll('#flash-messages > div');
            flashes.forEach((element) => {
                element.style.opacity = '0';
                setTimeout(() => element.remove(), 300);
            });
        }, 5000);
    }

    document.addEventListener('click', (event) => {
        const toggleButton = event.target.closest('[data-font-choice]');
        if (toggleButton) {
            applySiteFont(toggleButton.dataset.fontChoice);
        }
    });

    applySiteFont(localStorage.getItem('site-font') || root.dataset.siteFont);
    autoHideFlashMessages();

    window.ValitaSite = {
        getCsrfToken,
        postJson,
        showToast,
        updateCartBadge,
    };
})();
