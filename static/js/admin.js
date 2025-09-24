$(document).ready(function () {
    // Toast function
    function showAdminToast(message, type = 'info') {
        const toast = $('#admin-toast');
        toast.removeClass('bg-success bg-danger bg-warning bg-info');
        if (type === 'success') toast.addClass('bg-success');
        else if (type === 'error') toast.addClass('bg-danger');
        else if (type === 'warning') toast.addClass('bg-warning');
        else toast.addClass('bg-info');
        toast.find('.toast-body').text(message);
        toast.toast({ delay: 2500 });
        toast.toast('show');
    }

    // Update stats card (optional)
    function updateStatsCard(type, diff) {
        const card = $(`#stats-${type}`);
        if (card.length) {
            let val = parseInt(card.text()) || 0;
            card.text(val + diff);
        }
    }

    // Show empty table message
    function showEmptyTableMessage() {
        if ($('tbody tr:visible').length === 0) {
            $('tbody').append(
                `<tr class="text-center text-muted"><td colspan="99">ไม่มีข้อมูลสินค้า</td></tr>`
            );
        }
    }

    // ดึงข้อมูลเดิมมาใส่ฟอร์มตอนแก้ไข
    $(document).on('click', '.btn-edit', function () {
        const productId = $(this).data('product-id');
        $.get(`/admin/product/${productId}`, function (data) {
            if (data.error) {
                showAdminToast(data.error, 'error');
                return;
            }
            $('#product-form')[0].reset();
            $('#product-form').data('edit-id', productId);
            $('#product_name').val(data.name);
            $('#product_name_en').val(data.name_en);
            $('#product_description').val(data.description);
            $('#product_price').val(data.price);
            $('#product_category').val(data.category_id);
            $('#product_stock').val(data.stock_quantity);
            $('#product_image').val(data.image);
            $('#product_available').prop('checked', data.is_available == 1);
            $('#product_featured').prop('checked', data.is_featured == 1);
            $('#add-product-form').show();
            $('html,body').animate({ scrollTop: $('#add-product-form').offset().top - 80 }, 400);
        });
    });

    // แสดงฟอร์มเพิ่มสินค้า
    $('#show-add-form').click(function () {
        $('#product-form')[0].reset();
        $('#product-form').removeData('edit-id');
        $('#add-product-form').show();
        $('html,body').animate({ scrollTop: $('#add-product-form').offset().top - 80 }, 400);
    });

    // ปิดฟอร์ม
    $('#close-add-form').click(function () {
        $('#add-product-form').hide();
        $('#product-form')[0].reset();
        $('#product-form').removeData('edit-id');
    });

    // ส่งฟอร์มเพิ่ม/แก้ไขสินค้า
    $('#product-form').submit(function (e) {
        e.preventDefault();
        const editId = $(this).data('edit-id');
        const url = editId ? `/admin/update_product/${editId}` : '/admin/add_product';
        const formData = {
            name: $('#product_name').val(),
            name_en: $('#product_name_en').val(),
            description: $('#product_description').val(),
            price: $('#product_price').val(),
            image: $('#product_image').val(),
            category_id: $('#product_category').val(),
            is_available: $('#product_available').is(':checked') ? 1 : 0,
            is_featured: $('#product_featured').is(':checked') ? 1 : 0,
            stock_quantity: $('#product_stock').val()
        };
        const submitBtn = $('#product-form button[type="submit"]');
        const originalText = submitBtn.html();
        submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>กำลังบันทึก...');
        $.ajax({
            url: url,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function (response) {
                if (response.success) {
                    showAdminToast(editId ? 'แก้ไขสินค้าเรียบร้อย' : 'เพิ่มสินค้าเรียบร้อย', 'success');
                    setTimeout(() => location.reload(), 800);
                } else {
                    showAdminToast(response.message || 'เกิดข้อผิดพลาด', 'error');
                }
            },
            error: function () {
                showAdminToast('เกิดข้อผิดพลาดในการบันทึก', 'error');
            },
            complete: function () {
                submitBtn.prop('disabled', false).html(originalText);
            }
        });
    });

    // ลบสินค้า
    $(document).on('click', '.btn-delete', function () {
        const productId = $(this).data('product-id');
        const productName = $(this).data('product-name');
        const row = $(this).closest('tr');
        if (!confirm(`คุณต้องการลบสินค้า "${productName}" หรือไม่?\n\nการดำเนินการนี้ไม่สามารถยกเลิกได้`)) {
            return;
        }
        row.addClass('loading-row');
        $.ajax({
            url: `/admin/delete_product/${productId}`,
            type: 'DELETE',
            success: function (response) {
                if (response.success) {
                    row.fadeOut(300, function () {
                        row.remove();
                        showAdminToast(`ลบสินค้า "${productName}" เรียบร้อยแล้ว`, 'success');
                        updateStatsCard('products', -1);
                        showEmptyTableMessage();
                    });
                } else {
                    showAdminToast(response.message || 'เกิดข้อผิดพลาด', 'error');
                    row.removeClass('loading-row');
                }
            },
            error: function () {
                showAdminToast('เกิดข้อผิดพลาดในการลบสินค้า', 'error');
                row.removeClass('loading-row');
            }
        });
    });

    // ปิด/เปิดจำหน่าย
    $(document).on('click', '.btn-toggle-status', function () {
        const productId = $(this).data('product-id');
        const button = $(this);
        const row = button.closest('tr');
        button.prop('disabled', true);
        row.addClass('loading-row');
        $.ajax({
            url: `/admin/toggle_product_status/${productId}`,
            type: 'POST',
            success: function (response) {
                if (response.success) {
                    showAdminToast('อัปเดตสถานะสินค้าเรียบร้อย', 'success');
                    setTimeout(() => location.reload(), 600);
                } else {
                    showAdminToast(response.message || 'เกิดข้อผิดพลาด', 'error');
                }
            },
            error: function () {
                showAdminToast('เกิดข้อผิดพลาดในการอัปเดต', 'error');
            },
            complete: function () {
                button.prop('disabled', false);
                row.removeClass('loading-row');
            }
        });
    });

    // แนะนำ/ยกเลิกแนะนำ
    $(document).on('click', '.btn-toggle-featured', function () {
        const productId = $(this).data('product-id');
        const button = $(this);
        const row = button.closest('tr');
        button.prop('disabled', true);
        row.addClass('loading-row');
        $.ajax({
            url: `/admin/toggle_product_featured/${productId}`,
            type: 'POST',
            success: function (response) {
                if (response.success) {
                    showAdminToast('อัปเดตสถานะสินค้าแนะนำเรียบร้อย', 'success');
                    setTimeout(() => location.reload(), 600);
                } else {
                    showAdminToast(response.message || 'เกิดข้อผิดพลาด', 'error');
                }
            },
            error: function () {
                showAdminToast('เกิดข้อผิดพลาดในการอัปเดต', 'error');
            },
            complete: function () {
                button.prop('disabled', false);
                row.removeClass('loading-row');
            }
        });
    });

    // Preview image before upload (optional)
    $('#productImage').change(function () {
        const input = this;
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function (e) {
                $('#imagePreview').attr('src', e.target.result).show();
            };
            reader.readAsDataURL(input.files[0]);
        }
    });

    // DataTable init (optional, ถ้ามี DataTable)
    if ($.fn.DataTable) {
        $('#productTable').DataTable({
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/th.json'
            }
        });
    }
});