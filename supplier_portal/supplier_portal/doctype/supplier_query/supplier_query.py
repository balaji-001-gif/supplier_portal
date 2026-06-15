# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class SupplierQuery(Document):
    def validate(self):
        self.validate_supplier()

    def on_submit(self):
        self.status = "Open"
        self.submitted_by = frappe.session.user
        self.submitted_on = now_datetime()
        self.notify_internal_team()

    def on_update_after_submit(self):
        """Handle when internal team responds"""
        if self.response and not self.responded_by:
            self.responded_by = frappe.session.user
            self.responded_on = now_datetime()
            self.status = "Responded"
            self.notify_supplier_of_response()

    def validate_supplier(self):
        if frappe.session.user == "Administrator":
            return
        user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
        if user_supplier and user_supplier != self.supplier:
            frappe.throw(
                frappe._("You can only raise queries for your own supplier account")
            )

    def notify_internal_team(self):
        """Notify purchase team about new query"""
        purchase_users = frappe.get_all(
            "User",
            filters={"enabled": 1},
            fields=["email"],
            or_filters=[
                {"role_profile_name": ["in", ["Purchase Manager", "Purchase User"]]}
            ]
        )
        if purchase_users:
            frappe.sendmail(
                recipients=[u.email for u in purchase_users],
                subject=frappe._("New Supplier Query: {0} - {1}").format(self.subject, self.supplier_name),
                message=frappe._(
                    "Query from {0}: {1}<br><br>Message: {2}"
                ).format(self.supplier_name, self.subject, self.query_message),
                now=True
            )

    def notify_supplier_of_response(self):
        """Notify supplier that their query has been responded"""
        supplier_email = frappe.db.get_value("Supplier", self.supplier, "email_id")
        if supplier_email:
            frappe.sendmail(
                recipients=[supplier_email],
                subject=frappe._("Response to your query: {0}").format(self.subject),
                message=frappe._(
                    "<p>Dear {0},</p><p>Your query has been responded:</p>"
                    "<p><strong>Your query:</strong> {1}</p>"
                    "<p><strong>Response:</strong> {2}</p>"
                    "<p><a href='{3}'>View in Portal</a></p>"
                ).format(
                    self.supplier_name,
                    self.query_message,
                    self.response,
                    frappe.utils.get_url("/supplier_portal/queries/{0}".format(self.name))
                ),
                now=True
            )

    @frappe.whitelist()
    def respond(self, response_text):
        """Internal team responds to a query"""
        self.response = response_text
        self.responded_by = frappe.session.user
        self.responded_on = now_datetime()
        self.status = "Responded"
        self.save(ignore_permissions=True)
        return self.name


@frappe.whitelist()
def get_supplier_queries(supplier=None, status=None):
    """Get queries for supplier portal"""
    if not supplier:
        supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not supplier:
        return []
    filters = {"supplier": supplier}
    if status:
        filters["status"] = status
    return frappe.get_all(
        "Supplier Query",
        filters=filters,
        fields=[
            "name", "subject", "query_category", "status",
            "submitted_on", "responded_on", "priority"
        ],
        order_by="submitted_on desc"
    )
