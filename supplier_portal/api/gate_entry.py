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
def create_purchase_receipt_from_gate_entry(gate_entry_name, items=None):
    """Create a Purchase Receipt draft pre-filled from Gate Entry and ASN data"""
    try:
        if isinstance(items, str):
            items = json.loads(items) if items else []

        ge = frappe.get_doc("Gate Entry", gate_entry_name)
        if ge.docstatus != 1:
            frappe.throw(frappe._("Gate Entry must be submitted first"))
        if not ge.asn_reference:
            frappe.throw(frappe._("Gate Entry has no ASN reference"))

        asn = frappe.get_doc("Advance Shipment Notice", ge.asn_reference)
        po = frappe.get_doc("Purchase Order", asn.purchase_order) if asn.purchase_order else None

        pr = frappe.new_doc("Purchase Receipt")
        pr.supplier = ge.supplier
        pr.posting_date = ge.entry_date
        pr.posting_time = ge.entry_time
        pr.set_posting_time = 1
        pr.bill_no = asn.delivery_challan_no
        pr.bill_date = asn.challan_date
        pr.lr_no = ge.lr_no
        pr.transporter_name = ge.transport_company

        # Financial fields from PO
        if po:
            pr.company = po.company
            pr.currency = po.currency
            pr.conversion_rate = po.conversion_rate
            pr.plc_conversion_rate = po.plc_conversion_rate
            pr.price_list_currency = po.price_list_currency
            pr.buying_price_list = po.buying_price_list
            pr.set_warehouse = po.set_warehouse
        else:
            pr.company = frappe.defaults.get_user_default("company")
            pr.currency = frappe.defaults.get_global_default("currency") or "INR"
            pr.conversion_rate = 1
            pr.plc_conversion_rate = 1

        # Custom fields linking back to Gate Entry
        pr.db_set("gate_entry_reference", ge.name)
        pr.db_set("asn_reference", ge.asn_reference)

        # Build a lookup of user-provided qty overrides
        items_qty_map = {}
        for itm in items:
            items_qty_map[itm.get("item_code")] = itm.get("qty")

        for asn_item in asn.items:
            # Get PO item rate
            po_item_rate = 0
            po_item_uom = asn_item.uom
            po_conversion_factor = 1
            po_warehouse = None
            if po and asn_item.po_detail:
                for po_item in po.items:
                    if po_item.name == asn_item.po_detail:
                        po_item_rate = po_item.rate
                        po_item_uom = po_item.uom
                        po_conversion_factor = po_item.conversion_factor or 1
                        po_warehouse = po_item.warehouse
                        break

            # Use user-provided qty if given, else fall back to dispatch_qty
            qty = items_qty_map.get(asn_item.item_code, asn_item.dispatch_qty)
            if not qty or float(qty) <= 0:
                continue  # skip zero-qty items

            warehouse = po_warehouse or (pr.set_warehouse if po else None) or frappe.db.get_single_value("Buying Settings", "supplier_warehouse") or frappe.db.get_value("Company", pr.company, "default_warehouse")
            base_rate_val = po_item_rate * (po.conversion_rate if po else 1)
            amount_val = float(qty) * po_item_rate
            base_amount_val = float(qty) * po_item_rate * (po.conversion_rate if po else 1)

            pr_item = pr.append("items", {
                "item_code": asn_item.item_code,
                "item_name": asn_item.item_name,
                "qty": qty,
                "uom": po_item_uom,
                "conversion_factor": po_conversion_factor,
                "stock_uom": po_item_uom,
                "rate": po_item_rate,
                "price_list_rate": po_item_rate,
                "base_rate": base_rate_val,
                "amount": amount_val,
                "base_amount": base_amount_val,
                "warehouse": warehouse,
                "purchase_order": asn.purchase_order,
                "purchase_order_item": asn_item.po_detail
            })

            # Set batch/serial only if batch exists
            if asn_item.batch_no and frappe.db.exists("Batch", asn_item.batch_no):
                pr_item.batch_no = asn_item.batch_no
                pr_item.manufacturing_date = asn_item.manufacturing_date
                pr_item.expiry_date = asn_item.expiry_date
            if asn_item.serial_nos:
                pr_item.serial_no = asn_item.serial_nos

        if not pr.get("items"):
            frappe.throw(frappe._("No items to add to Purchase Receipt"))

        pr.save(ignore_permissions=True)

        # Link PR back to Gate Entry
        ge.db_set("purchase_receipt", pr.name)
        ge.db_set("pr_status", "Draft")

        return {
            "success": True,
            "purchase_receipt": pr.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PR Creation from Gate Entry")
        return {"success": False, "message": str(e)}


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
