# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import json


@frappe.whitelist()
def submit_invoice(data):
    """Submit invoice from supplier portal"""
    try:
        data = json.loads(data) if isinstance(data, str) else data
        user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
        if not user_supplier and frappe.session.user != "Administrator":
            frappe.throw(frappe._("You don't have permission to submit invoices"))

        inv = frappe.new_doc("Supplier Invoice Submission")
        inv.update(data)
        if user_supplier:
            inv.supplier = user_supplier
        inv.status = "Pending Approval"
        inv.save()

        return {
            "success": True,
            "invoice": inv.name,
            "message": frappe._("Invoice submitted for approval")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Invoice Submission Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_supplier_invoices(filters=None):
    """Get invoices for supplier portal"""
    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not user_supplier and frappe.session.user != "Administrator":
        return []

    base_filters = {"supplier": user_supplier} if user_supplier else {}
    if filters:
        base_filters.update(json.loads(filters) if isinstance(filters, str) else filters)

    return frappe.get_all(
        "Supplier Invoice Submission",
        filters=base_filters,
        fields=[
            "name", "invoice_number", "invoice_date", "invoice_amount",
            "purchase_receipt", "status", "submission_date",
            "purchase_invoice", "pi_status"
        ],
        order_by="submission_date desc"
    )
