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
        # Ensure items is always a list
        items = json.loads(items) if isinstance(items, str) else (items or [])

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

        # Build a lookup of user-provided qty overrides (item_code -> qty)
        items_qty_map = {}
        for itm in items:
            items_qty_map[itm.get("item_code")] = itm.get("qty")

        # Use Gate Entry Items (with captured batch/serial data) as source
        # Fall back to ASN items if Gate Entry has no items table populated
        source_items = ge.get("items") if ge.get("items") else asn.items

        # Build a quick lookup of PO item details (rate, uom, conversion_factor, warehouse)
        po_item_details = {}
        if po:
            for po_item in po.items:
                po_item_details[po_item.name] = {
                    "rate": po_item.rate,
                    "uom": po_item.uom,
                    "conversion_factor": po_item.conversion_factor or 1,
                    "warehouse": po_item.warehouse
                }

        for ge_item in source_items:
            po_detail = ge_item.get("po_detail")
            po_info = po_item_details.get(po_detail, {})

            po_item_rate = po_info.get("rate", 0)
            po_item_uom = po_info.get("uom", ge_item.get("uom"))
            po_conversion_factor = po_info.get("conversion_factor", 1)
            po_warehouse = po_info.get("warehouse")

            # Use user-provided qty override, else captured received_qty, else dispatch_qty
            qty = items_qty_map.get(
                ge_item.get("item_code"),
                ge_item.get("received_qty") or ge_item.get("dispatch_qty") or 0
            )
            if not qty or float(qty) <= 0:
                continue  # skip zero-qty items

            warehouse = po_warehouse or (pr.set_warehouse if po else None) or frappe.db.get_single_value("Buying Settings", "supplier_warehouse") or frappe.db.get_value("Company", pr.company, "default_warehouse")
            base_rate_val = po_item_rate * (po.conversion_rate if po else 1)
            amount_val = float(qty) * po_item_rate
            base_amount_val = float(qty) * po_item_rate * (po.conversion_rate if po else 1)

            pr_item = pr.append("items", {
                "item_code": ge_item.get("item_code"),
                "item_name": ge_item.get("item_name"),
                "qty": qty,
                "uom": po_item_uom,
                "conversion_factor": po_conversion_factor,
                "stock_uom": ge_item.get("uom") or po_item_uom,
                "rate": po_item_rate,
                "price_list_rate": po_item_rate,
                "base_rate": base_rate_val,
                "amount": amount_val,
                "base_amount": base_amount_val,
                "warehouse": warehouse,
                "purchase_order": asn.purchase_order,
                "purchase_order_item": po_detail
            })

            # Use batch/serial from source (both Gate Entry Items and ASN Items support .get())
            batch_no = ge_item.get("batch_no")
            if batch_no:
                if frappe.db.exists("Batch", batch_no):
                    pr_item.batch_no = batch_no
                    pr_item.manufacturing_date = ge_item.get("manufacturing_date")
                    pr_item.expiry_date = ge_item.get("expiry_date")
                else:
                    frappe.msgprint(frappe._(
                        "Batch {0} for item {1} does not exist. Please create it first."
                    ).format(batch_no, ge_item.get("item_code")))

            serial_nos = ge_item.get("serial_nos")
            if serial_nos:
                pr_item.serial_no = serial_nos

        if not pr.get("items"):
            frappe.throw(frappe._("No items to add to Purchase Receipt"))

        # Manually calculate header totals from items
        total_qty = 0
        total_amount = 0
        base_total_amount = 0
        for item in pr.items:
            total_qty += frappe.utils.flt(item.qty)
            total_amount += frappe.utils.flt(item.amount)
            base_total_amount += frappe.utils.flt(item.base_amount)
        pr.total_qty = total_qty
        pr.total = total_amount
        pr.base_total = base_total_amount
        pr.net_total = total_amount
        pr.base_net_total = base_total_amount

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
