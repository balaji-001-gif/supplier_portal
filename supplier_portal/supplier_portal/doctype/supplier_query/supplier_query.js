frappe.ui.form.on('Supplier Query', {
    refresh: function(frm) {
        // Show response field for internal users
        if (!frm.doc.__islocal && frm.doc.docstatus === 1 && frm.doc.status === 'Open') {
            frm.add_custom_button(__('Respond to Query'), function() {
                let d = new frappe.ui.Dialog({
                    title: __('Respond to Query'),
                    fields: [
                        {
                            fieldtype: 'Text Editor',
                            fieldname: 'response',
                            label: __('Your Response'),
                            reqd: 1
                        }
                    ],
                    primary_action_label: __('Send Response'),
                    primary_action: function() {
                        let data = d.get_values();
                        frm.call('respond', {
                            response_text: data.response
                        }, function(r) {
                            if (r.message) {
                                d.hide();
                                frm.refresh();
                                frappe.show_alert({
                                    message: __('Response sent successfully'),
                                    indicator: 'green'
                                });
                            }
                        });
                    }
                });
                d.show();
            }, __('Actions'));
        }

        // Allow closing resolved queries
        if (frm.doc.status === 'Responded') {
            frm.add_custom_button(__('Close Query'), function() {
                frm.set_value('status', 'Closed');
                frm.save();
            }, __('Actions'));
        }
    },

    onload: function(frm) {
        // Auto-set supplier for portal users
        if (frm.doc.__islocal && !frm.doc.supplier) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'User',
                    filters: { name: frappe.session.user },
                    fieldname: 'supplier'
                },
                callback: function(r) {
                    if (r.message && r.message.supplier) {
                        frm.set_value('supplier', r.message.supplier);
                    }
                }
            });
        }
    }
});
