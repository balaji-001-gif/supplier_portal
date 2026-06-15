# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.utils import now_datetime


def update_asn_eta_status():
    """Update ASN status based on expected delivery dates"""
    now = now_datetime()

    # Update ASNs that are due for delivery today
    due_asns = frappe.get_all(
        "Advance Shipment Notice",
        filters={
            "status": "Submitted",
            "expected_delivery_date": now.date(),
            "docstatus": 1
        }
    )

    for asn_name in due_asns:
        frappe.db.set_value("Advance Shipment Notice", asn_name, "status", "In Transit")

    # Update ASNs that have passed delivery date without gate entry
    overdue_asns = frappe.get_all(
        "Advance Shipment Notice",
        filters={
            "status": ["in", ["Submitted", "In Transit"]],
            "expected_delivery_date": ["<", now.date()],
            "docstatus": 1
        }
    )

    for asn_name in overdue_asns:
        # Check if gate entry exists
        gate_entry = frappe.db.get_value(
            "Gate Entry",
            {"asn_reference": asn_name},
            "name"
        )
        if not gate_entry:
            frappe.db.set_value("Advance Shipment Notice", asn_name, "status", "In Transit")
