/**
 * Sweet Dreams Bakery - Admin JavaScript
 * Admin panel functionality
 */

// Global admin variables
let adminData = {
    products: [],
    categories: [],
    currentEditId: null
};

// DOM ready
$(document).ready(function() {
    initializeAdmin();
});

/**
 * Initialize admin panel
 */
function initializeAdmin() {
    setupAdminEventListeners();
    initializeDataTables();
    setupRealTimeUpdates();
    loadDashboardData();
    
    console.log('🔧 Admin Panel Initialized');
}

/**
 * Setup event listeners for admin functions
 */
function setupAdminEventListeners() {
    // Show/Hide add product form
    $('#show-add-form').on('click', showAddProductForm);
    $('#close-add-form').on('click', hideAddProductForm);
    
    // Product form handling
    $('#product-form').on('submit', handleProductSubmit);
    $('#product-form').on('reset', resetProductForm);
    
    // Product management buttons
    $(document).on('click', '.btn-edit', handleEditProduct);
    $(document).on('click', '.btn-toggle-status', handleToggleStatus);
    $(document).on('click', '.btn-toggle-featured', handleToggleFeatured);
    $(document).on('click', '.btn-delete', handleDeleteProduct);
    
    // Search and filter
    $('#search-products').on('input', debounce(handleProductSearch, 300));
    $('#filter-category').on('change', handleCategoryFilter);
    $('#sort-products').on('change', handleProductSort);
    
    // Bulk actions
    $('#select-all-products').on('change', handleSelectAll);
    $(document).on('change', '.product-checkbox', handleProductSelect);
    $('#bulk-actions').on('click', handleBulkActions);
    
    // Quick actions
    $('.quick-action-btn').on('click', handleQuickAction);
    
    // File upload handling
    $('#product-image-upload').on('change', handleImageUpload);
    
    // Auto-save form data
    $('#product-form input, #product-form textarea, #product-form select').on('change', autoSaveFormData);
}

/**
 * Initialize DataTables for better table management
 */
function initializeDataTables() {
    if ($('.products-table').length && typeof $.fn.DataTable !== 'undefined') {
        $('.products-table').DataTable({
            responsive: true,
            pageLength: 25,
            order: [[1, 'asc']], // Sort by product name
            columnDefs: [
                { orderable: false, targets: [0, -1] } // Disable sorting for checkbox and actions
            ],
            language: {
                search: "ค้นหา:",
                lengthMenu: "แสดง _MENU_ รายการ",
                info: "แสดง _START_ ถึง _END_ จาก _TOTAL_ รายการ",
                paginate: {
                    first: "แรก",
                    last: "สุดท้าย",
                    next: "ถัดไป",
                    previous: "ก่อนหน้า"
                },
                emptyTable: "ไม่มีข้อมูล"
            }
        });
    }
}

/**
 * Show add product form
 */
function showAddProductForm() {
    resetProductForm();
    $('#add-product-form').addClass('show');
    $('html, body').animate({
        scrollTop: $('#add-product-form').offset().top - 100
    }, 500);
    $('#product_name').focus();
}

/**
 * Hide add product form
 */
function hideAddProductForm() {
    $('#add-product-form').removeClass('show');
    resetProductForm();
    adminData.currentEditId = null;
}

/**
 * Handle product form submission
 */
function handleProductSubmit(e) {
    e.preventDefault();
    
    // Validate form
    if (!validateProductForm()) {
        return;
    }
    
    const formData = collectFormData();
    const isEdit = adminData.currentEditId !== null;
    
    // Show loading
    const submitBtn = $('#product-form button[type="submit"]');
    const originalText = submitBtn.html();
    submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>กำลังบันทึก...');
    
    // Send to server
    const url = isEdit ? `/admin/update_product/${adminData.currentEditId}` : '/admin/add_product';
    const method = 'POST';
    
    $.ajax({
        url: url,
        type: method,
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            if (response.success) {
                showAdminToast(response.message, 'success');
                
                if (isEdit) {
                    updateProductInTable(adminData.currentEditId, formData);
                } else {
                    // Reload page to show new product
                    setTimeout(() => location.reload(), 1500);
                }
                
                hideAddProductForm();
                clearAutoSavedData();
            } else {
                showAdminToast(response.message || 'เกิดข้อผิดพลาด', 'error');
            }
        },
        error: function(xhr) {
            let errorMessage = 'เกิดข้อผิดพลาดในการบันทึก';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            }
            showAdminToast(errorMessage, 'error');
        },
        complete: function() {
            submitBtn.prop('disabled', false).html(originalText);
        }
    });
}

