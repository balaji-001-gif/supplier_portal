# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def get_context(context):
    """Router: dispatches to the correct page handler based on URL path"""
    context.no_cache = 1

    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Please login to access supplier portal"), frappe.PermissionError)

    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not user_supplier:
        frappe.throw(frappe._("You don't have supplier portal access"), frappe.PermissionError)

    context.supplier = user_supplier
    context.supplier_doc = frappe.get_doc("Supplier", user_supplier)

    # Determine which page to show from the URL path
    path = frappe.form_dict.get("app_path", "")
    context.current_page = "dashboard"

    if not path or path == "":
        _set_dashboard_context(context, user_supplier)
    elif path == "asn":
        context.current_page = "asn"
        _set_asn_list_context(context, user_supplier)
    elif path == "asn/new":
        context.current_page = "asn_new"
        _set_asn_new_context(context, user_supplier)
    elif path and path.startswith("asn/"):
        context.current_page = "asn_detail"
        _set_asn_detail_context(context, user_supplier, path.replace("asn/", ""))
    elif path == "invoices":
        context.current_page = "invoices"
        _set_invoices_context(context, user_supplier)
    elif path == "purchase_orders":
        context.current_page = "purchase_orders"
        _set_purchase_orders_context(context, user_supplier)
    elif path == "queries":
        context.current_page = "queries"
        _set_queries_context(context, user_supplier)
    elif path == "scorecard":
        context.current_page = "scorecard"
        _set_scorecard_context(context, user_supplier)
    elif path == "gate_entry":
        context.current_page = "gate_entry"
        _set_gate_entry_context(context, user_supplier)
    else:
        frappe.throw(frappe._("Page not found"), frappe.NotFound)

    return context


def _set_dashboard_context(context, user_supplier):
    """Dashboard - Home page with stats"""
    context.title = "Supplier Portal Dashboard"

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

    context.recent_asns = frappe.get_all(
        "Advance Shipment Notice",
        filters={"supplier": user_supplier},
        fields=["name", "asn_date", "purchase_order", "status", "expected_delivery_date"],
        order_by="asn_date desc",
        limit=5
    )

    context.recent_pos = frappe.get_all(
        "Purchase Order",
        filters={"supplier": user_supplier, "docstatus": 1},
        fields=["name", "transaction_date", "grand_total", "currency", "status"],
        order_by="transaction_date desc",
        limit=5
    )

    context.open_queries = frappe.db.count("Supplier Query", {
        "supplier": user_supplier,
        "status": ["in", ["Open", "Responded"]]
    })

    context.latest_scorecard = frappe.get_all(
        "Supplier Scorecard",
        filters={"supplier": user_supplier},
        fields=["overall_score", "rating"],
        order_by="fiscal_year_start desc",
        limit=1
    )


def _set_asn_list_context(context, user_supplier):
    """ASN List page"""
    context.title = "My ASNs - Supplier Portal"

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


def _set_asn_new_context(context, user_supplier):
    """New ASN form page"""
    context.title = "Create ASN - Supplier Portal"

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


def _set_invoices_context(context, user_supplier):
    """Invoices list page"""
    context.title = "Invoices - Supplier Portal"

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

    context.available_prs = frappe.get_all(
        "Purchase Receipt",
        filters={
            "supplier": user_supplier,
            "docstatus": 1
        },
        fields=["name", "posting_date", "grand_total", "currency"],
        order_by="posting_date desc"
    )


def _set_purchase_orders_context(context, user_supplier):
    """Purchase Orders list page"""
    context.title = "Purchase Orders - Supplier Portal"

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


def _set_queries_context(context, user_supplier):
    """Queries list page"""
    context.title = "Queries - Supplier Portal"

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


def _set_asn_detail_context(context, user_supplier, asn_name):
    """ASN detail view page"""
    asn = frappe.get_doc("Advance Shipment Notice", asn_name)
    if asn.supplier != user_supplier:
        frappe.throw(frappe._("Not found"), frappe.NotFound)
    context.title = "ASN {0} - Supplier Portal".format(asn_name)
    context.asn = asn
    context.asn_items = asn.items
    context.asn_packages = asn.packages


def _set_scorecard_context(context, user_supplier):
    """Scorecard view page"""
    context.title = "Scorecard - Supplier Portal"

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


def _set_gate_entry_context(context, user_supplier):
    """Gate Entry page with QR scanner"""
    context.title = "Gate Entry - Supplier Portal"

    # Get in-transit ASNs for gate entry
    context.in_transit_asns = frappe.get_all(
        "Advance Shipment Notice",
        filters={
            "supplier": user_supplier,
            "status": ["in", ["In Transit", "Submitted"]]
        },
        fields=["name", "vehicle_no", "expected_delivery_date", "num_packages", "status"],
        order_by="expected_delivery_date asc"
    )

    # Get today's gate entries
    today = frappe.utils.nowdate()
    context.todays_gate_entries = frappe.get_all(
        "Gate Entry",
        filters={
            "supplier": user_supplier,
            "entry_date": today
        },
        fields=["name", "entry_time", "asn_reference", "vehicle_no", "status"],
        order_by="entry_time desc"
    )
