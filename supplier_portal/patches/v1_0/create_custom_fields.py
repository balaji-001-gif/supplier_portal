# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Create custom fields for Supplier Portal integration"""
    custom_fields = {
        "Purchase Receipt": [
            {
                "fieldname": "gate_entry_reference",
                "label": "Gate Entry Reference",
                "fieldtype": "Link",
                "options": "Gate Entry",
                "insert_after": "supplier_delivery_note",
                "read_only": 1
            },
            {
                "fieldname": "asn_reference",
                "label": "ASN Reference",
                "fieldtype": "Link",
                "options": "Advance Shipment Notice",
                "insert_after": "gate_entry_reference",
                "read_only": 1
            }
        ],
        "User": [
            {
                "fieldname": "supplier",
                "label": "Supplier",
                "fieldtype": "Link",
                "options": "Supplier",
                "insert_after": "email"
            }
        ],
        "Supplier": [
            {
                "fieldname": "portal_access_enabled",
                "label": "Portal Access Enabled",
                "fieldtype": "Check",
                "default": "0",
                "insert_after": "disabled"
            },
            {
                "fieldname": "portal_user",
                "label": "Portal User",
                "fieldtype": "Link",
                "options": "User",
                "insert_after": "portal_access_enabled",
                "description": "Link to the User account that acts as this supplier's portal login"
            }
        ]
    }

    create_custom_fields(custom_fields, ignore_validate=True)
    frappe.db.commit()