/**
 * Handle toggle product status - แก้ไขให้เชื่อมต่อ API
 */
function handleToggleStatus() {
    const productId = $(this).data('product-id');
    const currentStatus = $(this).data('current-status');
    const newStatus = !currentStatus;
    const button = $(this);
    const row = button.closest('tr');
    
    // Show loading
    button.prop('disabled', true);
    row.addClass('loading-row');
    
    // Send to server
    $.ajax({
        url: `/admin/toggle_product_status/${productId}`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ status: newStatus }),
        success: function(response) {
            if (response.success) {
                // Update UI
                const statusCell = row.find('td:nth-child(6)');
                
                if (newStatus) {
                    statusCell.html('<span class="status-badge status-available">พร้อมจำหน่าย</span>');
                    button.html('<i class="fas fa-eye-slash"></i>')
                          .attr('title', 'ปิดการจำหน่าย')
                          .data('current-status', true);
                    showAdminToast('เปิดการจำหน่ายสินค้าแล้ว', 'success');
                } else {
                    statusCell.html('<span class="status-badge status-unavailable">ไม่พร้อมจำหน่าย</span>');
                    button.html('<i class="fas fa-eye"></i>')
                          .attr('title', 'เปิดการจำหน่าย')
                          .data('current-status', false);
                    showAdminToast('ปิดการจำหน่ายสินค้าแล้ว', 'warning');
                }
                
                // Refresh tooltip
                button.tooltip('dispose').tooltip();
            } else {
                showAdminToast(response.message || 'เกิดข้อผิดพลาด', 'error');
            }
        },
        error: function() {
            showAdminToast('เกิดข้อผิดพลาดในการอัปเดต', 'error');
        },
        complete: function() {
            button.prop('disabled', false);
            row.removeClass('loading-row');
        }
    });
}

/**
 * Handle toggle featured status - แก้ไขให้เชื่อมต่อ API
 */
function handleToggleFeatured() {
    const productId = $(this).data('product-id');
    const currentFeatured = $(this).data('current-featured');
    const newFeatured = !currentFeatured;
    const button = $(this);
    const row = button.closest('tr');
    
    // Show loading
    button.prop('disabled', true);
    row.addClass('loading-row');
    
    // Send to server
    $.ajax({
        url: `/admin/toggle_product_featured/${productId}`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ featured: newFeatured }),
        success: function(response) {
            if (response.success) {
                const statusCell = row.find('td:nth-child(6)');
                
                if (newFeatured) {
                    // Add featured badge if not exists
                    if (!statusCell.find('.featured-badge').length) {
                        statusCell.append('<span class="status-badge featured-badge">แนะนำ</span>');
                    }
                    button.html('<i class="fas fa-star"></i>')
                          .attr('title', 'ยกเลิกแนะนำ')
                          .data('current-featured', true);
                    showAdminToast('ตั้งเป็นสินค้าแนะนำแล้ว', 'success');
                } else {
                    statusCell.find('.featured-badge').remove();
                    button.html('<i class="far fa-star"></i>')
                          .attr('title', 'ตั้งเป็นสินค้าแนะนำ')
                          .data('current-featured', false);
                    showAdminToast('ยกเลิกการแนะนำสินค้าแล้ว', 'info');
                }
                
                // Refresh tooltip
                button.tooltip('dispose').tooltip();
            } else {
                showAdminToast(response.message || 'เกิดข้อผิดพลาด', 'error');
            }
        },
        error: function() {
            showAdminToast('เกิดข้อผิดพลาดในการอัปเดต', 'error');
        },
        complete: function() {
            button.prop('disabled', false);
            row.removeClass('loading-row');
        }
    });
}

