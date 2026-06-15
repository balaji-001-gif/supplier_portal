frappe.ui.form.on('Supplier Scorecard', {
    refresh: function(frm) {
        frm.add_custom_button(__('Recalculate Score'), function() {
            frm.call('calculate_average_metrics', {}, function(r) {
                frm.refresh_fields();
                frappe.show_alert({
                    message: __('Scorecard recalculated successfully'),
                    indicator: 'green'
                });
            });
        }, __('Actions'));
    },

    supplier: function(frm) {
        if (frm.doc.supplier) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Supplier',
                    filters: { name: frm.doc.supplier },
                    fieldname: 'supplier_name'
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('supplier_name', r.message.supplier_name);
                    }
                }
            });
        }
    }
});
