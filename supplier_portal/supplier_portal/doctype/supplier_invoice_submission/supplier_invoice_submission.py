# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class SupplierInvoiceSubmission(Document):
    def validate(self):
        self.validate_supplier()
        self.validate_purchase_receipt()

    def on_submit(self):
        self.status = "Approved"
        self.approved_by = frappe.session.user
        self.approved_on = now_datetime()
        self.create_purchase_invoice()

    def on_cancel(self):
        self.status = "Cancelled"

    def validate_supplier(self):
        if frappe.session.user == "Administrator":
            return
        user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
        if user_supplier and user_supplier != self.supplier:
            frappe.throw(
                frappe._("You can only submit invoices for your own supplier account")
            )

    def validate_purchase_receipt(self):
        """Validate PR belongs to supplier"""
        if self.purchase_receipt:
            pr_supplier = frappe.db.get_value("Purchase Receipt", self.purchase_receipt, "supplier")
            if pr_supplier != self.supplier:
                frappe.throw(
                    frappe._("Purchase Receipt {0} does not belong to supplier {1}").format(
                        self.purchase_receipt, self.supplier
                    )
                )

    def create_purchase_invoice(self):
        """Auto-create Purchase Invoice from submitted invoice"""
        pr = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
        pi = frappe.new_doc("Purchase Invoice")
        pi.supplier = self.supplier
        pi.posting_date = self.invoice_date
        pi.bill_no = self.invoice_number
        pi.bill_date = self.invoice_date
        pi.bill_amount = self.invoice_amount
        pi.supplier_invoice_submission = self.name

        # Map items from PR
        for pr_item in pr.items:
            pi.append("items", {
                "item_code": pr_item.item_code,
                "item_name": pr_item.item_name,
                "qty": pr_item.qty,
                "rate": pr_item.rate,
                "uom": pr_item.uom,
                "purchase_order": pr_item.purchase_order,
                "purchase_receipt": pr.name,
                "purchase_receipt_item": pr_item.name
            })

        # Add taxes from PR if any
        if pr.taxes:
            for tax in pr.taxes:
                pi.append("taxes", {
                    "charge_type": tax.charge_type,
                    "account_head": tax.account_head,
                    "rate": tax.rate
                })

        pi.save(ignore_permissions=True)
        self.db_set("purchase_invoice", pi.name)
        self.db_set("pi_status", "Draft")
        frappe.msgprint(frappe._("Purchase Invoice {0} created successfully").format(pi.name))


@frappe.whitelist()
def get_supplier_purchase_receipts(supplier=None):
    """Get submitted PRs for invoice submission"""
    if not supplier:
        supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not supplier:
        return []
    return frappe.get_all(
        "Purchase Receipt",
        filters={
            "supplier": supplier,
            "docstatus": 1,
            "status": ["!=", "Cancelled"]
        },
        fields=["name", "posting_date", "grand_total", "currency"],
        order_by="posting_date desc"
    )