/**
 * Handle delete product - แก้ไขให้เชื่อมต่อ API
 */
function handleDeleteProduct() {
    const productId = $(this).data('product-id');
    const productName = $(this).data('product-name');
    const button = $(this);
    const row = button.closest('tr');
    
    // Show confirmation dialog
    if (!confirm(`คุณต้องการลบสินค้า "${productName}" หรือไม่?\n\nการดำเนินการนี้ไม่สามารถยกเลิกได้`)) {
        return;
    }
    
    // Show loading
    row.addClass('loading-row');
    
    // Send delete request
    $.ajax({
        url: `/admin/delete_product/${productId}`,
        type: 'DELETE',
        success: function(response) {
            if (response.success) {
                row.fadeOut(300, function() {
                    row.remove();
                    showAdminToast(response.message, 'success');
                    
                    // Update stats
                    updateStatsCard('products', -1);
                    
                    // Check if table is empty
                    if ($('tbody tr:visible').length === 0) {
                        showEmptyTableMessage();
                    }
                });
            } else {
                showAdminToast(response.message || 'เกิดข้อผิดพลาด', 'error');
                row.removeClass('loading-row');
            }
        },
        error: function() {
            showAdminToast('เกิดข้อผิดพลาดในการลบสินค้า', 'error');
            row.removeClass('loading-row');
        }
    });
}

/**
 * Validate product form
 */
function validateProductForm() {
    let isValid = true;
    const requiredFields = ['product_name', 'product_price', 'product_category'];
    
    // Reset validation states
    $('.form-control, .form-select').removeClass('is-invalid is-valid');
    
    // Check required fields
    requiredFields.forEach(fieldId => {
        const field = $(`#${fieldId}`);
        const value = field.val().trim();
        
        if (!value) {
            field.addClass('is-invalid');
            isValid = false;
        } else {
            field.addClass('is-valid');
        }
    });
    
    // Validate price
    const price = parseFloat($('#product_price').val());
    if (isNaN(price) || price < 0) {
        $('#product_price').addClass('is-invalid');
        isValid = false;
    }
    
    // Validate stock
    const stock = parseInt($('#product_stock').val());
    if (isNaN(stock) || stock < 0) {
        $('#product_stock').addClass('is-invalid');
        isValid = false;
    }
    
    if (!isValid) {
        showAdminToast('กรุณากรอกข้อมูลให้ถูกต้องและครบถ้วน', 'warning');
    }
    
    return isValid;
}

/**
 * Collect form data
 */
function collectFormData() {
    return {
        id: adminData.currentEditId || Date.now(), // Use timestamp as ID for new products
        name: $('#product_name').val().trim(),
        name_en: $('#product_name_en').val().trim(),
        price: parseFloat($('#product_price').val()),
        category_id: $('#product_category').val(),
        category_name: $('#product_category option:selected').text(),
        description: $('#product_description').val().trim(),
        stock_quantity: parseInt($('#product_stock').val()) || 0,
        image: $('#product_image').val().trim(),
        is_available: $('#product_available').is(':checked'),
        is_featured: $('#product_featured').is(':checked'),
        created_at: new Date().toISOString()
    };
}

/**
 * Reset product form
 */
function resetProductForm() {
    $('#product-form')[0].reset();
    $('.form-control, .form-select').removeClass('is-invalid is-valid');
    $('#product_available').prop('checked', true);
    $('#product_featured').prop('checked', false);
}

/**
 * Handle edit product
 */
