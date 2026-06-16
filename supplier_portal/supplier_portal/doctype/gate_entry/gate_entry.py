# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_seconds


class GateEntry(Document):
    def validate(self):
        self.calculate_unloading_duration()
        self.set_gate_guard()

    def before_submit(self):
        self.update_asn_status()

    def on_submit(self):
        # Note: Purchase Receipt is NOT auto-created here.
        # The warehouse team creates PR manually based on actual received quantities
        # referencing the Gate Entry and Purchase Order.
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
