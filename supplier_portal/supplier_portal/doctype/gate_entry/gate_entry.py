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


# API endpoints (scan_qr, get_gate_queue, create_gate_entry_from_asn) are in supplier_portal/api/gate_entry.py