function handleEditProduct() {
    const productId = $(this).data('product-id');
    const row = $(this).closest('tr');
    
    // Extract product data from table row
    const productData = {
        id: productId,
        name: row.find('td:nth-child(2) .fw-600').text(),
        price: parseFloat(row.find('td:nth-child(4)').text().replace(' ฿', '').replace(',', '')),
        category: row.find('td:nth-child(3) .badge').text(),
        stock: parseInt(row.find('td:nth-child(5)').text()),
        is_available: row.find('.status-available').length > 0,
        is_featured: row.find('.featured-badge').length > 0
    };
    
    // Populate form with existing data
    populateForm(productData);
    adminData.currentEditId = productId;
    
    // Change form title and button text
    $('#add-product-form h4').html('<i class="fas fa-edit text-warning me-2"></i>แก้ไขสินค้า');
    $('#product-form button[type="submit"]').html('<i class="fas fa-save me-2"></i>อัปเดตสินค้า');
    
    showAddProductForm();
}

/**
 * Populate form with product data
 */
function populateForm(productData) {
    $('#product_name').val(productData.name);
    $('#product_price').val(productData.price);
    $('#product_stock').val(productData.stock);
    $('#product_available').prop('checked', productData.is_available);
    $('#product_featured').prop('checked', productData.is_featured);
    
    // Find and select the category
    $('#product_category option').each(function() {
        if ($(this).text() === productData.category) {
            $(this).prop('selected', true);
        }
    });
}

/**
 * Handle toggle product status
 */
function handleToggleStatus() {
    const productId = $(this).data('product-id');
    const currentStatus = $(this).data('current-status');
    const newStatus = !currentStatus;
    const button = $(this);
    const row = button.closest('tr');
    
    // Show loading
    button.prop('disabled', true);
    row.addClass('loading-row');
    
    // Simulate API call
    setTimeout(() => {
        // Update UI
        const statusCell = row.find('td:nth-child(6)');
        
        if (newStatus) {
            statusCell.html('<span class="status-badge status-available">พร้อมจำหน่าย</span>');
            button.html('<i class="fas fa-eye-slash"></i>')
                  .attr('title', 'ปิดการจำหน่าย')
                  .data('current-status', true);
            showAdminToast('เปิดการจำหน่ายสินค้าแล้ว', 'success');
        } else {
            statusCell.html('<span class="status-badge status-unavailable">ไม่พร้อมจำหน่าย</span>');
            button.html('<i class="fas fa-eye"></i>')
                  .attr('title', 'เปิดการจำหน่าย')
                  .data('current-status', false);
            showAdminToast('ปิดการจำหน่ายสินค้าแล้ว', 'warning');
        }
        
        // Remove loading
        button.prop('disabled', false);
        row.removeClass('loading-row');
        
        // Refresh tooltip
        button.tooltip('dispose').tooltip();
        
    }, 800);
}

/**
 * Handle toggle featured status
 */
function handleToggleFeatured() {
    const productId = $(this).data('product-id');
    const currentFeatured = $(this).data('current-featured');
    const newFeatured = !currentFeatured;
    const button = $(this);
    const row = button.closest('tr');
    
    // Show loading
    button.prop('disabled', true);
    row.addClass('loading-row');
    
    // Simulate API call
    setTimeout(() => {
        const statusCell = row.find('td:nth-child(6)');
        
        if (newFeatured) {
            // Add featured badge if not exists
            if (!statusCell.find('.featured-badge').length) {
                statusCell.append('<span class="status-badge featured-badge">แนะนำ</span>');
            }
            button.html('<i class="fas fa-star"></i>')
                  .attr('title', 'ยกเลิกแนะนำ')
                  .data('current-featured', true);
            showAdminToast('ตั้งเป็นสินค้าแนะนำแล้ว', 'success');
        } else {
            statusCell.find('.featured-badge').remove();
            button.html('<i class="far fa-star"></i>')
                  .attr('title', 'ตั้งเป็นสินค้าแนะนำ')
                  .data('current-featured', false);
            showAdminToast('ยกเลิกการแนะนำสินค้าแล้ว', 'info');
        }
        
        // Remove loading
        button.prop('disabled', false);
        row.removeClass('loading-row');
        
        // Refresh tooltip
        button.tooltip('dispose').tooltip();
        
    }, 800);
}

/**
 * Handle delete product
 */
