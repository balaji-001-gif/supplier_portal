# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class GateEntryItem(Document):
    def validate(self):
        self.validate_quantities()

    def validate_quantities(self):
        if flt(self.received_qty) < 0:
            frappe.throw(frappe._("Row #{0}: Received qty cannot be negative").format(self.idx))
        if flt(self.accepted_qty) < 0:
            frappe.throw(frappe._("Row #{0}: Accepted qty cannot be negative").format(self.idx))
        if flt(self.rejected_qty) < 0:
            frappe.throw(frappe._("Row #{0}: Rejected qty cannot be negative").format(self.idx))
