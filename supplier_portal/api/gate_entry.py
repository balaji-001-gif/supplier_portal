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
