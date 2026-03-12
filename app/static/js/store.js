(function () {
    function initHomePage() {
        const layers = document.querySelectorAll('.parallax-layer');
        if (!layers.length) {
            return;
        }

        let scrollY = 0;
        let mouseX = 0;
        let mouseY = 0;
        let ticking = false;

        function updateParallax() {
            const centerX = window.innerWidth / 2;
            const centerY = window.innerHeight / 2;

            layers.forEach((layer) => {
                const speedX = parseFloat(layer.getAttribute('data-speed-x'));
                const speedY = parseFloat(layer.getAttribute('data-speed-y'));
                const x = (mouseX - centerX) * speedX;
                const y = (mouseY - centerY) * speedY - (scrollY * speedY * 1.5);
                layer.style.transform = `translate3d(${x}px, ${y}px, 0)`;
            });

            ticking = false;
        }

        window.addEventListener('scroll', () => {
            scrollY = window.scrollY;
            if (!ticking) {
                window.requestAnimationFrame(updateParallax);
                ticking = true;
            }
        });

        window.addEventListener('mousemove', (event) => {
            mouseX = event.clientX;
            mouseY = event.clientY;
            if (!ticking) {
                window.requestAnimationFrame(updateParallax);
                ticking = true;
            }
        });

        updateParallax();
    }

    async function addToCart(productId, quantity) {
        const data = await window.ValitaSite.postJson('/carrito/agregar', {
            product_id: productId,
            quantity: quantity,
        });

        if (!data.success) {
            return;
        }

        window.ValitaSite.updateCartBadge(data.cart_count);
        window.ValitaSite.showToast('¡Agregado al carrito!');
    }

    function updateQuantity(delta) {
        const input = document.getElementById('qty');
        if (!input) {
            return;
        }

        const currentValue = parseInt(input.value, 10) || 1;
        const min = parseInt(input.min || '1', 10);
        const max = input.max ? parseInt(input.max, 10) : Number.MAX_SAFE_INTEGER;
        input.value = Math.min(max, Math.max(min, currentValue + delta));
    }

    window.ValitaStore = {
        addToCart,
        updateQuantity,
    };

    document.addEventListener('DOMContentLoaded', () => {
        if (document.body.dataset.page === 'store-home') {
            initHomePage();
        }
    });
})();
