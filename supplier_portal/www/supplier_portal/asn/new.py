# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def get_context(context):
    """ASN creation form page"""
    context.no_cache = 1

    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Please login"), frappe.PermissionError)

    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not user_supplier:
        frappe.throw(frappe._("Access denied"), frappe.PermissionError)

    context.supplier = user_supplier

    # Get open POs for this supplier
    context.purchase_orders = frappe.get_all(
        "Purchase Order",
        filters={
            "supplier": user_supplier,
            "docstatus": 1,
            "status": ["not in", ["Closed", "Completed", "Cancelled"]],
            "per_received": ["<", 100]
        },
        fields=["name", "transaction_date", "schedule_date", "grand_total", "currency"],
        order_by="transaction_date desc"
    )

    return context
