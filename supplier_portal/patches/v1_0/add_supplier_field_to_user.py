# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def execute():
    """Ensure the supplier field exists on User doctype"""
    # Check if custom field exists, if not, rely on create_custom_fields patch
    if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "supplier"}):
        # Custom fields will be created by the create_custom_fields patch
        pass

    # Add Supplier Portal User role to any users linked to suppliers
    users_with_supplier = frappe.db.get_all(
        "User",
        filters={"supplier": ["!=", ""]},
        fields=["name", "supplier"]
    )

    for user in users_with_supplier:
        user_doc = frappe.get_doc("User", user.name)
        roles = [r.role for r in user_doc.roles]
        if "Supplier Portal User" not in roles:
            user_doc.add_roles("Supplier Portal User")

    frappe.db.commit()
