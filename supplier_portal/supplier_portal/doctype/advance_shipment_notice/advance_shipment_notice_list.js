// List view script for Advance Shipment Notice
frappe.listview_settings['Advance Shipment Notice'] = {
    add_fields: ["status", "supplier", "expected_delivery_date", "num_packages"],
    filters: [["status", "!=", "Cancelled"]],
    get_indicator: function(doc) {
        const status_colors = {
            "Draft": "grey",
            "Submitted": "blue",
            "In Transit": "orange",
            "At Gate": "purple",
            "Unloading": "yellow",
            "Received": "green",
            "Cancelled": "red"
        };
        return [__(doc.status), status_colors[doc.status] || "grey", "status,=," + doc.status];
    },
    button: {
        show: function(doc) {
            return doc.name;
        },
        get_label: function() {
            return __('View QR');
        },
        get_description: function(doc) {
            return __('View QR Codes for {0}', [doc.name]);
        },
        action: function(doc) {
            frappe.call({
                method: 'supplier_portal.api.qr_code.get_package_qr_pdf',
                args: { asn_name: doc.name },
                callback: function(r) {
                    if (r.message) {
                        window.open(r.message);
                    }
                }
            });
        }
    },
    onload: function(listview) {
        listview.page.add_menu_item(__('Gate Queue'), function() {
            frappe.set_route('List', 'Gate Entry', {
                'status': ['in', ['At Gate', 'Waiting for Unloading']]
            });
        });
    }
};
