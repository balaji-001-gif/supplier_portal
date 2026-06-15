# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.permissions import add_permission


def execute():
    """Create the Supplier Portal User and Warehouse Staff roles"""
    roles = [
        {
            "role_name": "Supplier Portal User",
            "desk_access": 0,
            "role_type": "System"
        },
        {
            "role_name": "Warehouse Staff",
            "desk_access": 1,
            "role_type": "System"
        }
    ]

    for role in roles:
        if not frappe.db.exists("Role", role["role_name"]):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role["role_name"],
                "desk_access": role["desk_access"],
                "role_type": role["role_type"]
            }).insert(ignore_permissions=True)

    # Add permission to Gate Entry for Warehouse Staff
    for doctype in ["Gate Entry", "Advance Shipment Notice", "Purchase Receipt"]:
        for role in ["Warehouse Staff", "Stock User"]:
            try:
                add_permission(doctype, role, 1)
            except Exception:
                pass

    frappe.db.commit()
