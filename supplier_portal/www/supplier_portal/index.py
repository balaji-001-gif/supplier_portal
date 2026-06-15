# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def get_context(context):
    """Supplier portal dashboard home page"""
    context.no_cache = 1

    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Please login to access supplier portal"), frappe.PermissionError)

    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not user_supplier:
        frappe.throw(frappe._("You don't have supplier portal access"), frappe.PermissionError)

    context.supplier = frappe.get_doc("Supplier", user_supplier)

    # Dashboard statistics
    context.stats = {
        "open_pos": frappe.db.count("Purchase Order", {
            "supplier": user_supplier,
            "docstatus": 1,
            "status": ["not in", ["Closed", "Completed"]]
        }),
        "pending_asns": frappe.db.count("Advance Shipment Notice", {
            "supplier": user_supplier,
            "status": ["in", ["Draft", "Submitted", "In Transit"]]
        }),
        "pending_invoices": frappe.db.count("Supplier Invoice Submission", {
            "supplier": user_supplier,
            "status": ["in", ["Draft", "Pending Approval"]]
        }),
        "this_month_deliveries": frappe.db.count("Purchase Receipt", {
            "supplier": user_supplier,
            "docstatus": 1,
            "posting_date": [">=", frappe.utils.nowdate()[:8] + "01"]
        })
    }

    # Recent ASNs
    context.recent_asns = frappe.get_all(
        "Advance Shipment Notice",
        filters={"supplier": user_supplier},
        fields=["name", "asn_date", "purchase_order", "status", "expected_delivery_date"],
        order_by="asn_date desc",
        limit=5
    )

    # Recent POs
    context.recent_pos = frappe.get_all(
        "Purchase Order",
        filters={"supplier": user_supplier, "docstatus": 1},
        fields=["name", "transaction_date", "grand_total", "currency", "status"],
        order_by="transaction_date desc",
        limit=5
    )

    # Open queries count
    context.open_queries = frappe.db.count("Supplier Query", {
        "supplier": user_supplier,
        "status": ["in", ["Open", "Responded"]]
    })

    # Latest scorecard
    context.latest_scorecard = frappe.get_all(
        "Supplier Scorecard",
        filters={"supplier": user_supplier},
        fields=["overall_score", "rating"],
        order_by="fiscal_year_start desc",
        limit=1
    )

    return context
