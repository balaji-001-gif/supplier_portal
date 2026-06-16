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
        # Supplier-scoped filter applies only for read operations.
        # For create/write, fall back to default role-based permissions
        # so internal users with the portal role are not blocked.
        if ptype != 'read':
            return None
        return False
    return None
