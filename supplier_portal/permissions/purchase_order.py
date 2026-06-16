# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def query_conditions(user):
    """Return query conditions to filter POs by supplier for portal users"""
    if "Supplier Portal User" in frappe.get_roles(user):
        supplier = frappe.db.get_value("User", user, "supplier")
        if supplier:
            return """(`tabPurchase Order`.supplier = '{supplier}')""".format(supplier=supplier)
    return ""


def has_permission(doc, ptype, user):
    """Check if user has permission for a specific PO"""
    if "Supplier Portal User" in frappe.get_roles(user):
        # Supplier-scoped filter applies only for read operations.
        # For create/write (e.g., saving from desk), fall back to
        # default role-based permissions so internal users who also
        # have the portal role are not blocked.
        if ptype != 'read':
            return None
        user_supplier = frappe.db.get_value("User", user, "supplier")
        if user_supplier and doc.supplier == user_supplier:
            return True
        return False
    # Fallback to ERPNext default permissions
    return None
