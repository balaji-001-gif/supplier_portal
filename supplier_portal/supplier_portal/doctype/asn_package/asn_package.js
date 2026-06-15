frappe.ui.form.on('ASN Package', {
    // Client-side logic for inline package editing in the ASN form
    package_type: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.package_type === 'Pallet') {
            frappe.model.set_value(cdt, cdn, 'package_id', 'PAL-' + row.idx.toString().padStart(2, '0'));
        } else if (row.package_type === 'Crate') {
            frappe.model.set_value(cdt, cdn, 'package_id', 'CRT-' + row.idx.toString().padStart(2, '0'));
        } else {
            frappe.model.set_value(cdt, cdn, 'package_id', 'PKG-' + row.idx.toString().padStart(2, '0'));
        }
    }
});
