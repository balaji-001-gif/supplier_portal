# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def get_context(context):
    """ASN list page"""
    context.no_cache = 1

    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Please login"), frappe.PermissionError)

    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not user_supplier:
        frappe.throw(frappe._("Access denied"), frappe.PermissionError)

    context.supplier = user_supplier

    # Get ASNs with optional status filter
    filters = {"supplier": user_supplier}
    status = frappe.form_dict.get("status")
    if status:
        filters["status"] = status

    context.asns = frappe.get_all(
        "Advance Shipment Notice",
        filters=filters,
        fields=[
            "name", "asn_date", "purchase_order", "expected_delivery_date",
            "vehicle_no", "num_packages", "status", "docstatus"
        ],
        order_by="asn_date desc"
    )

    context.statuses = ["Draft", "Submitted", "In Transit", "At Gate", "Unloading", "Received", "Cancelled"]
    return context
