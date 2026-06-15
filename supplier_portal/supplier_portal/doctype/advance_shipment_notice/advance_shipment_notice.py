# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import json
from frappe.model.document import Document
from frappe.utils import now_datetime


class AdvanceShipmentNotice(Document):
    def validate(self):
        self.validate_supplier_permission()
        self.validate_purchase_order()
        self.validate_dispatch_quantities()
        self.calculate_short_excess()

    def before_submit(self):
        self.generate_package_qr_codes()
        self.status = "Submitted"
        self.submitted_by = frappe.session.user
        self.submitted_on = now_datetime()

    def on_submit(self):
        self.send_notification_to_warehouse()
        self.send_notification_to_supplier()

    def on_cancel(self):
        self.status = "Cancelled"

    def validate_supplier_permission(self):
        """Ensure supplier can only create ASN for their own POs"""
        if frappe.session.user == "Administrator":
            return
        user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
        if user_supplier and user_supplier != self.supplier:
            frappe.throw(
                frappe._("You can only create ASN for your own purchase orders")
            )

    def validate_purchase_order(self):
        """Validate PO exists and belongs to supplier"""
        if not self.purchase_order:
            return
        po = frappe.get_doc("Purchase Order", self.purchase_order)
        if po.supplier != self.supplier:
            frappe.throw(
                frappe._(
                    "Purchase Order {0} does not belong to supplier {1}"
                ).format(self.purchase_order, self.supplier)
            )
        if po.docstatus != 1:
            frappe.throw(
                frappe._("Purchase Order {0} is not submitted").format(self.purchase_order)
            )
        if not self.supplier:
            self.supplier = po.supplier
            self.supplier_name = po.supplier_name

    def validate_dispatch_quantities(self):
        """Ensure dispatch qty doesn't exceed pending PO qty"""
        for item in self.items:
            if not item.po_detail:
                continue
            po_item = frappe.get_doc("Purchase Order Item", item.po_detail)
            dispatched_qty = frappe.db.sql("""
                SELECT COALESCE(SUM(asn_item.dispatch_qty), 0)
                FROM `tabASN Item` asn_item
                INNER JOIN `tabAdvance Shipment Notice` asn
                    ON asn.name = asn_item.parent
                WHERE asn_item.po_detail = %s
                    AND asn.docstatus = 1
                    AND asn.name != %s
            """, (item.po_detail, self.name))[0][0]
            pending_qty = po_item.qty - po_item.received_qty - dispatched_qty
            if item.dispatch_qty > pending_qty:
                frappe.throw(
                    frappe._(
                        "Row #{0}: Dispatch qty {1} exceeds pending qty {2} "
                        "for item {3}"
                    ).format(item.idx, item.dispatch_qty, pending_qty, item.item_code)
                )
            item.po_qty = po_item.qty

    def calculate_short_excess(self):
        """Calculate short/excess quantities after receipt"""
        for item in self.items:
            if item.received_qty:
                variance = item.received_qty - item.dispatch_qty
                if variance < 0:
                    item.short_qty = abs(variance)
                    item.excess_qty = 0
                elif variance > 0:
                    item.short_qty = 0
                    item.excess_qty = variance
                else:
                    item.short_qty = 0
                    item.excess_qty = 0

    def generate_package_qr_codes(self):
        """Generate QR code payload for each package"""
        if not self.packages:
            for i in range(self.num_packages or 1):
                self.append("packages", {
                    "package_id": "PKG-{0:02d}".format(i + 1),
                    "package_type": "Carton"
                })
        for pkg in self.packages:
            if not pkg.qr_generated:
                qr_data = self.get_qr_payload(pkg)
                pkg.qr_code = json.dumps(qr_data, indent=2)
                pkg.qr_generated = 1

    def get_qr_payload(self, package):
        """Build QR code payload with all required data"""
        items_data = []
        for item in self.items:
            items_data.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "dispatch_qty": item.dispatch_qty,
                "uom": item.uom,
                "batch_no": item.batch_no,
                "manufacturing_date": str(item.manufacturing_date) if item.manufacturing_date else None,
                "expiry_date": str(item.expiry_date) if item.expiry_date else None,
                "serial_nos": item.serial_nos
            })
        return {
            "doc_type": "Advance Shipment Notice",
            "doc_id": self.name,
            "asn_date": str(self.asn_date),
            "supplier_id": self.supplier,
            "supplier_name": self.supplier_name,
            "po_no": self.purchase_order,
            "vehicle_no": self.vehicle_no,
            "driver_name": self.driver_name,
            "driver_mobile": self.driver_mobile,
            "package_id": package.package_id,
            "package_type": package.package_type,
            "num_packages": self.num_packages,
            "challan_no": self.delivery_challan_no,
            "challan_date": str(self.challan_date),
            "eta_date": str(self.expected_delivery_date),
            "eta_time": str(self.expected_arrival_time) if self.expected_arrival_time else None,
            "items": items_data,
            "scan_url": frappe.utils.get_url(
                "/api/method/supplier_portal.api.gate_entry.scan_qr"
            )
        }

    def send_notification_to_warehouse(self):
        """Notify warehouse team of incoming shipment"""
        recipients = frappe.get_all(
            "User",
            filters={"enabled": 1},
            fields=["email"],
            or_filters=[
                {"role_profile_name": ["in", ["Warehouse Staff", "Stock Manager", "Stock User"]]}
            ]
        )
        if not recipients:
            return
        frappe.sendmail(
            recipients=[r.email for r in recipients],
            subject=frappe._("New ASN Submitted: {0}").format(self.name),
            template="asn_submitted",
            args={"doc": self, "items": self.items, "packages": self.packages},
            now=True
        )

    def send_notification_to_supplier(self):
        """Send confirmation to supplier"""
        supplier_email = frappe.db.get_value("Supplier", self.supplier, "email_id")
        if not supplier_email:
            return
        portal_link = frappe.utils.get_url("/supplier_portal/asn/{0}".format(self.name))
        frappe.sendmail(
            recipients=[supplier_email],
            subject=frappe._("ASN Submitted Successfully: {0}").format(self.name),
            message=frappe.render_template(
                "supplier_portal/templates/emails/asn_submitted.html",
                {"doc": self, "portal_link": portal_link}
            ),
            now=True
        )

    @frappe.whitelist()
    def generate_qr_image(self, package_id):
        """Generate QR code image for a specific package"""
        import io
        import base64
        import qrcode
        from qrcode.image.pil import PilImage

        package = None
        for pkg in self.packages:
            if pkg.package_id == package_id:
                package = pkg
                break
        if not package or not package.qr_code:
            frappe.throw(frappe._("Package not found or QR not generated"))
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(package.qr_code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return "data:image/png;base64,{0}".format(img_str)


@frappe.whitelist()
def get_supplier_purchase_orders(supplier=None):
    """Get open purchase orders for supplier portal"""
    if not supplier:
        supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not supplier:
        return []
    return frappe.get_all(
        "Purchase Order",
        filters={
            "supplier": supplier,
            "docstatus": 1,
            "status": ["not in", ["Closed", "Completed", "Cancelled"]],
            "per_received": ["<", 100]
        },
        fields=[
            "name", "transaction_date", "schedule_date",
            "grand_total", "currency", "per_received", "status"
        ],
        order_by="transaction_date desc"
    )


@frappe.whitelist()
def get_po_items(purchase_order):
    """Get items from a purchase order for ASN creation"""
    if not purchase_order:
        return []
    po = frappe.get_doc("Purchase Order", purchase_order)
    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if user_supplier and user_supplier != po.supplier and frappe.session.user != "Administrator":
        frappe.throw(frappe._("You don't have permission to access this Purchase Order"))
    items = []
    for item in po.items:
        pending_qty = item.qty - item.received_qty
        items.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "po_detail": item.name,
            "po_qty": item.qty,
            "uom": item.uom,
            "received_qty": item.received_qty,
            "pending_qty": pending_qty,
            "rate": item.rate,
            "amount": item.amount
        })
    return items
