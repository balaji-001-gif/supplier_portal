# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def query_conditions(user):
    """Return query conditions to filter queries by supplier for portal users"""
    if "Supplier Portal User" in frappe.get_roles(user):
        supplier = frappe.db.get_value("User", user, "supplier")
        if supplier:
            return """(`tabSupplier Query`.supplier = '{supplier}')""".format(supplier=supplier)
    return ""


def has_permission(doc, ptype, user):
    """Check if user has permission for a specific query"""
    if "Supplier Portal User" in frappe.get_roles(user):
        # For create operations, doc is None or a string (doctype name),
        # so fall back to default role-based permissions
        if not doc or not hasattr(doc, 'supplier') or not doc.supplier:
            return None
        user_supplier = frappe.db.get_value("User", user, "supplier")
        if user_supplier and doc.supplier == user_supplier:
            return True
        return False
    return None
