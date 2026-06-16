# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import json
from frappe.utils import now_datetime


@frappe.whitelist()
def create_gate_entry_from_asn(asn_data):
    """Create gate entry from ASN reference (mapped doc method)"""
    if isinstance(asn_data, str):
        asn_data = json.loads(asn_data)

    gate_entry = frappe.new_doc("Gate Entry")
    gate_entry.asn_reference = asn_data.get("name")
    gate_entry.supplier = asn_data.get("supplier")
    gate_entry.supplier_name = asn_data.get("supplier_name")
    gate_entry.vehicle_no = asn_data.get("vehicle_no")
    gate_entry.driver_name = asn_data.get("driver_name")
    gate_entry.driver_mobile = asn_data.get("driver_mobile")
    gate_entry.lr_no = asn_data.get("lr_no")
    gate_entry.transport_company = asn_data.get("transport_company")
    gate_entry.num_packages = asn_data.get("num_packages")
    gate_entry.entry_date = frappe.utils.nowdate()
    gate_entry.entry_time = frappe.utils.nowtime()
    return gate_entry


@frappe.whitelist()
def scan_qr(qr_data):
    """Process QR code scan at gate"""
    try:
        if isinstance(qr_data, str):
            data = json.loads(qr_data)
        else:
            data = qr_data
    except Exception:
        frappe.throw(frappe._("Invalid QR code data"))

    if data.get("doc_type") != "Advance Shipment Notice":
        frappe.throw(frappe._("Invalid QR code: Not an ASN QR code"))

    asn_name = data.get("doc_id")
    if not frappe.db.exists("Advance Shipment Notice", asn_name):
        frappe.throw(frappe._("ASN {0} not found").format(asn_name))

    asn = frappe.get_doc("Advance Shipment Notice", asn_name)
    if asn.docstatus != 1:
        frappe.throw(frappe._("ASN is not submitted"))

    # Create or update Gate Entry
    gate_entry_name = frappe.db.get_value(
        "Gate Entry",
        {"asn_reference": asn_name, "docstatus": 0}
    )

    if gate_entry_name:
        gate_entry = frappe.get_doc("Gate Entry", gate_entry_name)
    else:
        gate_entry = frappe.new_doc("Gate Entry")
        gate_entry.asn_reference = asn_name
        gate_entry.supplier = data.get("supplier_id")
        gate_entry.supplier_name = data.get("supplier_name")
        gate_entry.vehicle_no = data.get("vehicle_no")
        gate_entry.driver_name = data.get("driver_name")
        gate_entry.driver_mobile = data.get("driver_mobile")
        gate_entry.lr_no = asn.lr_no
        gate_entry.transport_company = asn.transport_company
        gate_entry.num_packages = data.get("num_packages")
        gate_entry.entry_date = frappe.utils.nowdate()
        gate_entry.entry_time = frappe.utils.nowtime()

    gate_entry.scanned_package_id = data.get("package_id")
    gate_entry.scan_timestamp = now_datetime()
    gate_entry.gate_guard = frappe.session.user
    gate_entry.save(ignore_permissions=True)

    return {
        "success": True,
        "gate_entry": gate_entry.name,
        "asn": asn_name,
        "supplier": asn.supplier_name,
        "vehicle": asn.vehicle_no,
        "packages": asn.num_packages,
        "items": [{"item_code": item.item_code, "qty": item.dispatch_qty} for item in asn.items]
    }


@frappe.whitelist()
def start_unloading(gate_entry_name, unloading_bay=None):
    """Start unloading process for a gate entry"""
    gate_entry = frappe.get_doc("Gate Entry", gate_entry_name)
    gate_entry.unloading_start_time = now_datetime()
    if unloading_bay:
        gate_entry.unloading_bay = unloading_bay
    gate_entry.status = "Unloading"

    if gate_entry.asn_reference:
        frappe.db.set_value("Advance Shipment Notice", gate_entry.asn_reference, "status", "Unloading")

    gate_entry.save(ignore_permissions=True)
    return {"success": True, "message": frappe._("Unloading started"), "name": gate_entry.name}


@frappe.whitelist()
def complete_unloading(gate_entry_name):
    """Complete unloading process for a gate entry"""
    gate_entry = frappe.get_doc("Gate Entry", gate_entry_name)
    gate_entry.unloading_end_time = now_datetime()
    gate_entry.status = "Completed"
    gate_entry.save(ignore_permissions=True)
    return {"success": True, "message": frappe._("Unloading completed"), "name": gate_entry.name}
