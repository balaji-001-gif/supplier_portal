# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def get_context(context):
    """Scorecard view page"""
    context.no_cache = 1

    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Please login"), frappe.PermissionError)

    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not user_supplier:
        frappe.throw(frappe._("Access denied"), frappe.PermissionError)

    context.supplier = user_supplier

    context.scorecards = frappe.get_all(
        "Supplier Scorecard",
        filters={"supplier": user_supplier},
        fields=[
            "name", "fiscal_year_start", "overall_score", "rating",
            "on_time_delivery_rate", "quality_acceptance_rate",
            "documentation_compliance_rate", "invoice_accuracy_rate"
        ],
        order_by="fiscal_year_start desc"
    )

    return context