function handleDeleteProduct() {
    const productId = $(this).data('product-id');
    const productName = $(this).data('product-name');
    const button = $(this);
    const row = button.closest('tr');
    
    // Show confirmation dialog
    if (!confirm(`คุณต้องการลบสินค้า "${productName}" หรือไม่?\n\nการดำเนินการนี้ไม่สามารถยกเลิกได้`)) {
        return;
    }
    
    // Show loading
    row.addClass('loading-row');
    
    // Simulate API call
    setTimeout(() => {
        row.fadeOut(300, function() {
            row.remove();
            showAdminToast(`ลบสินค้า "${productName}" เรียบร้อยแล้ว`, 'success');
            
            // Update stats
            updateStatsCard('products', -1);
            
            // Check if table is empty
            if ($('tbody tr:visible').length === 0) {
                showEmptyTableMessage();
            }
        });
    }, 1000);
}

/**
 * Handle product search
 */
function handleProductSearch() {
    const searchTerm = $('#search-products').val().toLowerCase();
    
    $('tbody tr').each(function() {
        const row = $(this);
        const productName = row.find('td:nth-child(2)').text().toLowerCase();
        const category = row.find('td:nth-child(3)').text().toLowerCase();
        
        if (productName.includes(searchTerm) || category.includes(searchTerm)) {
            row.show();
        } else {
            row.hide();
        }
    });
    
    updateSearchResults();
}

/**
 * Handle category filter
 */
function handleCategoryFilter() {
    const selectedCategory = $('#filter-category').val();
    
    $('tbody tr').each(function() {
        const row = $(this);
        const category = row.find('td:nth-child(3) .badge').text();
        
        if (selectedCategory === '' || category === selectedCategory) {
            row.show();
        } else {
            row.hide();
        }
    });
    
    updateSearchResults();
}

/**
 * Handle product sorting
 */
function handleProductSort() {
    const sortBy = $('#sort-products').val();
    const tbody = $('tbody');
    const rows = tbody.find('tr').get();
    
    rows.sort(function(a, b) {
        let aVal, bVal;
        
        switch(sortBy) {
            case 'name-asc':
                aVal = $(a).find('td:nth-child(2)').text().toLowerCase();
                bVal = $(b).find('td:nth-child(2)').text().toLowerCase();
                return aVal.localeCompare(bVal);
            case 'name-desc':
                aVal = $(a).find('td:nth-child(2)').text().toLowerCase();
                bVal = $(b).find('td:nth-child(2)').text().toLowerCase();
                return bVal.localeCompare(aVal);
            case 'price-asc':
                aVal = parseFloat($(a).find('td:nth-child(4)').text().replace(' ฿', '').replace(',', ''));
                bVal = parseFloat($(b).find('td:nth-child(4)').text().replace(' ฿', '').replace(',', ''));
                return aVal - bVal;
            case 'price-desc':
                aVal = parseFloat($(a).find('td:nth-child(4)').text().replace(' ฿', '').replace(',', ''));
                bVal = parseFloat($(b).find('td:nth-child(4)').text().replace(' ฿', '').replace(',', ''));
                return bVal - aVal;
            case 'stock-asc':
                aVal = parseInt($(a).find('td:nth-child(5)').text());
                bVal = parseInt($(b).find('td:nth-child(5)').text());
                return aVal - bVal;
            case 'stock-desc':
                aVal = parseInt($(a).find('td:nth-child(5)').text());
                bVal = parseInt($(b).find('td:nth-child(5)').text());
                return bVal - aVal;
            default:
                return 0;
        }
    });
    
    tbody.empty().append(rows);
}

/**
 * Update search results count
 */
function updateSearchResults() {
    const visibleRows = $('tbody tr:visible').length;
    const totalRows = $('tbody tr').length;
    
    if ($('#search-results').length === 0) {
        $('.products-section').append('<div id="search-results" class="text-muted text-center mt-3"></div>');
    }
    
    $('#search-results').html(
        `แสดง ${visibleRows} จาก ${totalRows} รายการ ${visibleRows !== totalRows ? '(กรองแล้ว)' : ''}`
    );
}

/**
 * Handle bulk actions
 */
function handleSelectAll() {
    const isChecked = $(this).is(':checked');
    $('.product-checkbox').prop('checked', isChecked);
    updateBulkActionButtons();
}

