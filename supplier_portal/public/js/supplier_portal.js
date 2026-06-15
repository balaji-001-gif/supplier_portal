// Supplier Portal Main JS

frappe.provide('frappe.supplier_portal');

frappe.supplier_portal = {
    init: function() {
        this.bind_events();
    },

    bind_events: function() {
        $(document).on('click', '[data-action="portal-logout"]', function() {
            frappe.call({
                method: 'logout',
                callback: function() {
                    window.location.href = '/login';
                }
            });
        });
    },

    // Helper to format currency
    format_currency: function(amount, currency) {
        if (!amount) return '-';
        currency = currency || 'INR';
        return frappe.format(amount, { fieldtype: 'Currency', options: currency });
    },

    // Helper to show loading state
    show_loading: function(selector) {
        $(selector).html('<div class="portal-loading"><span class="spinner"></span> Loading...</div>');
    },

    // Helper to show error state
    show_error: function(selector, message) {
        $(selector).html('<div class="portal-error">' + (message || 'An error occurred') + '</div>');
    }
};

// Initialize on document ready
$(document).ready(function() {
    frappe.supplier_portal.init();
});
