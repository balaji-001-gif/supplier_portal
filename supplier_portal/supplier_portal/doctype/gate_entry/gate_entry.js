frappe.ui.form.on('Gate Entry', {
    refresh: function(frm) {
        // Actions for submitted gate entries
        if (frm.doc.docstatus === 1) {
            if (frm.doc.asn_reference) {
                frm.add_custom_button(__('Create Purchase Receipt'), function() {
                    createPRFromGateEntry(frm, this);
                }, __('Actions'));
            }
            if (frm.doc.purchase_receipt) {
                frm.add_custom_button(__('View Purchase Receipt'), function() {
                    frappe.set_route('Form', 'Purchase Receipt', frm.doc.purchase_receipt);
                }, __('Actions'));
            }
        }

        function createPRFromGateEntry(frm, btn) {
            // Disable button and show loading
            $(btn).prop('disabled', true).html(__('Creating PR...'));

            frappe.call({
                method: 'supplier_portal.api.gate_entry.create_purchase_receipt_from_gate_entry',
                args: {
                    gate_entry_name: frm.doc.name
                },
                callback: function(res) {
                    if (res.message && res.message.success) {
                        frappe.show_alert({
                            message: __('Purchase Receipt {0} created. Edit details as needed.', [res.message.purchase_receipt]),
                            indicator: 'green'
                        });
                        frappe.set_route('Form', 'Purchase Receipt', res.message.purchase_receipt);
                    } else {
                        frappe.msgprint(__('Error: {0}', [res.message.message || 'Unknown error']));
                        $(btn).prop('disabled', false).html(__('Create Purchase Receipt'));
                    }
                },
                error: function(err) {
                    frappe.msgprint(__('Error: {0}', [err.message]));
                    $(btn).prop('disabled', false).html(__('Create Purchase Receipt'));
                }
            });
        }

        // Open QR Scanner dialog
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Open QR Scanner'), function() {
                var scannerStream = null;
                var scanInterval = null;

                var d = new frappe.ui.Dialog({
                    title: __('Scan QR Code'),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'qr_scanner',
                            options: '\
                                <div style="text-align: center;">\
                                    <video id="qr-video" style="width: 100%; max-width: 400px; border: 2px dashed #ccc; border-radius: 8px; display: none;"></video>\
                                    <canvas id="qr-canvas" style="display:none;"></canvas>\
                                    <div id="qr-placeholder" style="padding: 40px 20px; color: #94a3b8;">\
                                        <div style="font-size: 48px; margin-bottom: 12px;">📷</div>\
                                        <div>Camera off — click Start to begin scanning</div>\
                                    </div>\
                                    <p id="scanner-status" style="font-size: 12px; margin-top: 8px; min-height: 20px; color: #64748b;"></p>\
                                    <button class="btn btn-sm btn-primary" id="start-scanner-btn">\
                                        📷 Start Camera\
                                    </button>\
                                    <button class="btn btn-sm btn-danger" id="stop-scanner-btn" style="display:none;">\
                                        ⏹ Stop Camera\
                                    </button>\
                                </div>\
                            '
                        }
                    ],
                    primary_action_label: __('Close'),
                    primary_action: function() {
                        stopScanner();
                        d.hide();
                    }
                });

                // Load jsQR library from CDN
                function loadJsQR(callback) {
                    if (typeof jsQR !== 'undefined') {
                        callback();
                        return;
                    }
                    var script = document.createElement('script');
                    script.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js';
                    script.onload = callback;
                    script.onerror = function() {
                        // Restore button state so user can retry
                        var status = document.getElementById('scanner-status');
                        if (status) {
                            status.textContent = '❌ Failed to load QR decoder. Check internet and retry.';
                            status.style.color = '#dc2626';
                        }
                        document.getElementById('start-scanner-btn').style.display = 'inline-block';
                        frappe.msgprint(__('Failed to load QR decoding library. Please check your internet connection and try again.'));
                    };
                    document.head.appendChild(script);
                }

                function startScanner() {
                    var video = document.getElementById('qr-video');
                    var placeholder = document.getElementById('qr-placeholder');
                    var status = document.getElementById('scanner-status');

                    if (!video) return;

                    // Check for secure context
                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        if (status) {
                            status.textContent = '❌ Camera requires HTTPS. Please access this page via https://';
                            status.style.color = '#dc2626';
                        }
                        frappe.msgprint(__('Camera access requires a secure connection (HTTPS). Please access this page via https:// instead of http://'));
                        return;
                    }

                    // Load jsQR first, then start camera
                    loadJsQR(function() {
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
                                // Start scanning frames
                                startFrameScan(video, status);
                            })
                            .catch(function(err) {
                                if (status) {
                                    status.textContent = '❌ Camera access denied: ' + err.message;
                                    status.style.color = '#dc2626';
                                }
                                frappe.msgprint(__('Camera access denied: {0}', [err.message]));
                            });
                    });
                }

                function startFrameScan(video, status) {
                    var canvas = document.getElementById('qr-canvas');
                    if (!canvas) return;
                    var ctx = canvas.getContext('2d');

                    // Clear any existing interval
                    if (scanInterval) {
                        clearInterval(scanInterval);
                    }

                    scanInterval = setInterval(function() {
                        if (!video || video.readyState !== video.HAVE_ENOUGH_DATA || !scannerStream) {
                            return;
                        }

                        // Match canvas size to video
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;

                        // Draw the video frame to the canvas
                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                        // Get image data for QR decoding
                        var imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

                        try {
                            var code = jsQR(imageData.data, imageData.width, imageData.height, {
                                inversionAttempts: 'dontInvert'
                            });

                            if (code && code.data) {
                                // QR code detected!
                                if (status) {
                                    status.textContent = '✅ QR Code detected! Processing...';
                                    status.style.color = '#16a34a';
                                }

                                // Stop scanning
                                stopScanner();

                                // Process the QR code data
                                processQRCode(code.data, frm, d, status);
                            }
                        } catch(e) {
                            // jsQR throws on some edge cases, ignore
                        }
                    }, 500); // Check every 500ms
                }

                function processQRCode(qrData, frm, dialog, status) {
                    // Try to parse as JSON (ASN QR codes are JSON)
                    var payload;
                    try {
                        payload = JSON.parse(qrData);
                    } catch(e) {
                        // Not JSON — treat as raw text
                        payload = { doc_type: 'Raw', doc_id: qrData };
                    }

                    // Call the server API to process the scan
                    frappe.call({
                        method: 'supplier_portal.api.gate_entry.scan_qr',
                        args: {
                            qr_data: JSON.stringify(payload)
                        },
                        callback: function(r) {
                            if (r.message && r.message.success) {
                                frappe.show_alert({
                                    message: __('Gate entry created: {0}', [r.message.gate_entry]),
                                    indicator: 'green'
                                });
                                if (status) {
                                    status.textContent = '✅ Gate entry created!';
                                    status.style.color = '#16a34a';
                                }
                                dialog.hide();
                                frappe.set_route('Form', 'Gate Entry', r.message.gate_entry);
                            } else {
                                var errMsg = (r.message && r.message.message) || 'Unknown error';
                                if (status) {
                                    status.textContent = '❌ Error: ' + errMsg;
                                    status.style.color = '#dc2626';
                                }
                                frappe.msgprint(__('Scan failed: {0}', [errMsg]));
                            }
                        },
                        error: function(err) {
                            if (status) {
                                status.textContent = '❌ Server error: ' + err.message;
                                status.style.color = '#dc2626';
                            }
                            frappe.msgprint(__('Server error: {0}', [err.message]));
                        }
                    });
                }

                function stopScanner() {
                    if (scanInterval) {
                        clearInterval(scanInterval);
                        scanInterval = null;
                    }
                    if (scannerStream) {
                        scannerStream.getTracks().forEach(function(t) { t.stop(); });
                        scannerStream = null;
                    }
                    var video = document.getElementById('qr-video');
                    var placeholder = document.getElementById('qr-placeholder');
                    var status = document.getElementById('scanner-status');
                    if (video) video.style.display = 'none';
                    if (placeholder) placeholder.style.display = 'block';
                    document.getElementById('start-scanner-btn').style.display = 'inline-block';
                    document.getElementById('stop-scanner-btn').style.display = 'none';
                    if (status && status.textContent.indexOf('✅') === -1) {
                        status.textContent = 'Camera stopped';
                        status.style.color = '#64748b';
                    }
                }

                d.show();

                // Attach scanner button handlers
                d.$wrapper.find('#start-scanner-btn').on('click', startScanner);
                d.$wrapper.find('#stop-scanner-btn').on('click', stopScanner);

                // Clean up camera when dialog is dismissed
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
                        var asn = r.message;
                        frm.set_value('supplier', asn.supplier);
                        frm.set_value('supplier_name', asn.supplier_name);
                        frm.set_value('vehicle_no', asn.vehicle_no);
                        frm.set_value('driver_name', asn.driver_name);
                        frm.set_value('driver_mobile', asn.driver_mobile);
                        frm.set_value('lr_no', asn.lr_no);
                        frm.set_value('transport_company', asn.transport_company);
                        frm.set_value('num_packages', asn.num_packages);

                        // Auto-populate items from ASN
                        frm.clear_table('items');
                        if (asn.items && asn.items.length) {
                            asn.items.forEach(function(asn_item) {
                                var row = frm.add_child('items');
                                row.item_code = asn_item.item_code;
                                row.item_name = asn_item.item_name;
                                row.po_detail = asn_item.po_detail;
                                row.uom = asn_item.uom;
                                row.dispatch_qty = asn_item.dispatch_qty;
                                row.received_qty = asn_item.dispatch_qty;
                                row.batch_no = asn_item.batch_no;
                                row.manufacturing_date = asn_item.manufacturing_date;
                                row.expiry_date = asn_item.expiry_date;
                                row.serial_nos = asn_item.serial_nos;
                            });
                            frm.refresh_field('items');
                        }
                    }
                }
            });
        } else {
            frm.clear_table('items');
            frm.refresh_field('items');
        }
    },

    unloading_start_time: function(frm) {
        if (frm.doc.unloading_start_time) {
            frm.set_value('unloading_end_time', '');
            if (frm.doc.status === 'At Gate' || frm.doc.status === 'Waiting for Unloading') {
                frm.set_value('status', 'Unloading');
            }
        }
    },

    unloading_end_time: function(frm) {
        if (frm.doc.unloading_end_time && frm.doc.unloading_start_time) {
            frm.call('calculate_unloading_duration', {}, function(r) {});
            frm.set_value('status', 'Completed');
        }
    }
});
