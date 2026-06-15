# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.utils import today, add_days


def send_daily_asn_reminder():
    """Send reminders for ASNs that are still in Draft and approaching expected delivery"""
    tomorrow = add_days(today(), 1)

    pending_asns = frappe.get_all(
        "Advance Shipment Notice",
        filters={
            "docstatus": 0,
            "expected_delivery_date": ["<=", add_days(today(), 3)],
            "status": "Draft"
        },
        fields=["name", "supplier", "supplier_name", "purchase_order", "expected_delivery_date"]
    )

    for asn in pending_asns:
        supplier_email = frappe.db.get_value("Supplier", asn.supplier, "email_id")
        if supplier_email:
            frappe.sendmail(
                recipients=[supplier_email],
                subject=frappe._("Reminder: Pending ASN {0}").format(asn.name),
                message=frappe._(
                    "<p>Dear {0},</p>"
                    "<p>Your ASN <strong>{1}</strong> for PO {2} is still in Draft.</p>"
                    "<p>Expected delivery date: {3}</p>"
                    "<p>Please submit the ASN at the earliest.</p>"
                    "<p><a href='{4}'>Complete ASN</a></p>"
                ).format(
                    asn.supplier_name,
                    asn.name,
                    asn.purchase_order,
                    asn.expected_delivery_date,
                    frappe.utils.get_url("/supplier_portal/asn/new")
                ),
                now=True
            )


def supplier_scorecard_calculation():
    """Auto-calculate scorecards for all suppliers periodically"""
    from frappe.utils import get_first_day_of_month, get_last_day_of_month

    # Get all suppliers with portal access
    suppliers = frappe.get_all(
        "Supplier",
        filters={"portal_access_enabled": 1},
        fields=["name", "supplier_name"]
    )

    year_start = today()[:4] + "-01-01"
    year_end = today()[:4] + "-12-31"

    for supplier in suppliers:
        existing = frappe.db.get_value(
            "Supplier Scorecard",
            {"supplier": supplier.name, "fiscal_year_start": year_start},
            "name"
        )

        if existing:
            scorecard = frappe.get_doc("Supplier Scorecard", existing)
        else:
            scorecard = frappe.new_doc("Supplier Scorecard")
            scorecard.supplier = supplier.name
            scorecard.supplier_name = supplier.supplier_name
            scorecard.fiscal_year_start = year_start
            scorecard.fiscal_year_end = year_end

        scorecard.save(ignore_permissions=True)
