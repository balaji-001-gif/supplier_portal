# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.utils import now_datetime


@frappe.whitelist()
def notify_supplier_on_po_submit(doc, method):
    """Notify supplier when a PO is submitted"""
    if not doc.supplier:
        return
    supplier_email = frappe.db.get_value("Supplier", doc.supplier, "email_id")
    if not supplier_email:
        return
    portal_link = frappe.utils.get_url(
        "/supplier_portal/purchase_orders/{0}".format(doc.name)
    )
    frappe.sendmail(
        recipients=[supplier_email],
        subject=frappe._("New Purchase Order: {0}").format(doc.name),
        message=frappe._(
            "<p>Dear {0},</p>"
            "<p>A new Purchase Order <strong>{1}</strong> has been created for you.</p>"
            "<p>Amount: {2} {3}<br>"
            "Schedule Date: {4}</p>"
            "<p><a href='{5}'>View in Supplier Portal</a></p>"
        ).format(
            doc.supplier_name,
            doc.name,
            doc.grand_total,
            doc.currency,
            doc.schedule_date,
            portal_link
        ),
        now=True
    )


@frappe.whitelist()
def update_asn_on_pr_submit(doc, method):
    """Update ASN status when Purchase Receipt is submitted"""
    asn_reference = doc.get("asn_reference")
    if asn_reference:
        asn = frappe.get_doc("Advance Shipment Notice", asn_reference)
        asn.db_set("status", "Received")
        # Update item quantities in ASN
        for pr_item in doc.items:
            for asn_item in asn.items:
                if asn_item.item_code == pr_item.item_code:
                    asn_item.db_set("received_qty", pr_item.qty)
                    asn_item.db_set("accepted_qty", pr_item.qty - pr_item.rejected_qty)
                    asn_item.db_set("rejected_qty", pr_item.rejected_qty)

        # Update package statuses
        for pkg in asn.packages:
            pkg.db_set("package_status", "Received")

        # Update Gate Entry if exists
        gate_entry = frappe.db.get_value(
            "Gate Entry",
            {"asn_reference": asn_reference},
            "name"
        )
        if gate_entry:
            frappe.db.set_value("Gate Entry", gate_entry, "pr_status", "Submitted")

        # Notify supplier
        supplier_email = frappe.db.get_value("Supplier", doc.supplier, "email_id")
        if supplier_email:
            frappe.sendmail(
                recipients=[supplier_email],
                subject=frappe._("Purchase Receipt Created: {0}").format(doc.name),
                message=frappe._(
                    "<p>Dear {0},</p>"
                    "<p>Purchase Receipt <strong>{1}</strong> has been created against your ASN {2}.</p>"
                    "<p><a href='{3}'>View in Portal</a></p>"
                ).format(
                    doc.supplier_name,
                    doc.name,
                    asn_reference,
                    frappe.utils.get_url("/supplier_portal/asn/{0}".format(asn_reference))
                ),
                now=True
            )


@frappe.whitelist()
def revert_asn_on_pr_cancel(doc, method):
    """Revert ASN status when Purchase Receipt is cancelled"""
    asn_reference = doc.get("asn_reference")
    if asn_reference:
        asn = frappe.get_doc("Advance Shipment Notice", asn_reference)
        asn.db_set("status", "At Gate")
        for pr_item in doc.items:
            for asn_item in asn.items:
                if asn_item.item_code == pr_item.item_code:
                    asn_item.db_set("received_qty", 0)
                    asn_item.db_set("accepted_qty", 0)
                    asn_item.db_set("rejected_qty", 0)

        for pkg in asn.packages:
            pkg.db_set("package_status", "At Gate")

        gate_entry = frappe.db.get_value(
            "Gate Entry",
            {"asn_reference": asn_reference},
            "name"
        )
        if gate_entry:
            frappe.db.set_value("Gate Entry", gate_entry, "pr_status", "Cancelled")
            frappe.db.set_value("Gate Entry", gate_entry, "purchase_receipt", "")
