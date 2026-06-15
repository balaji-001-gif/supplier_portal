# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import json
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_seconds


class GateEntry(Document):
    def validate(self):
        self.calculate_unloading_duration()
        self.set_gate_guard()

    def before_submit(self):
        self.update_asn_status()

    def on_submit(self):
        self.create_purchase_receipt_draft()
        self.send_gate_entry_notification()

    def on_cancel(self):
        if self.asn_reference:
            frappe.db.set_value("Advance Shipment Notice", self.asn_reference, "status", "Submitted")

    def set_gate_guard(self):
        if not self.gate_guard:
            self.gate_guard = frappe.session.user

    def calculate_unloading_duration(self):
        if self.unloading_start_time and self.unloading_end_time:
            duration_seconds = time_diff_in_seconds(
                self.unloading_end_time, self.unloading_start_time
            )
            self.unloading_duration = duration_seconds / 60

    def update_asn_status(self):
        if self.asn_reference:
            asn = frappe.get_doc("Advance Shipment Notice", self.asn_reference)
            asn.db_set("status", "At Gate")
            if self.scanned_package_id:
                for pkg in asn.packages:
                    if pkg.package_id == self.scanned_package_id:
                        pkg.db_set("scanned_at_gate", 1)
                        pkg.db_set("scan_timestamp", self.scan_timestamp or now_datetime())
                        pkg.db_set("package_status", "At Gate")

    def create_purchase_receipt_draft(self):
        """Auto-create Purchase Receipt from Gate Entry"""
        if not self.asn_reference:
            return
        asn = frappe.get_doc("Advance Shipment Notice", self.asn_reference)
        pr = frappe.new_doc("Purchase Receipt")
        pr.supplier = self.supplier
        pr.posting_date = self.entry_date
        pr.posting_time = self.entry_time
        pr.set_posting_time = 1
        pr.bill_no = asn.delivery_challan_no
        pr.bill_date = asn.challan_date
        pr.lr_no = self.lr_no
        pr.transporter_name = self.transport_company

        # Custom fields on PR (added via fixtures)
        pr.db_set("gate_entry_reference", self.name)
        pr.db_set("asn_reference", self.asn_reference)

        for asn_item in asn.items:
            pr.append("items", {
                "item_code": asn_item.item_code,
                "item_name": asn_item.item_name,
                "qty": asn_item.dispatch_qty,
                "uom": asn_item.uom,
                "purchase_order": asn.purchase_order,
                "purchase_order_item": asn_item.po_detail,
                "batch_no": asn_item.batch_no,
                "manufacturing_date": asn_item.manufacturing_date,
                "expiry_date": asn_item.expiry_date,
                "serial_no": asn_item.serial_nos
            })
        pr.save(ignore_permissions=True)
        self.db_set("purchase_receipt", pr.name)
        self.db_set("pr_status", "Draft")
        frappe.msgprint(frappe._("Purchase Receipt {0} created successfully").format(pr.name))

    def send_gate_entry_notification(self):
        """Notify warehouse team about new gate entry"""
        warehouse_users = frappe.get_all(
            "User",
            filters={"enabled": 1},
            fields=["email"],
            or_filters=[
                {"role_profile_name": ["in", ["Warehouse Staff", "Stock Manager"]]}
            ]
        )
        if warehouse_users:
            frappe.sendmail(
                recipients=[u.email for u in warehouse_users],
                subject=frappe._("New Gate Entry: {0} - {1}").format(self.name, self.supplier_name),
                message=frappe._(
                    "Vehicle {0} has arrived at gate. ASN: {1}, Packages: {2}"
                ).format(self.vehicle_no, self.asn_reference, self.num_packages),
                now=True
            )


@frappe.whitelist()
def scan_qr(qr_data):
    """Process QR code scan at gate"""
    try:
        if isinstance(qr_data, str):
            data = json.loads(qr_data)
        else:
            data = qr_data
    except Exception:
        frappe.throw(frappe._("Invalid QR code data"))

    if data.get("doc_type") != "Advance Shipment Notice":
        frappe.throw(frappe._("Invalid QR code: Not an ASN QR code"))

    asn_name = data.get("doc_id")
    if not frappe.db.exists("Advance Shipment Notice", asn_name):
        frappe.throw(frappe._("ASN {0} not found").format(asn_name))

    asn = frappe.get_doc("Advance Shipment Notice", asn_name)
    if asn.docstatus != 1:
        frappe.throw(frappe._("ASN is not submitted"))

    # Create or update Gate Entry
    gate_entry_name = frappe.db.get_value(
        "Gate Entry",
        {"asn_reference": asn_name, "docstatus": 0}
    )

    if gate_entry_name:
        gate_entry = frappe.get_doc("Gate Entry", gate_entry_name)
    else:
        gate_entry = frappe.new_doc("Gate Entry")
        gate_entry.asn_reference = asn_name
        gate_entry.supplier = data.get("supplier_id")
        gate_entry.supplier_name = data.get("supplier_name")
        gate_entry.vehicle_no = data.get("vehicle_no")
        gate_entry.driver_name = data.get("driver_name")
        gate_entry.driver_mobile = data.get("driver_mobile")
        gate_entry.lr_no = asn.lr_no
        gate_entry.transport_company = asn.transport_company
        gate_entry.num_packages = data.get("num_packages")
        gate_entry.entry_date = frappe.utils.nowdate()
        gate_entry.entry_time = frappe.utils.nowtime()

    gate_entry.scanned_package_id = data.get("package_id")
    gate_entry.scan_timestamp = now_datetime()
    gate_entry.gate_guard = frappe.session.user
    gate_entry.save(ignore_permissions=True)

    return {
        "success": True,
        "gate_entry": gate_entry.name,
        "asn": asn_name,
        "supplier": asn.supplier_name,
        "vehicle": asn.vehicle_no,
        "packages": asn.num_packages,
        "items": [{"item_code": item.item_code, "qty": item.dispatch_qty} for item in asn.items]
    }


@frappe.whitelist()
def get_gate_queue():
    """Get current gate queue for warehouse view"""
    return frappe.get_all(
        "Gate Entry",
        filters={"docstatus": 0, "status": ["in", ["At Gate", "Waiting for Unloading"]]},
        fields=[
            "name", "entry_date", "entry_time", "supplier",
            "supplier_name", "vehicle_no", "asn_reference",
            "status", "num_packages"
        ],
        order_by="entry_date, entry_time"
    )


@frappe.whitelist()
def create_gate_entry_from_asn(asn_data):
    """Mapped doc method to create Gate Entry from ASN"""
    if isinstance(asn_data, str):
        asn_data = json.loads(asn_data)

    # Create a new Gate Entry and pre-fill from ASN
    gate_entry = frappe.new_doc("Gate Entry")
    gate_entry.asn_reference = asn_data.get("name")
    gate_entry.supplier = asn_data.get("supplier")
    gate_entry.supplier_name = asn_data.get("supplier_name")
    gate_entry.vehicle_no = asn_data.get("vehicle_no")
    gate_entry.driver_name = asn_data.get("driver_name")
    gate_entry.driver_mobile = asn_data.get("driver_mobile")
    gate_entry.lr_no = asn_data.get("lr_no")
    gate_entry.transport_company = asn_data.get("transport_company")
    gate_entry.num_packages = asn_data.get("num_packages")
    return gate_entry
