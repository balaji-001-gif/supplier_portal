# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ASNItem(Document):
    def validate(self):
        self.validate_dispatch_qty()

    def validate_dispatch_qty(self):
        if flt(self.dispatch_qty) < 0:
            frappe.throw(frappe._("Dispatch qty cannot be negative"))

    def before_save(self):
        """Auto-set received_qty and accepted_qty based on Purchase Receipt updates"""
        if self.po_detail:
            received = frappe.db.sql("""
                SELECT COALESCE(SUM(pr_item.qty), 0) as qty
                FROM `tabPurchase Receipt Item` pr_item
                INNER JOIN `tabPurchase Receipt` pr ON pr.name = pr_item.parent
                WHERE pr_item.purchase_order_item = %s
                  AND pr.docstatus = 1
            """, self.po_detail, as_dict=True)
            if received:
                self.received_qty = received[0].qty