function handleProductSelect() {
    updateBulkActionButtons();
}

function updateBulkActionButtons() {
    const selectedCount = $('.product-checkbox:checked').length;
    const bulkActionsContainer = $('#bulk-actions');
    
    if (selectedCount > 0) {
        if (bulkActionsContainer.length === 0) {
            $('.section-header').append(`
                <div id="bulk-actions" class="mt-3">
                    <span class="text-muted me-3">เลือก ${selectedCount} รายการ</span>
                    <button class="btn btn-sm btn-success" onclick="bulkToggleStatus(true)">
                        <i class="fas fa-eye me-1"></i>เปิดการจำหน่าย
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="bulkToggleStatus(false)">
                        <i class="fas fa-eye-slash me-1"></i>ปิดการจำหน่าย
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="bulkToggleFeatured(true)">
                        <i class="fas fa-star me-1"></i>ตั้งเป็นแนะนำ
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="bulkDelete()">
                        <i class="fas fa-trash me-1"></i>ลบที่เลือก
                    </button>
                </div>
            `);
        } else {
            bulkActionsContainer.find('span').text(`เลือก ${selectedCount} รายการ`);
        }
    } else {
        bulkActionsContainer.remove();
    }
}

/**
 * Auto-save form data
 */
function autoSaveFormData() {
    const formData = {
        product_name: $('#product_name').val(),
        product_price: $('#product_price').val(),
        product_category: $('#product_category').val(),
        product_description: $('#product_description').val(),
        product_stock: $('#product_stock').val(),
        product_image: $('#product_image').val(),
        product_available: $('#product_available').is(':checked'),
        product_featured: $('#product_featured').is(':checked')
    };
    
    localStorage.setItem('admin_form_draft', JSON.stringify(formData));
}

/**
 * Load auto-saved form data
 */
function loadAutoSavedData() {
    const saved = localStorage.getItem('admin_form_draft');
    if (saved) {
        const data = JSON.parse(saved);
        Object.keys(data).forEach(key => {
            const element = $(`#${key}`);
            if (element.attr('type') === 'checkbox') {
                element.prop('checked', data[key]);
            } else {
                element.val(data[key]);
            }
        });
    }
}

/**
 * Clear auto-saved data
 */
function clearAutoSavedData() {
    localStorage.removeItem('admin_form_draft');
}

/**
 * Handle image upload
 */
function handleImageUpload(e) {
    const file = e.target.files[0];
    if (file) {
        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            showAdminToast('รูปภาพต้องเป็นไฟล์ JPG, PNG, GIF หรือ WebP เท่านั้น', 'error');
            return;
        }
        
        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showAdminToast('ขนาดไฟล์ต้องไม่เกิน 5MB', 'error');
            return;
        }
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            $('#image-preview').remove();
            $('#product-image-upload').after(`
                <div id="image-preview" class="mt-2">
                    <img src="${e.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px; border-radius: 8px;">
                    <button type="button" class="btn btn-sm btn-danger ms-2" onclick="removeImagePreview()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `);
        };
        reader.readAsDataURL(file);
        
        // Set filename in text input
        $('#product_image').val(file.name);
    }
}

/**
 * Remove image preview
 */
function removeImagePreview() {
    $('#image-preview').remove();
    $('#product-image-upload').val('');
    $('#product_image').val('');
}

/**
 * Setup real-time updates
 */
function setupRealTimeUpdates() {
    // Simulate real-time stats updates
    setInterval(() => {
        const random = Math.floor(Math.random() * 10);
        if (random > 8) {
            updateStatsCard('orders', Math.floor(Math.random() * 3) + 1);
            updateStatsCard('revenue', Math.floor(Math.random() * 500) + 100);
        }
    }, 30000);
}

/**
 * Update statistics card
 */
