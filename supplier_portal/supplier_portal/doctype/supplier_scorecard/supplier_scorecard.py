# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import flt, today, get_first_day_of_month


class SupplierScorecard(Document):
    def validate(self):
        self.calculate_average_metrics()

    def calculate_average_metrics(self):
        """Calculate scorecard metrics based on actual transaction data"""
        if not self.supplier:
            return

        # On-Time Delivery Rate (%)
        total_deliveries = frappe.db.count("Purchase Receipt", {
            "supplier": self.supplier,
            "docstatus": 1,
            "posting_date": [">=", self.fiscal_year_start] if self.fiscal_year_start else [">=", "2000-01-01"]
        })

        # Count deliveries made on or before schedule date
        on_time = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabPurchase Receipt` pr
            INNER JOIN `tabPurchase Order` po ON po.name = pr.purchase_order
            WHERE pr.supplier = %(supplier)s
              AND pr.docstatus = 1
              AND pr.posting_date <= po.schedule_date
              AND pr.posting_date >= %(period_start)s
        """, {
            "supplier": self.supplier,
            "period_start": self.fiscal_year_start or "2000-01-01"
        }, as_dict=True)[0].count

        self.on_time_delivery_rate = flt(on_time / total_deliveries * 100, 2) if total_deliveries else 0

        # Quality Acceptance Rate (%)
        quality_data = frappe.db.sql("""
            SELECT COALESCE(SUM(pr_item.qty), 0) as total_qty,
                   COALESCE(SUM(pr_item.rejected_qty), 0) as rejected_qty
            FROM `tabPurchase Receipt Item` pr_item
            INNER JOIN `tabPurchase Receipt` pr ON pr.name = pr_item.parent
            WHERE pr.supplier = %(supplier)s
              AND pr.docstatus = 1
              AND pr.posting_date >= %(period_start)s
        """, {
            "supplier": self.supplier,
            "period_start": self.fiscal_year_start or "2000-01-01"
        }, as_dict=True)[0]

        total_qty = flt(quality_data.total_qty)
        rejected_qty = flt(quality_data.rejected_qty)
        accepted_qty = total_qty - rejected_qty
        self.quality_acceptance_rate = flt(accepted_qty / total_qty * 100, 2) if total_qty else 0

        # Documentation Compliance Rate (%)
        total_asns = frappe.db.count("Advance Shipment Notice", {
            "supplier": self.supplier,
            "docstatus": 1,
            "asn_date": [">=", self.fiscal_year_start or "2000-01-01"]
        })
        asns_with_docs = frappe.db.count("Advance Shipment Notice", {
            "supplier": self.supplier,
            "docstatus": 1,
            "delivery_challan_attachment": ["!=", ""],
            "asn_date": [">=", self.fiscal_year_start or "2000-01-01"]
        })
        self.documentation_compliance_rate = flt(asns_with_docs / total_asns * 100, 2) if total_asns else 0

        # Invoice Accuracy Rate (%)
        total_invoices = frappe.db.count("Supplier Invoice Submission", {
            "supplier": self.supplier,
            "docstatus": 1,
            "submission_date": [">=", self.fiscal_year_start or "2000-01-01"]
        })
        accurate_invoices = frappe.db.count("Supplier Invoice Submission", {
            "supplier": self.supplier,
            "docstatus": 1,
            "status": "Approved",
            "submission_date": [">=", self.fiscal_year_start or "2000-01-01"]
        })
        self.invoice_accuracy_rate = flt(accurate_invoices / total_invoices * 100, 2) if total_invoices else 0

        # Overall Score (weighted average)
        self.overall_score = flt(
            self.on_time_delivery_rate * 0.30 +
            self.quality_acceptance_rate * 0.30 +
            self.documentation_compliance_rate * 0.20 +
            self.invoice_accuracy_rate * 0.20,
            2
        )

        # Rating based on score
        if self.overall_score >= 90:
            self.rating = "A+ - Excellent"
        elif self.overall_score >= 80:
            self.rating = "A - Very Good"
        elif self.overall_score >= 70:
            self.rating = "B - Good"
        elif self.overall_score >= 60:
            self.rating = "C - Average"
        else:
            self.rating = "D - Needs Improvement"


@frappe.whitelist()
def get_supplier_scorecard(supplier=None):
    """Get scorecard data for supplier portal"""
    if not supplier:
        supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if not supplier:
        return None
    return frappe.get_all(
        "Supplier Scorecard",
        filters={"supplier": supplier},
        fields=[
            "name", "fiscal_year_start", "overall_score", "rating",
            "on_time_delivery_rate", "quality_acceptance_rate",
            "documentation_compliance_rate", "invoice_accuracy_rate"
        ],
        order_by="fiscal_year_start desc",
        limit=1
    )
