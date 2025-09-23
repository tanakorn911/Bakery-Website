/**
 * Sweet Dreams Bakery - Main JavaScript
 * Handles cart management, AJAX requests, and UI interactions
 */

// Global variables
let cart = {};
let isLoading = false;

// DOM Content Loaded
$(document).ready(function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    setupEventListeners();
    initializeAnimations();
    updateCartBadge();
    
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Auto-hide flash messages
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
    
    console.log('🍰 Sweet Dreams Bakery - Application Initialized');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Add to cart buttons
    $(document).on('click', '.add-to-cart', handleAddToCart);
    
    // Quantity update buttons
    $(document).on('click', '.quantity-btn', handleQuantityUpdate);
    
    // Remove from cart buttons
    $(document).on('click', '.remove-from-cart', handleRemoveFromCart);
    
    // Quick view product
    $(document).on('click', '.quick-view', handleQuickView);
    
    // Search functionality
    $('#search-input').on('input', debounce(handleSearch, 300));
    
    // Category filter
    $('.category-filter').on('click', handleCategoryFilter);
    
    // Smooth scroll for anchor links
    $('a[href^="#"]').on('click', handleSmoothScroll);
    
    // Form validation
    $('form').on('submit', handleFormValidation);
    
    // Loading overlay
    $(document).on('ajaxStart', showLoading).on('ajaxStop', hideLoading);
}

/**
 * Initialize animations
 */
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    $('.product-card, .feature-card').each(function() {
        observer.observe(this);
    });
}

/**
 * Handle add to cart
 */
function handleAddToCart(e) {
    e.preventDefault();
    
    if (isLoading) return;
    
    const button = $(this);
    const productId = button.data('product-id');
    const productName = button.data('product-name');
    const productPrice = button.data('product-price');
    const quantity = parseInt($(`#quantity-${productId}`).val()) || 1;
    
    // Check for product options (if applicable)
    let options = '';
    const optionModal = $(`#optionModal-${productId}`);
    if (optionModal.length && optionModal.is(':visible')) {
        options = optionModal.find('select').val();
    }
    
    // Prepare data
    const data = {
        product_id: productId,
        quantity: quantity,
        options: options
    };
    
    // Show loading state
    const originalText = button.html();
    button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>กำลังเพิ่ม...');
    
    // Send AJAX request
    $.ajax({
        url: '/add_to_cart',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function(response) {
            if (response.success) {
                // Update cart badge
                updateCartBadge(response.total_items);
                
                // Show success toast
                showToast(response.message, 'success');
                
                // Add animation to cart icon
                animateCartIcon();
                
                // Close option modal if open
                optionModal.modal('hide');
                
            } else {
                showToast(response.message, 'error');
            }
        },
        error: function() {
            showToast('เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง', 'error');
        },
        complete: function() {
            // Restore button
            button.prop('disabled', false).html(originalText);
        }
    });
}

/**
 * Handle quantity update
 */
function handleQuantityUpdate(e) {
    e.preventDefault();
    
    if (isLoading) return;
    
    const button = $(this);
    const action = button.data('action'); // 'increase' or 'decrease'
    const cartKey = button.data('cart-key');
    const quantityDisplay = $(`#quantity-${cartKey}`);
    const currentQuantity = parseInt(quantityDisplay.text());
    
    let newQuantity = currentQuantity;
    if (action === 'increase') {
        newQuantity++;
    } else if (action === 'decrease') {
        newQuantity = Math.max(0, currentQuantity - 1);
    }
    
    // If quantity is 0, remove item
    if (newQuantity === 0) {
        handleRemoveFromCart(e);
        return;
    }
    
    // Update quantity
    updateCartQuantity(cartKey, newQuantity);
}

/**
 * Update cart quantity
 */
