# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe

# Import the real ERPNext PurchaseReceipt class so super() calls work correctly
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt


class CustomPurchaseReceipt(PurchaseReceipt):
    """Extended Purchase Receipt with ASN/Gate Entry integration"""

    def on_submit(self):
        """Update ASN item quantities on PR submit"""
        super(CustomPurchaseReceipt, self).on_submit()

        if self.get("asn_reference"):
            asn = frappe.get_doc("Advance Shipment Notice", self.asn_reference)
            # Update ASN item received/accepted/rejected qty
            for pr_item in self.items:
                for asn_item in asn.items:
                    if asn_item.item_code == pr_item.item_code:
                        asn_item.db_set("received_qty", pr_item.qty)
                        asn_item.db_set("accepted_qty", pr_item.qty - (pr_item.rejected_qty or 0))
                        asn_item.db_set("rejected_qty", pr_item.rejected_qty or 0)

            # Update ASN status
            asn.db_set("status", "Received")

            # Update package statuses
            for pkg in asn.packages:
                pkg.db_set("package_status", "Received")

            # Update Gate Entry PR status
            gate_entry_name = frappe.db.get_value(
                "Gate Entry",
                {"asn_reference": self.asn_reference},
                "name"
            )
            if gate_entry_name:
                frappe.db.set_value("Gate Entry", gate_entry_name, "pr_status", "Submitted")
                frappe.db.set_value("Gate Entry", gate_entry_name, "purchase_receipt", self.name)

    def on_cancel(self):
        """Revert ASN status on PR cancel"""
        super(CustomPurchaseReceipt, self).on_cancel()

        if self.get("asn_reference"):
            asn = frappe.get_doc("Advance Shipment Notice", self.asn_reference)
            for pr_item in self.items:
                for asn_item in asn.items:
                    if asn_item.item_code == pr_item.item_code:
                        asn_item.db_set("received_qty", 0)
                        asn_item.db_set("accepted_qty", 0)
                        asn_item.db_set("rejected_qty", 0)

            asn.db_set("status", "At Gate")

            for pkg in asn.packages:
                pkg.db_set("package_status", "At Gate")

            gate_entry_name = frappe.db.get_value(
                "Gate Entry",
                {"asn_reference": self.asn_reference},
                "name"
            )
            if gate_entry_name:
                frappe.db.set_value("Gate Entry", gate_entry_name, "pr_status", "Cancelled")
                frappe.db.set_value("Gate Entry", gate_entry_name, "purchase_receipt", "")
