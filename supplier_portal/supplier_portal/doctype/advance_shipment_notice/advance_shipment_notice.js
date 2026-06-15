frappe.ui.form.on('Advance Shipment Notice', {
    refresh: function(frm) {
        // Show QR generation button for submitted ASN
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Print QR Labels'), function() {
                frappe.call({
                    method: 'frappe.utils.print_format.download_pdf',
                    args: {
                        doctype: frm.doc.doctype,
                        name: frm.doc.name,
                        format: 'ASN QR Labels',
                        no_letterhead: 1
                    }
                });
            }, __('Actions'));

            frm.add_custom_button(__('View Tracking'), function() {
                frappe.call({
                    method: 'supplier_portal.api.asn.get_asn_tracking',
                    args: { asn_name: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            // Show tracking details in a dialog
                            let d = new frappe.ui.Dialog({
                                title: __('Tracking - {0}', [frm.doc.name]),
                                fields: [
                                    { fieldtype: 'HTML', options: __(JSON.stringify(r.message, null, 2)) }
                                ],
                                primary_action_label: __('Close'),
                                primary_action: function() { d.hide(); }
                            });
                            d.show();
                        }
                    }
                });
            }, __('Actions'));
        }

        // Show "Create Gate Entry" for submitted ASN without gate entry
        if (frm.doc.docstatus === 1 && frm.doc.status !== 'Cancelled') {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Gate Entry',
                    filters: { asn_reference: frm.doc.name },
                    fieldname: 'name'
                },
                callback: function(r) {
                    if (!r.message) {
                        frm.add_custom_button(__('Create Gate Entry'), function() {
                            frappe.call({
                                method: 'frappe.client.get_value',
                                args: {
                                    doctype: 'Advance Shipment Notice',
                                    filters: { name: frm.doc.name },
                                    fieldname: ['name', 'supplier', 'supplier_name', 'vehicle_no',
                                        'driver_name', 'driver_mobile', 'lr_no', 'transport_company', 'num_packages']
                                },
                                callback: function(res) {
                                    if (res.message) {
                                        frappe.model.open_mapped_doc({
                                            method: 'supplier_portal.api.gate_entry.create_gate_entry_from_asn',
                                            frm: res.message
                                        });
                                    }
                                }
                            });
                        }, __('Actions'));
                    }
                }
            });
        }
    },

    purchase_order: function(frm) {
        if (frm.doc.purchase_order) {
            frappe.call({
                method: 'supplier_portal.api.asn.get_asn_items',
                args: {
                    purchase_order: frm.doc.purchase_order,
                    asn: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frm.clear_table('items');
                        r.message.forEach(function(item) {
                            let row = frm.add_child('items');
                            row.item_code = item.item_code;
                            row.item_name = item.item_name;
                            row.po_detail = item.name;
                            row.po_qty = item.qty;
                            row.uom = item.uom;
                            row.dispatch_qty = item.qty - item.received_qty;
                        });
                        frm.refresh_field('items');
                    }
                }
            });
        }
    },

    before_submit: function(frm) {
        // Auto-generate packages from num_packages if not manually added
        if (frm.doc.packages && frm.doc.packages.length === 0 && frm.doc.num_packages > 0) {
            for (let i = 0; i < frm.doc.num_packages; i++) {
                let row = frm.add_child('packages');
                row.package_id = 'PKG-' + String(i + 1).padStart(2, '0');
                row.package_type = 'Carton';
            }
            frm.refresh_field('packages');
        }
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