function updateCartQuantity(cartKey, quantity) {
    const data = {
        cart_key: cartKey,
        quantity: quantity
    };
    
    $.ajax({
        url: '/update_cart',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function(response) {
            if (response.success) {
                // Update quantity display
                $(`#quantity-${cartKey}`).text(quantity);
                
                // Update item total
                const itemPrice = parseFloat($(`[data-cart-key="${cartKey}"]`).data('price'));
                const itemTotal = itemPrice * quantity;
                $(`#total-${cartKey}`).text(formatPrice(itemTotal));
                
                // Update cart totals
                updateCartTotals(response.total_items, response.total_price);
                
                // Show toast
                showToast('อัพเดทจำนวนสินค้าแล้ว', 'success');
                
            } else {
                showToast(response.message, 'error');
            }
        },
        error: function() {
            showToast('เกิดข้อผิดพลาด', 'error');
        }
    });
}

/**
 * Handle remove from cart
 */
function handleRemoveFromCart(e) {
    e.preventDefault();
    
    if (isLoading) return;
    
    const button = $(this);
    const cartKey = button.data('cart-key');
    const productName = button.data('product-name') || 'สินค้า';
    
    // Confirm removal
    if (!confirm(`ต้องการลบ ${productName} ออกจากตะกร้าหรือไม่?`)) {
        return;
    }
    
    const data = {
        cart_key: cartKey
    };
    
    $.ajax({
        url: '/remove_from_cart',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function(response) {
            if (response.success) {
                // Remove item with animation
                const cartItem = $(`[data-cart-key="${cartKey}"]`);
                cartItem.fadeOut(300, function() {
                    cartItem.remove();
                    
                    // Check if cart is empty
                    if (response.total_items === 0) {
                        setTimeout(() => location.reload(), 1000);
                    }
                });
                
                // Update cart totals
                updateCartTotals(response.total_items, response.total_price);
                
                // Show toast
                showToast(`ลบ ${productName} ออกจากตะกร้าแล้ว`, 'success');
                
            } else {
                showToast(response.message, 'error');
            }
        },
        error: function() {
            showToast('เกิดข้อผิดพลาด', 'error');
        }
    });
}

/**
 * Handle quick view
 */
function handleQuickView(e) {
    e.preventDefault();
    
    const productId = $(this).data('product-id');
    
    // For now, redirect to product detail page
    // In future, could open a modal with product details
    window.location.href = `/product/${productId}`;
}

/**
 * Handle search
 */
