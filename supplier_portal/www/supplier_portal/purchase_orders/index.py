# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def get_context(context):
    """Purchase Orders list page"""
    context.no_cache = 1

    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Please login"), frappe.PermissionError)

    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not user_supplier:
        frappe.throw(frappe._("Access denied"), frappe.PermissionError)

    context.supplier = user_supplier

    context.purchase_orders = frappe.get_all(
        "Purchase Order",
        filters={
            "supplier": user_supplier,
            "docstatus": 1
        },
        fields=[
            "name", "transaction_date", "schedule_date", "grand_total",
            "currency", "per_received", "status", "per_billed"
        ],
        order_by="transaction_date desc"
    )

    return context