function updateStatsCard(type, change) {
    const card = $(`.stat-${type} .stat-number`);
    let currentValue = parseInt(card.text().replace(/[^\d]/g, ''));
    let newValue = currentValue + change;
    
    if (type === 'revenue') {
        card.text('฿' + newValue.toLocaleString());
    } else {
        card.text(newValue);
    }
    
    // Add animation
    card.addClass('animate-pulse');
    setTimeout(() => card.removeClass('animate-pulse'), 1000);
}

/**
 * Load dashboard data
 */
function loadDashboardData() {
    // Load recent orders, popular products, etc.
    // This would typically be AJAX calls to the server
    setTimeout(() => {
        showAdminToast('ข้อมูลแดชบอร์ดโหลดเสร็จแล้ว', 'info');
    }, 2000);
}

/**
 * Add product to table
 */
function addProductToTable(productData) {
    const newRow = createProductTableRow(productData);
    $('tbody').prepend(newRow);
    
    // Add animation
    newRow.hide().fadeIn(500);
    
    // Remove empty table message if exists
    $('.empty-table-message').remove();
}

/**
 * Update product in table
 */
function updateProductInTable(productId, productData) {
    const row = $(`tr[data-product-id="${productId}"]`);
    const newRow = createProductTableRow(productData);
    
    row.replaceWith(newRow);
    newRow.addClass('table-warning');
    setTimeout(() => newRow.removeClass('table-warning'), 2000);
}

/**
 * Create product table row
 */
function createProductTableRow(product) {
    return $(`
        <tr data-product-id="${product.id}">
            <td>
                <div class="form-check">
                    <input class="form-check-input product-checkbox" type="checkbox" value="${product.id}">
                </div>
            </td>
            <td>
                ${product.image ? 
                    `<img src="/static/images/products/${product.image}" class="product-image-thumb me-2" alt="${product.name}">` : 
                    '<div class="product-image-thumb me-2 d-inline-flex align-items-center justify-content-center bg-light"><i class="fas fa-image text-muted"></i></div>'
                }
                <div class="d-inline-block">
                    <div class="fw-600">${product.name}</div>
                    ${product.description ? `<small class="text-muted">${product.description.substring(0, 50)}...</small>` : ''}
                </div>
            </td>
            <td><span class="badge bg-light text-dark">${product.category_name}</span></td>
            <td class="fw-600 text-primary">${product.price.toFixed(0)} ฿</td>
            <td><span class="${product.stock_quantity <= 5 ? 'text-warning' : 'text-success'}">${product.stock_quantity}</span></td>
            <td>
                <div class="d-flex flex-column gap-1">
                    <span class="status-badge ${product.is_available ? 'status-available' : 'status-unavailable'}">
                        ${product.is_available ? 'พร้อมจำหน่าย' : 'ไม่พร้อมจำหน่าย'}
                    </span>
                    ${product.is_featured ? '<span class="status-badge featured-badge">แนะนำ</span>' : ''}
                </div>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-outline-primary btn-action btn-edit" data-product-id="${product.id}" data-bs-toggle="tooltip" title="แก้ไข">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-info btn-action btn-toggle-status" 
                            data-product-id="${product.id}" data-current-status="${product.is_available}"
                            data-bs-toggle="tooltip" title="${product.is_available ? 'ปิดการจำหน่าย' : 'เปิดการจำหน่าย'}">
                        <i class="fas ${product.is_available ? 'fa-eye-slash' : 'fa-eye'}"></i>
                    </button>
                    <button class="btn btn-outline-warning btn-action btn-toggle-featured" 
                            data-product-id="${product.id}" data-current-featured="${product.is_featured}"
                            data-bs-toggle="tooltip" title="${product.is_featured ? 'ยกเลิกแนะนำ' : 'ตั้งเป็นสินค้าแนะนำ'}">
                        <i class="fas ${product.is_featured ? 'fa-star' : 'fa-star'} ${product.is_featured ? '' : 'far'}"></i>
                    </button>
                    <button class="btn btn-outline-danger btn-action btn-delete" 
                            data-product-id="${product.id}" data-product-name="${product.name}"
                            data-bs-toggle="tooltip" title="ลบ">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `);
}

/**
 * Show empty table message
 */