function handleSearch() {
    const query = $('#search-input').val().toLowerCase();
    
    if (query.length === 0) {
        $('.product-card').show();
        return;
    }
    
    $('.product-card').each(function() {
        const productName = $(this).find('.product-name').text().toLowerCase();
        const productDescription = $(this).find('.product-description').text().toLowerCase();
        
        if (productName.includes(query) || productDescription.includes(query)) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}

/**
 * Handle category filter
 */
function handleCategoryFilter(e) {
    e.preventDefault();
    
    const category = $(this).data('category');
    
    // Update active state
    $('.category-filter').removeClass('active');
    $(this).addClass('active');
    
    if (category === 'all') {
        $('.product-card').show();
    } else {
        $('.product-card').each(function() {
            const productCategory = $(this).data('category');
            if (productCategory === category) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    }
}

/**
 * Handle smooth scroll
 */
function handleSmoothScroll(e) {
    const target = $(this).attr('href');
    
    if (target.startsWith('#')) {
        e.preventDefault();
        
        const targetElement = $(target);
        if (targetElement.length) {
            $('html, body').animate({
                scrollTop: targetElement.offset().top - 100
            }, 800);
        }
    }
}

/**
 * Handle form validation
 */
function handleFormValidation(e) {
    const form = $(this);
    
    // Basic validation
    let isValid = true;
    
    form.find('input[required], select[required], textarea[required]').each(function() {
        const field = $(this);
        const value = field.val().trim();
        
        if (!value) {
            field.addClass('is-invalid');
            isValid = false;
        } else {
            field.removeClass('is-invalid').addClass('is-valid');
        }
    });
    
    // Email validation
    form.find('input[type="email"]').each(function() {
        const email = $(this).val();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (email && !emailRegex.test(email)) {
            $(this).addClass('is-invalid');
            isValid = false;
        }
    });
    
    // Phone validation (Thai format)
    form.find('input[type="tel"]').each(function() {
        const phone = $(this).val();
        const phoneRegex = /^[0-9]{9,10}$/;
        
        if (phone && !phoneRegex.test(phone.replace(/[-\s]/g, ''))) {
            $(this).addClass('is-invalid');
            isValid = false;
        }
    });
    
    if (!isValid) {
        e.preventDefault();
        showToast('กรุณากรอกข้อมูลให้ครบถ้วน', 'warning');
        
        // Focus on first invalid field
        form.find('.is-invalid:first').focus();
    }
}

/**
 * Update cart badge
 */
function updateCartBadge(totalItems = null) {
    const badge = $('#cart-badge');
    
    if (totalItems !== null) {
        if (totalItems > 0) {
            badge.text(totalItems).show();
        } else {
            badge.hide();
        }
    }
}

/**
 * Update cart totals
 */
function updateCartTotals(totalItems, totalPrice) {
    $('#total-items').text(`${totalItems} ชิ้น`);
    $('#total-price').text(formatPrice(totalPrice));
    updateCartBadge(totalItems);
}

/**
 * Animate cart icon
 */
function animateCartIcon() {
    const cartIcon = $('.cart-link i');
    cartIcon.addClass('fa-bounce');
    
    setTimeout(() => {
        cartIcon.removeClass('fa-bounce');
    }, 1000);
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = $('#toast');
    const toastBody = toast.find('.toast-body');
    
    // Set message and type
    toastBody.text(message);
    
    // Remove existing type classes
    toast.removeClass('toast-success toast-error toast-warning toast-info');
    
    // Add appropriate class
    toast.addClass(`toast-${type}`);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast[0], {
        autohide: true,
        delay: 4000
    });
    
    bsToast.show();
}

/**
 * Show/Hide loading overlay
 */
function showLoading() {
    if (!isLoading) {
        isLoading = true;
        $('#loading-overlay').removeClass('d-none');
    }
}

function hideLoading() {
    setTimeout(() => {
        isLoading = false;
        $('#loading-overlay').addClass('d-none');
    }, 300);
}

/**
 * Format price
 */
function formatPrice(price) {
    return new Intl.NumberFormat('th-TH', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(price) + ' บาท';
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Format number with commas
 */
function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Validate Thai phone number
 */
function validateThaiPhone(phone) {
    const cleaned = phone.replace(/[-\s]/g, '');
    return /^[0-9]{9,10}$/.test(cleaned);
}

/**
 * Get Thai date format
 */
function getThaiDate(date = new Date()) {
    return date.toLocaleDateString('th-TH', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            return successful;
        } catch (err) {
            document.body.removeChild(textArea);
            return false;
        }
    }
}

/**
 * Local Storage Helper (with fallback)
 */
const StorageHelper = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.warn('LocalStorage not available:', e);
            return false;
        }
    },
    
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.warn('LocalStorage not available:', e);
            return defaultValue;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.warn('LocalStorage not available:', e);
            return false;
        }
    }
};

/**
 * Image lazy loading
 */
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

/**
 * Back to top button
 */
function initBackToTop() {
    const backToTopBtn = $('<button>')
        .attr('id', 'back-to-top')
        .addClass('btn btn-primary position-fixed')
        .css({
            'bottom': '20px',
            'right': '20px',
            'z-index': '1000',
            'border-radius': '50%',
            'width': '50px',
            'height': '50px',
            'display': 'none'
        })
        .html('<i class="fas fa-arrow-up"></i>')
        .appendTo('body');

    $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
            backToTopBtn.fadeIn();
        } else {
            backToTopBtn.fadeOut();
        }
    });

    backToTopBtn.click(function() {
        $('html, body').animate({scrollTop: 0}, 800);
        return false;
    });
}

/**
 * Initialize on DOM ready
 */
$(document).ready(function() {
    initLazyLoading();
    initBackToTop();
});

/**
 * Service Worker Registration (if available)
 */
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('SW registered: ', registration);
            })
            .catch(function(registrationError) {
                console.log('SW registration failed: ', registrationError);
            });
    });
}

/**
 * Export functions for global use
 */
window.BakeryApp = {
    showToast,
    showLoading,
    hideLoading,
    formatPrice,
    updateCartBadge,
    copyToClipboard,
    StorageHelper,
    validateThaiPhone,
    getThaiDate
};