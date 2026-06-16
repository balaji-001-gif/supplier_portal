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

        // Open QR Scanner dialog
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Open QR Scanner'), function() {
                let scannerStream = null;

                let d = new frappe.ui.Dialog({
                    title: __('Scan QR Code'),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'qr_scanner',
                            options: `
                                <div style="text-align: center;">
                                    <video id="qr-video" style="width: 100%; max-width: 400px; border: 2px dashed #ccc; border-radius: 8px; display: none;"></video>
                                    <div id="qr-placeholder" style="padding: 40px 20px; color: #94a3b8;">
                                        <div style="font-size: 48px; margin-bottom: 12px;">📷</div>
                                        <div>Camera off — click Start to begin scanning</div>
                                    </div>
                                    <p id="scanner-status" style="font-size: 12px; margin-top: 8px; min-height: 20px; color: #64748b;"></p>
                                    <button class="btn btn-sm btn-primary" id="start-scanner-btn">
                                        📷 Start Camera
                                    </button>
                                    <button class="btn btn-sm btn-danger" id="stop-scanner-btn" style="display:none;">
                                        ⏹ Stop Camera
                                    </button>
                                </div>
                            `
                        }
                    ],
                    primary_action_label: __('Close'),
                    primary_action: function() {
                        stopScanner();
                        d.hide();
                    }
                });

                function startScanner() {
                    let video = document.getElementById('qr-video');
                    let placeholder = document.getElementById('qr-placeholder');
                    let status = document.getElementById('scanner-status');

                    if (!video) return;

                    // Check for secure context — mediaDevices is undefined on HTTP
                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        if (status) {
                            status.textContent = '❌ Camera requires HTTPS. Please access this page via https://';
                            status.style.color = '#dc2626';
                        }
                        frappe.msgprint(__('Camera access requires a secure connection (HTTPS). ' +
                            'Please access this page via https:// instead of http://'));
                        return;
                    }

                    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                        .then(function(stream) {
                            scannerStream = stream;
                            video.srcObject = stream;
                            video.play();
                            video.style.display = 'block';
                            if (placeholder) placeholder.style.display = 'none';
                            document.getElementById('start-scanner-btn').style.display = 'none';
                            document.getElementById('stop-scanner-btn').style.display = 'inline-block';
                            if (status) {
                                status.textContent = '✅ Camera active. Point at QR code.';
                                status.style.color = '#16a34a';
                            }
                        })
                        .catch(function(err) {
                            if (status) {
                                status.textContent = '❌ Camera access denied: ' + err.message;
                                status.style.color = '#dc2626';
                            }
                            frappe.msgprint(__('Camera access denied: {0}', [err.message]));
                        });
                }

                function stopScanner() {
                    if (scannerStream) {
                        scannerStream.getTracks().forEach(function(t) { t.stop(); });
                        scannerStream = null;
                    }
                    let video = document.getElementById('qr-video');
                    let placeholder = document.getElementById('qr-placeholder');
                    let status = document.getElementById('scanner-status');
                    if (video) video.style.display = 'none';
                    if (placeholder) placeholder.style.display = 'block';
                    document.getElementById('start-scanner-btn').style.display = 'inline-block';
                    document.getElementById('stop-scanner-btn').style.display = 'none';
                    if (status) {
                        status.textContent = 'Camera stopped';
                        status.style.color = '#64748b';
                    }
                }

                d.show();

                // Attach scanner button handlers via d.$wrapper — always safe after d.show()
                d.$wrapper.find('#start-scanner-btn').on('click', startScanner);
                d.$wrapper.find('#stop-scanner-btn').on('click', stopScanner);

                // Clean up camera when dialog is dismissed by any means (Escape, click-outside, Close button)
                d.$wrapper.on('hidden.bs.modal', function() {
                    stopScanner();
                });
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
