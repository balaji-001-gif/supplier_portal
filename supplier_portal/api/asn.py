# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import json
from frappe.utils import now_datetime


@frappe.whitelist()
def create_asn(data):
    """Create ASN from supplier portal"""
    try:
        data = json.loads(data) if isinstance(data, str) else data
        user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
        if not user_supplier and frappe.session.user != "Administrator":
            frappe.throw(frappe._("You don't have permission to create ASN"))

        asn = frappe.new_doc("Advance Shipment Notice")
        asn.update(data)
        if user_supplier:
            asn.supplier = user_supplier
        asn.save()

        return {
            "success": True,
            "asn": asn.name,
            "message": frappe._("ASN created successfully")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "ASN Creation Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def submit_asn(asn_name):
    """Submit ASN and generate QR codes"""
    try:
        asn = frappe.get_doc("Advance Shipment Notice", asn_name)
        user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
        if user_supplier and user_supplier != asn.supplier and frappe.session.user != "Administrator":
            frappe.throw(frappe._("You don't have permission to submit this ASN"))

        asn.submit()
        qr_codes = []
        for pkg in asn.packages:
            qr_image = asn.generate_qr_image(pkg.package_id)
            qr_codes.append({
                "package_id": pkg.package_id,
                "qr_image": qr_image
            })

        return {
            "success": True,
            "asn": asn.name,
            "qr_codes": qr_codes,
            "message": frappe._("ASN submitted successfully. QR codes generated.")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "ASN Submission Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_supplier_asn_list(filters=None):
    """Get ASN list for supplier portal"""
    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not user_supplier and frappe.session.user != "Administrator":
        return []

    base_filters = {"supplier": user_supplier} if user_supplier else {}
    if filters:
        base_filters.update(json.loads(filters) if isinstance(filters, str) else filters)

    return frappe.get_all(
        "Advance Shipment Notice",
        filters=base_filters,
        fields=[
            "name", "asn_date", "purchase_order", "expected_delivery_date",
            "vehicle_no", "num_packages", "status", "docstatus"
        ],
        order_by="asn_date desc"
    )


@frappe.whitelist()
def get_asn_tracking(asn_name):
    """Get ASN tracking status with gate entry and PR info"""
    asn = frappe.get_doc("Advance Shipment Notice", asn_name)
    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if user_supplier and user_supplier != asn.supplier and frappe.session.user != "Administrator":
        frappe.throw(frappe._("You don't have permission to view this ASN"))

    gate_entry = frappe.db.get_value(
        "Gate Entry",
        {"asn_reference": asn_name},
        ["name", "entry_date", "entry_time", "status", "unloading_bay"],
        as_dict=1
    )

    pr = None
    if gate_entry:
        pr = frappe.db.get_value(
            "Purchase Receipt",
            {"gate_entry_reference": gate_entry.name},
            ["name", "posting_date", "docstatus", "per_billed"],
            as_dict=1
        )

    return {
        "asn": {
            "name": asn.name,
            "status": asn.status,
            "asn_date": asn.asn_date,
            "expected_delivery": asn.expected_delivery_date,
            "vehicle": asn.vehicle_no
        },
        "gate_entry": gate_entry,
        "purchase_receipt": pr,
        "packages": [{
            "package_id": pkg.package_id,
            "scanned": pkg.scanned_at_gate,
            "scan_time": pkg.scan_timestamp,
            "status": pkg.package_status
        } for pkg in asn.packages]
    }


@frappe.whitelist()
def get_asn_items(purchase_order, asn=None):
    """Get pending PO items for ASN creation"""
    po = frappe.get_doc("Purchase Order", purchase_order)
    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if user_supplier and user_supplier != po.supplier and frappe.session.user != "Administrator":
        frappe.throw(frappe._("You don't have permission to access this Purchase Order"))
    return po.items