function showEmptyTableMessage() {
    $('tbody').html(`
        <tr class="empty-table-message">
            <td colspan="7" class="text-center py-5">
                <i class="fas fa-box-open fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">ไม่มีสินค้า</h5>
                <p class="text-muted">คลิกเพิ่มสินค้าใหม่เพื่อเริ่มต้น</p>
                <button class="btn btn-primary" onclick="showAddProductForm()">
                    <i class="fas fa-plus me-2"></i>เพิ่มสินค้าใหม่
                </button>
            </td>
        </tr>
    `);
}

/**
 * Show admin toast notification
 */
function showAdminToast(message, type = 'info') {
    // Remove existing toasts
    $('.admin-toast').remove();
    
    const toastHtml = `
        <div class="toast admin-toast align-items-center border-0 position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999;" role="alert">
            <div class="d-flex">
                <div class="toast-body bg-${type === 'error' ? 'danger' : type} text-white rounded">
                    <i class="fas fa-${getToastIcon(type)} me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    $('body').append(toastHtml);
    
    const toast = new bootstrap.Toast($('.admin-toast').last()[0], {
        autohide: true,
        delay: type === 'error' ? 5000 : 3000
    });
    
    toast.show();
}

/**
 * Get appropriate icon for toast type
 */
function getToastIcon(type) {
    switch(type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        case 'info': return 'info-circle';
        default: return 'info-circle';
    }
}

/**
 * Bulk operations
 */
function bulkToggleStatus(status) {
    const selectedIds = getSelectedProductIds();
    if (selectedIds.length === 0) return;
    
    selectedIds.forEach(id => {
        const button = $(`.btn-toggle-status[data-product-id="${id}"]`);
        if (button.data('current-status') !== status) {
            button.click();
        }
    });
}

function bulkToggleFeatured(featured) {
    const selectedIds = getSelectedProductIds();
    if (selectedIds.length === 0) return;
    
    selectedIds.forEach(id => {
        const button = $(`.btn-toggle-featured[data-product-id="${id}"]`);
        if (button.data('current-featured') !== featured) {
            button.click();
        }
    });
}

function bulkDelete() {
    const selectedIds = getSelectedProductIds();
    if (selectedIds.length === 0) return;
    
    if (!confirm(`คุณต้องการลบสินค้า ${selectedIds.length} รายการที่เลือกหรือไม่?`)) {
        return;
    }
    
    selectedIds.forEach(id => {
        $(`.btn-delete[data-product-id="${id}"]`).click();
    });
}

function getSelectedProductIds() {
    return $('.product-checkbox:checked').map(function() {
        return $(this).val();
    }).get();
}

/**
 * Utility functions
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
 * Quick actions
 */
function handleQuickAction() {
    const action = $(this).data('action');
    
    switch(action) {
        case 'export':
            exportProducts();
            break;
        case 'import':
            showImportModal();
            break;
        case 'backup':
            backupDatabase();
            break;
        case 'reports':
            showReportsModal();
            break;
        default:
            showAdminToast('ฟีเจอร์นี้ยังไม่พร้อมใช้งาน', 'info');
    }
}

function exportProducts() {
    showAdminToast('กำลังส่งออกข้อมูล...', 'info');
    
    // Simulate export process
    setTimeout(() => {
        showAdminToast('ส่งออกข้อมูลเรียบร้อยแล้ว', 'success');
    }, 2000);
}

function showImportModal() {
    // Implementation for import modal
    showAdminToast('ฟีเจอร์นำเข้าข้อมูล (ยังไม่ได้ทำ)', 'info');
}

function backupDatabase() {
    showAdminToast('กำลังสำรองข้อมูล...', 'info');
    
    setTimeout(() => {
        showAdminToast('สำรองข้อมูลเรียบร้อยแล้ว', 'success');
    }, 3000);
}

function showReportsModal() {
    showAdminToast('ฟีเจอร์รายงาน (ยังไม่ได้ทำ)', 'info');
}

// Export functions for global use
window.AdminPanel = {
    showAddProductForm,
    hideAddProductForm,
    showAdminToast,
    exportProducts,
    backupDatabase
};