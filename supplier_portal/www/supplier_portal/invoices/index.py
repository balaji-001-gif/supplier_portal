# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def get_context(context):
    """Invoices list and submission page"""
    context.no_cache = 1

    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Please login"), frappe.PermissionError)

    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not user_supplier:
        frappe.throw(frappe._("Access denied"), frappe.PermissionError)

    context.supplier = user_supplier

    # Get submitted invoices
    context.invoices = frappe.get_all(
        "Supplier Invoice Submission",
        filters={"supplier": user_supplier},
        fields=[
            "name", "invoice_number", "invoice_date", "invoice_amount",
            "purchase_receipt", "status", "submission_date",
            "purchase_invoice", "pi_status"
        ],
        order_by="submission_date desc"
    )

    # Get available PRs for new invoice submission
    context.available_prs = frappe.get_all(
        "Purchase Receipt",
        filters={
            "supplier": user_supplier,
            "docstatus": 1
        },
        fields=["name", "posting_date", "grand_total", "currency"],
        order_by="posting_date desc"
    )

    return context
