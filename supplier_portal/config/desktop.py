# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
        {
            "module_name": "Supplier Portal",
            "category": "Modules",
            "label": _("Supplier Portal"),
            "color": "#2563eb",
            "icon": "octicon octicon-package",
            "type": "module",
            "description": "Manage supplier portal with ASN, gate entry, and QR code tracking.",
        }
    ]
