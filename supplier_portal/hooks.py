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
# Portals use inline styles in templates - no external assets needed.
# ---------------------------------------------

# ---------------------------------------------
# Website route rules
# ---------------------------------------------
# Route all /supplier_portal/* paths to the main router page handler
# Using a single router instead of www subdirectory auto-routing for reliability
website_route_rules = [
    {"from_route": "/supplier_portal", "to_route": "supplier_portal"},
    {"from_route": "/supplier_portal/<path:app_path>", "to_route": "supplier_portal"},
]

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
    },
    "Supplier": {
        "on_update": "supplier_portal.hooks.sync_portal_user"
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
# Session Creation
# ---------------------------------------------
on_session_creation = "supplier_portal.utils.redirect_to_supplier_portal"

# ---------------------------------------------
# Website Context
# ---------------------------------------------
website_context = {
    "navbar_search": False,
    "footer": False,
    "supplier_portal": True
}


def sync_portal_user(doc, method):
    """Auto-sync User.supplier when Supplier.portal_user or portal_access_enabled changes.

    When a Supplier's portal_user is set, this ensures the linked User's
    'supplier' custom field is also set (and unset if removed).
    """
    if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "supplier"}):
        return

    if doc.portal_user:
        prev_supplier = frappe.db.get_value("User", doc.portal_user, "supplier")
        if prev_supplier != doc.name:
            frappe.db.set_value("User", doc.portal_user, "supplier", doc.name)
            # Ensure the user gets the Supplier Portal User role
            user_doc = frappe.get_doc("User", doc.portal_user)
            has_role = any(r.role == "Supplier Portal User" for r in user_doc.roles)
            if not has_role:
                user_doc.add_roles("Supplier Portal User")

    # If portal_user was cleared, unset the old user's supplier field
    doc_before_save = doc.get_doc_before_save()
    if not doc.portal_user and doc_before_save and doc_before_save.portal_user:
        old_user = doc_before_save.portal_user
        current = frappe.db.get_value("User", old_user, "supplier")
        if current == doc.name:
            frappe.db.set_value("User", old_user, "supplier", None)

