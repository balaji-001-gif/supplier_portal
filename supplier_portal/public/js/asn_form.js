// ASN Form Helper for Supplier Portal
// Used on the /supplier_portal/asn/new page

frappe.provide('frappe.supplier_portal.asn');

frappe.supplier_portal.asn = {
    currentPO: null,
    items: [],

    init: function() {
        this.bind_events();
    },

    bind_events: function() {
        var self = this;

        // PO Selection Change
        $(document).on('change', '#asn-po-select', function() {
            var po = $(this).val();
            if (po) {
                self.loadPOItems(po);
            } else {
                $('#items-container').html('<p class="text-muted">Select a Purchase Order to load items</p>');
            }
        });

        // Auto-calculate number of packages
        $(document).on('change', '#asn-num-packages', function() {
            var count = parseInt($(this).val()) || 0;
            var container = $('#packages-preview');
            container.empty();

            for (var i = 1; i <= count; i++) {
                container.append(
                    '<div class="package-chip">' +
                    '<span class="package-id">Pkg ' + String(i).padStart(2, '0') + '</span>' +
                    '<span class="package-status text-muted">QR on submit</span>' +
                    '</div>'
                );
            }
        });
    },

    loadPOItems: function(po) {
        var self = this;

        frappe.call({
            method: 'supplier_portal.api.asn.get_asn_items',
            args: { purchase_order: po },
            callback: function(r) {
                if (r.message) {
                    self.items = r.message;
                    self.renderItems(r.message);
                }
            }
        });
    },

    renderItems: function(items) {
        var container = $('#items-container');
        container.empty();

        items.forEach(function(item, idx) {
            var pending = item.qty - (item.received_qty || 0);
            container.append(
                '<div class="item-row" data-idx="' + idx + '">' +
                '<div class="item-header">' +
                '<div><strong>' + item.item_name + '</strong></div>' +
                '<div class="text-muted">' + item.item_code + ' | PO Qty: ' + item.qty + ' ' + item.uom + '</div>' +
                '</div>' +
                '<div class="item-fields">' +
                '<div class="form-group">' +
                '<label>Dispatch Qty *</label>' +
                '<input type="number" class="form-control dispatch-qty" value="' + pending + '" min="0" step="0.01">' +
                '</div>' +
                '<div class="form-group">' +
                '<label>Batch No. *</label>' +
                '<input type="text" class="form-control batch-no" placeholder="BATCH-...">' +
                '</div>' +
                '<div class="form-group">' +
                '<label>Mfg Date</label>' +
                '<input type="date" class="form-control mfg-date">' +
                '</div>' +
                '<div class="form-group">' +
                '<label>Expiry Date</label>' +
                '<input type="date" class="form-control expiry-date">' +
                '</div>' +
                '</div>' +
                '</div>'
            );
        });
    },

    collectFormData: function() {
        var data = {
            purchase_order: $('#asn-po-select').val(),
            asn_date: $('#asn-date').val(),
            expected_delivery_date: $('#asn-eta-date').val(),
            expected_arrival_time: $('#asn-eta-time').val() || null,
            delivery_challan_no: $('#asn-challan-no').val(),
            challan_date: $('#asn-challan-date').val(),
            num_packages: parseInt($('#asn-num-packages').val()) || 1,
            eway_bill_no: $('#asn-eway-bill').val(),
            lr_no: $('#asn-lr-no').val(),
            vehicle_no: $('#asn-vehicle-no').val(),
            driver_name: $('#asn-driver-name').val(),
            driver_mobile: $('#asn-driver-mobile').val(),
            transport_company: $('#asn-transport').val(),
            remarks: $('#asn-remarks').val(),
            items: []
        };

        $('.item-row').each(function() {
            var idx = $(this).data('idx');
            if (frappe.supplier_portal.asn.items[idx]) {
                data.items.push({
                    item_code: frappe.supplier_portal.asn.items[idx].item_code,
                    po_detail: frappe.supplier_portal.asn.items[idx].name,
                    dispatch_qty: parseFloat($(this).find('.dispatch-qty').val()) || 0,
                    batch_no: $(this).find('.batch-no').val(),
                    manufacturing_date: $(this).find('.mfg-date').val() || null,
                    expiry_date: $(this).find('.expiry-date').val() || null
                });
            }
        });

        return data;
    }
};

$(document).ready(function() {
    frappe.supplier_portal.asn.init();
});
