# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def get_context(context):
    """Supplier queries page"""
    context.no_cache = 1

    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Please login"), frappe.PermissionError)

    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not user_supplier:
        frappe.throw(frappe._("Access denied"), frappe.PermissionError)

    context.supplier = user_supplier

    # Get queries
    filters = {"supplier": user_supplier}
    status = frappe.form_dict.get("status")
    if status:
        filters["status"] = status

    context.queries = frappe.get_all(
        "Supplier Query",
        filters=filters,
        fields=[
            "name", "subject", "query_category", "status",
            "submitted_on", "responded_on", "priority", "response"
        ],
        order_by="submitted_on desc"
    )

    context.statuses = ["Open", "Responded", "Closed"]
    return context
