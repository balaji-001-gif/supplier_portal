# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ASNPackage(Document):
    def validate(self):
        self.calculate_volume()

    def calculate_volume(self):
        if self.length and self.width and self.height:
            self.volume = (flt(self.length) * flt(self.width) * flt(self.height)) / 1000000
