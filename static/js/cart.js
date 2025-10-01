/**
 * Sweet Dreams Bakery - Cart JavaScript
 * Shopping cart functionality
 */

// Global cart variables
let cartData = {
    items: {},
    total: 0,
    count: 0,
    isUpdating: false
};

// DOM ready
$(document).ready(function() {
    initializeCart();
});

/**
 * Initialize cart functionality
 */
function initializeCart() {
    setupCartEventListeners();
    loadCartFromSession();
    updateCartDisplay();
    setupCartAnimations();
    
    console.log('🛒 Cart System Initialized');
}

/**
 * Setup cart event listeners
 */
function setupCartEventListeners() {
    // Quantity controls
    $(document).on('click', '.quantity-btn-increase', handleQuantityIncrease);
    $(document).on('click', '.quantity-btn-decrease', handleQuantityDecrease);
    $(document).on('change', '.quantity-display', handleQuantityChange);
    
    // Remove item buttons
    $(document).on('click', '.remove-from-cart', handleRemoveItem);
    
    // Add to cart buttons
    $(document).on('click', '.add-to-cart', function(e) {
        e.preventDefault();
        const btn = $(this);
        const productId = btn.data('product-id');
        const quantity = 1;
        $.ajax({
            url: '/add_to_cart',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                product_id: productId,
                quantity: quantity
            }),
            success: function(response) {
                if (response.success) {
                    $('#cart-badge').text(response.total_items).show();
                    showToast(response.message);
                } else {
                    showToast(response.message || 'เกิดข้อผิดพลาด', true);
                }
            }
        });
    });
    
    // Clear cart
    $('#clear-cart').on('click', handleClearCart);
    
    // Apply coupon
    $('#apply-coupon').on('click', handleApplyCoupon);
    
    // Checkout button
    $('.checkout-btn').on('click', handleCheckout);
    
    // Save for later
    $(document).on('click', '.save-for-later', handleSaveForLater);
    
    // Continue shopping
    $('.continue-shopping').on('click', handleContinueShopping);
}

/**
 * Handle quantity increase
 */
function handleQuantityIncrease() {
    if (cartData.isUpdating) return;
    
    const cartKey = $(this).data('cart-key');
    const quantityDisplay = $(`#quantity-${cartKey}`);
    const currentQuantity = parseInt(quantityDisplay.val()) || parseInt(quantityDisplay.text());
    const maxQuantity = parseInt(quantityDisplay.attr('max')) || 99;
    
    if (currentQuantity < maxQuantity) {
        const newQuantity = currentQuantity + 1;
        updateCartItemQuantity(cartKey, newQuantity);
    } else {
        showCartToast('ไม่สามารถเพิ่มได้อีก จำนวนสูงสุดคือ ' + maxQuantity, 'warning');
    }
}

/**
 * Handle quantity decrease
 */
function handleQuantityDecrease() {
    if (cartData.isUpdating) return;
    
    const cartKey = $(this).data('cart-key');
    const quantityDisplay = $(`#quantity-${cartKey}`);
    const currentQuantity = parseInt(quantityDisplay.val()) || parseInt(quantityDisplay.text());
    
    if (currentQuantity > 1) {
        const newQuantity = currentQuantity - 1;
        updateCartItemQuantity(cartKey, newQuantity);
    } else {
        // Ask if user wants to remove item
        const productName = $(this).data('product-name') || 'สินค้านี้';
        if (confirm(`ต้องการลบ ${productName} ออกจากตะกร้าหรือไม่?`)) {
            removeCartItem(cartKey);
        }
    }
}

/**
 * Handle direct quantity change
 */
function handleQuantityChange() {
    if (cartData.isUpdating) return;
    
    const cartKey = $(this).data('cart-key');
    const newQuantity = Math.max(1, Math.min(99, parseInt($(this).val()) || 1));
    
    // Update display to valid quantity
    $(this).val(newQuantity);
    
    updateCartItemQuantity(cartKey, newQuantity);

/**
 * Handle clear cart
 */
function handleClearCart() {
    if (cartData.isUpdating) return;
    
    if (!confirm('คุณต้องการเคลียร์สินค้าทั้งหมดในตะกร้าหรือไม่?')) {
        return;
    }
    
    clearCart().then(response => {
        if (response.success) {
            showCartToast('เคลียร์ตะกร้าเรียบร้อยแล้ว', 'info');
            setTimeout(() => location.reload(), 1500);
        }
    });
}

/**
 * Handle apply coupon
 */
function handleApplyCoupon() {
    const couponCode = $('#coupon-code').val().trim();
    
    if (!couponCode) {
        showCartToast('กรุณาใส่รหัสคูปอง', 'warning');
        return;
    }
    
    // Show loading
    const button = $(this);
    const originalText = button.html();
    button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>ตรวจสอบ...');
    
    // Simulate coupon validation
    setTimeout(() => {
        // Demo coupon codes
        const validCoupons = {
            'SWEET10': { discount: 10, type: 'percent', message: 'ส่วนลด 10%' },
            'NEWBIE50': { discount: 50, type: 'fixed', message: 'ส่วนลด 50 บาท' },
            'FREESHIP': { discount: 0, type: 'freeship', message: 'ฟรีค่าจัดส่ง' }
        };
        
        if (validCoupons[couponCode.toUpperCase()]) {
            const coupon = validCoupons[couponCode.toUpperCase()];
            applyCoupon(coupon);
            showCartToast(`ใช้คูปอง ${couponCode} สำเร็จ - ${coupon.message}`, 'success');
        } else {
            showCartToast('รหัสคูปองไม่ถูกต้อง', 'error');
        }
        
        button.prop('disabled', false).html(originalText);
    }, 1500);
}

/**
 * Handle checkout
 */
function handleCheckout() {
    if (cartData.isUpdating) return;
    
    if (cartData.count === 0) {
        showCartToast('ตะกร้าสินค้าว่าง', 'warning');
        return;
    }
    
    // Check stock availability
    if (!validateCartStock()) {
        return;
    }
    
    // Proceed to checkout
    window.location.href = '/checkout';
}

/**
 * Show toast message
 */
function showToast(message, isError) {
    const toast = $('#toast');
    toast.find('.toast-body').text(message);
    toast.removeClass('bg-danger bg-success');
    toast.addClass(isError ? 'bg-danger' : 'bg-success');
    toast.toast({ delay: 2500 });
    toast.toast('show');
}
