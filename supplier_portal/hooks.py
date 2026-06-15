# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "supplier_portal"
app_title = "Supplier Portal"
app_publisher = "Your Organization"
app_description = "Comprehensive supplier portal with ASN, QR codes, and gate entry for ERPNext V15"
app_icon = "octicon octicon-package"
app_color = "blue"
app_email = "info@yourcompany.com"
app_license = "MIT"

# ---------------------------------------------
# Includes in <head>
# ---------------------------------------------
app_include_css = "/assets/supplier_portal/css/supplier_portal.css"
app_include_js = "/assets/supplier_portal/js/supplier_portal.js"

# Web page includes
web_include_css = "/assets/supplier_portal/css/supplier_portal.css"
web_include_js = "/assets/supplier_portal/js/qr_scanner.js"

# ---------------------------------------------
# Website route rules
# ---------------------------------------------
# Routes are handled automatically via the www/supplier_portal/ directory structure
# No additional route rules needed

# ---------------------------------------------
# DocType Class Overrides
# ---------------------------------------------
override_doctype_class = {
    "Purchase Receipt": "supplier_portal.overrides.purchase_receipt.CustomPurchaseReceipt"
}

# ---------------------------------------------
# Document Events
# ---------------------------------------------
# Purchase Receipt events are handled via override_doctype_class (CustomPurchaseReceipt).
# Using both override_doctype_class AND doc_events for PR would cause double processing.
doc_events = {
    "Purchase Order": {
        "on_submit": "supplier_portal.api.supplier_portal.notify_supplier_on_po_submit"
    }
}

# ---------------------------------------------
# Scheduled Tasks
# ---------------------------------------------
scheduler_events = {
    "daily": [
        "supplier_portal.tasks.daily.send_daily_asn_reminder",
        "supplier_portal.tasks.daily.supplier_scorecard_calculation"
    ],
    "hourly": [
        "supplier_portal.tasks.hourly.update_asn_eta_status"
    ],
    "weekly": [],
    "monthly": []
}

# ---------------------------------------------
# Permissions
# ---------------------------------------------
permission_query_conditions = {
    "Purchase Order": "supplier_portal.permissions.purchase_order.query_conditions",
    "Advance Shipment Notice": "supplier_portal.permissions.asn.query_conditions",
    "Gate Entry": "supplier_portal.permissions.gate_entry.query_conditions",
    "Supplier Invoice Submission": "supplier_portal.permissions.invoice.query_conditions",
    "Supplier Scorecard": "supplier_portal.permissions.scorecard.query_conditions",
    "Supplier Query": "supplier_portal.permissions.supplier_query.query_conditions",
}

has_permission = {
    "Purchase Order": "supplier_portal.permissions.purchase_order.has_permission",
    "Advance Shipment Notice": "supplier_portal.permissions.asn.has_permission",
    "Gate Entry": "supplier_portal.permissions.gate_entry.has_permission",
    "Supplier Invoice Submission": "supplier_portal.permissions.invoice.has_permission",
    "Supplier Scorecard": "supplier_portal.permissions.scorecard.has_permission",
    "Supplier Query": "supplier_portal.permissions.supplier_query.has_permission",
}

# ---------------------------------------------
# Fixtures
# ---------------------------------------------
fixtures = [
    {"dt": "Custom Field", "filters": [["name", "in", [
        "Purchase Receipt-gate_entry_reference",
        "Purchase Receipt-asn_reference",
        "User-supplier",
        "Supplier-portal_access_enabled",
        "Supplier-portal_user"
    ]]]},
    {"dt": "Workspace", "filters": [["module", "=", "Supplier Portal"]]},
    {"dt": "Role", "filters": [["name", "in", ["Supplier Portal User", "Warehouse Staff"]]]},
]

# ---------------------------------------------
# Website Context
# ---------------------------------------------
website_context = {
    "navbar_search": False,
    "footer": False,
    "supplier_portal": True
}

