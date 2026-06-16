# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe


def query_conditions(user):
    """Gate entries are internal only; return empty for portal users"""
    if "Supplier Portal User" in frappe.get_roles(user):
        # Suppliers should not see gate entries directly
        return "1=0"
    return ""


def has_permission(doc, ptype, user):
    """Gate entries are internal only"""
    if "Supplier Portal User" in frappe.get_roles(user):
        # For create operations, fall back to default permissions
        if not doc or not hasattr(doc, 'supplier'):
            return None
        # For existing documents, always deny portal users
        return False
    return None
