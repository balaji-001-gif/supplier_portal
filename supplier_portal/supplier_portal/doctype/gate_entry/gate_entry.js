frappe.ui.form.on('Gate Entry', {
    refresh: function(frm) {
        // Actions for submitted gate entries
        if (frm.doc.docstatus === 1) {
            if (frm.doc.purchase_receipt) {
                frm.add_custom_button(__('View Purchase Receipt'), function() {
                    frappe.set_route('Form', 'Purchase Receipt', frm.doc.purchase_receipt);
                }, __('Actions'));
            }
        }

        // Generate QR scan link
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Open QR Scanner'), function() {
                let d = new frappe.ui.Dialog({
                    title: __('Scan QR Code'),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'qr_scanner',
                            options: `
                                <div style="text-align: center;">
                                    <video id="qr-video" style="width: 100%; max-width: 400px; border: 2px dashed #ccc; border-radius: 8px;"></video>
                                    <p class="text-muted" style="margin-top: 8px; font-size: 12px;">
                                        Point camera at the package QR code
                                    </p>
                                    <button class="btn btn-sm btn-primary" onclick="startQRScanner()">
                                        Start Camera
                                    </button>
                                    <button class="btn btn-sm btn-danger" onclick="stopQRScanner()" style="display:none;" id="stop-scanner-btn">
                                        Stop Camera
                                    </button>
                                </div>
                                <script>
                                    let scannerStream = null;
                                    function startQRScanner() {
                                        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                                            .then(function(stream) {
                                                scannerStream = stream;
                                                document.getElementById('qr-video').srcObject = stream;
                                                document.getElementById('stop-scanner-btn').style.display = 'inline-block';
                                            })
                                            .catch(function(err) {
                                                frappe.msgprint(__('Camera access denied. Please use a QR scanner device.'));
                                            });
                                    }
                                    function stopQRScanner() {
                                        if (scannerStream) {
                                            scannerStream.getTracks().forEach(t => t.stop());
                                            scannerStream = null;
                                        }
                                        document.getElementById('stop-scanner-btn').style.display = 'none';
                                    }
                                </script>
                            `
                        }
                    ],
                    primary_action_label: __('Close'),
                    primary_action: function() { d.hide(); }
                });
                d.show();
            }, __('Actions'));
        }
    },

    asn_reference: function(frm) {
        if (frm.doc.asn_reference) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Advance Shipment Notice',
                    name: frm.doc.asn_reference
                },
                callback: function(r) {
                    if (r.message) {
                        let asn = r.message;
                        frm.set_value('supplier', asn.supplier);
                        frm.set_value('supplier_name', asn.supplier_name);
                        frm.set_value('vehicle_no', asn.vehicle_no);
                        frm.set_value('driver_name', asn.driver_name);
                        frm.set_value('driver_mobile', asn.driver_mobile);
                        frm.set_value('lr_no', asn.lr_no);
                        frm.set_value('transport_company', asn.transport_company);
                        frm.set_value('num_packages', asn.num_packages);
                    }
                }
            });
        }
    },

    unloading_start_time: function(frm) {
        if (frm.doc.unloading_start_time) {
            frm.set_value('unloading_end_time', '');
            // Set status to Unloading
            if (frm.doc.status === 'At Gate' || frm.doc.status === 'Waiting for Unloading') {
                frm.set_value('status', 'Unloading');
            }
        }
    },

    unloading_end_time: function(frm) {
        if (frm.doc.unloading_end_time && frm.doc.unloading_start_time) {
            // Calculate duration via server-side
            frm.call('calculate_unloading_duration', {}, function(r) {
                // Duration auto-calculated on validate
            });
            frm.set_value('status', 'Completed');
        }
    }
});
