(function () {
    async function updateCartItem(productId, newQty) {
        if (newQty <= 0) {
            removeCartItem(productId);
            return;
        }

        const data = await window.ValitaSite.postJson('/carrito/actualizar', {
            product_id: productId,
            quantity: newQty,
        });

        if (data.success) {
            window.location.reload();
        }
    }

    async function removeCartItem(productId) {
        const data = await window.ValitaSite.postJson('/carrito/eliminar', {
            product_id: productId,
        });

        if (data.success) {
            window.location.reload();
        }
    }

    window.ValitaCart = {
        updateCartItem,
        removeCartItem,
    };
})();
