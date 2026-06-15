# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def redirect_to_supplier_portal():
    """Redirect supplier portal users to the web portal after login instead of the blank desk."""
    if frappe.session.user == "Guest":
        return

    user = frappe.session.user
    roles = frappe.get_roles(user)

    if "Supplier Portal User" in roles and "System Manager" not in roles:
        supplier = frappe.db.get_value("User", user, "supplier")
        if supplier:
            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = "/supplier_portal"
