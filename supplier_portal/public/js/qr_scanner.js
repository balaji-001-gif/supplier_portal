// QR Scanner for Supplier Portal Gate Entry
// This file is included on all supplier portal web pages for QR scanning capability

frappe.provide('frappe.supplier_portal.qr');

frappe.supplier_portal.qr = {
    scannerStream: null,
    isScanning: false,

    init: function() {
        this.bind_events();
    },

    bind_events: function() {
        var self = this;

        // Listen for QR scan button clicks
        $(document).on('click', '[data-action="start-qr-scan"]', function() {
            self.startCamera($(this).data('target') || '#qr-video');
        });

        $(document).on('click', '[data-action="stop-qr-scan"]', function() {
            self.stopCamera();
        });
    },

    startCamera: function(videoSelector) {
        var self = this;
        var video = $(videoSelector)[0];

        if (!video) {
            frappe.msgprint(__('QR video element not found'));
            return;
        }

        if (self.isScanning) {
            frappe.msgprint(__('Scanner is already running'));
            return;
        }

        // Check for camera support
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            frappe.msgprint(__('Camera access is not supported on this device'));
            return;
        }

        navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
        }).then(function(stream) {
            self.scannerStream = stream;
            self.isScanning = true;
            video.srcObject = stream;
            video.play();

            // Show the video element and hide the placeholder
            $(videoSelector).show();
            $('#qr-placeholder').hide();

            // Show stop button, hide start button
            $('[data-action="start-qr-scan"]').hide();
            $('[data-action="stop-qr-scan"]').show();
            $('.qr-status').text(__('Camera active. Point at QR code.')).removeClass('text-danger').addClass('text-success');

            // Here you would integrate a QR decoding library like jsQR
            // Example: scanFrame() with requestAnimationFrame

        }).catch(function(err) {
            frappe.msgprint(__('Camera access denied. Error: ') + err.message);
            $('.qr-status').text(__('Camera access denied')).removeClass('text-success').addClass('text-danger');
        });
    },

    stopCamera: function() {
        if (this.scannerStream) {
            this.scannerStream.getTracks().forEach(function(track) {
                track.stop();
            });
            this.scannerStream = null;
        }
        this.isScanning = false;

        // Hide the video element and show the placeholder
        $('#qr-video').hide();
        $('#qr-placeholder').show();

        // Show start button, hide stop button
        $('[data-action="start-qr-scan"]').show();
        $('[data-action="stop-qr-scan"]').hide();
        $('.qr-status').text(__('Camera stopped')).removeClass('text-success text-danger');
    },

    // Process scanned QR code data by calling the server API
    processScan: function(qrData) {
        var self = this;

        if (!qrData) {
            frappe.msgprint(__('No QR code data found'));
            return;
        }

        frappe.call({
            method: 'supplier_portal.api.gate_entry.scan_qr',
            args: {
                qr_data: qrData
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    self.stopCamera();
                    frappe.show_alert({
                        message: __('Gate entry created: {0}', [r.message.gate_entry]),
                        indicator: 'green'
                    });
                    // Redirect to the gate entry form
                    frappe.set_route('Form', 'Gate Entry', r.message.gate_entry);
                } else {
                    frappe.msgprint(__('Scan failed: ') + (r.message.message || 'Unknown error'));
                }
            },
            error: function(err) {
                frappe.msgprint(__('Server error: ') + err.message);
            }
        });
    }
};

// Initialize on document ready
$(document).ready(function() {
    frappe.supplier_portal.qr.init();
});
