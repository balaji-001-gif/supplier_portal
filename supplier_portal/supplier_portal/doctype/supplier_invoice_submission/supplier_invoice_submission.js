frappe.ui.form.on('Supplier Invoice Submission', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.purchase_invoice) {
            frm.add_custom_button(__('View Purchase Invoice'), function() {
                frappe.set_route('Form', 'Purchase Invoice', frm.doc.purchase_invoice);
            }, __('Actions'));
        }
    },

    purchase_receipt: function(frm) {
        if (frm.doc.purchase_receipt) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Purchase Receipt',
                    name: frm.doc.purchase_receipt
                },
                callback: function(r) {
                    if (r.message) {
                        let pr = r.message;
                        frm.set_value('supplier', pr.supplier);
                        frm.set_value('supplier_name', pr.supplier_name);
                        frm.set_value('total_amount', pr.grand_total);
                        // Suggest invoice amount = PR total
                        if (!frm.doc.invoice_amount) {
                            frm.set_value('invoice_amount', pr.grand_total);
                        }
                    }
                }
            });
        }
    }
});
