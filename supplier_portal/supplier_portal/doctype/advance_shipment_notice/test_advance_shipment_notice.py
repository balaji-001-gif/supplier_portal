# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import unittest

if not frappe.db:
    pass


class TestAdvanceShipmentNotice(unittest.TestCase):
    """Test Advance Shipment Notice doctype"""

    def setUp(self):
        frappe.db.sql("DELETE FROM `tabAdvance Shipment Notice`")
        frappe.db.sql("DELETE FROM `tabASN Item`")
        frappe.db.sql("DELETE FROM `tabASN Package`")

    def _create_supplier(self):
        if not frappe.db.exists("Supplier", "_Test Supplier"):
            supplier = frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": "_Test Supplier",
                "supplier_type": "Company",
                "supplier_group": "All Supplier Groups"
            }).insert(ignore_permissions=True)
            return supplier.name
        return "_Test Supplier"

    def _create_item(self, item_code="_Test ASN Item"):
        if not frappe.db.exists("Item", item_code):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_name": item_code,
                "item_group": "All Item Groups",
                "stock_uom": "Nos",
                "is_stock_item": 1
            }).insert(ignore_permissions=True)
            return item.name
        return item_code

    def _create_purchase_order(self, supplier=None):
        if not supplier:
            supplier = self._create_supplier()
        item = self._create_item()

        if frappe.db.exists("Purchase Order", {"supplier": supplier, "docstatus": 0}):
            po_name = frappe.db.get_value("Purchase Order", {"supplier": supplier, "docstatus": 0})
            return po_name

        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "supplier": supplier,
            "transaction_date": frappe.utils.nowdate(),
            "schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
            "items": [{
                "item_code": item,
                "qty": 100,
                "rate": 10,
                "uom": "Nos",
                "schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 7)
            }]
        })
        po.insert(ignore_permissions=True)
        return po.name

    def test_asn_creation(self):
        """Test basic ASN creation"""
        supplier = self._create_supplier()
        po = self._create_purchase_order(supplier)
        item = self._create_item()

        asn = frappe.get_doc({
            "doctype": "Advance Shipment Notice",
            "supplier": supplier,
            "purchase_order": po,
            "asn_date": frappe.utils.nowdate(),
            "expected_delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 3),
            "delivery_challan_no": "DC-2025-001",
            "challan_date": frappe.utils.nowdate(),
            "num_packages": 2,
            "vehicle_no": "MH12AB1234",
            "driver_name": "Test Driver",
            "driver_mobile": "9876543210",
            "items": [{
                "item_code": item,
                "item_name": item,
                "dispatch_qty": 100,
                "uom": "Nos",
                "batch_no": "BATCH-001"
            }]
        })
        asn.insert(ignore_permissions=True)
        self.assertTrue(asn.name)
        self.assertEqual(asn.status, "Draft")

    def test_qr_generation_on_submit(self):
        """Test QR codes are generated on submit"""
        supplier = self._create_supplier()
        po = self._create_purchase_order(supplier)
        item = self._create_item()

        asn = frappe.get_doc({
            "doctype": "Advance Shipment Notice",
            "supplier": supplier,
            "purchase_order": po,
            "asn_date": frappe.utils.nowdate(),
            "expected_delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 3),
            "delivery_challan_no": "DC-2025-002",
            "challan_date": frappe.utils.nowdate(),
            "num_packages": 2,
            "vehicle_no": "MH12AB5678",
            "items": [{
                "item_code": item,
                "item_name": item,
                "dispatch_qty": 100,
                "uom": "Nos",
                "batch_no": "BATCH-002"
            }]
        })
        asn.insert(ignore_permissions=True)
        asn.submit()

        self.assertEqual(asn.status, "Submitted")
        self.assertTrue(len(asn.packages) > 0)

        for pkg in asn.packages:
            self.assertTrue(pkg.qr_generated, "QR should be generated for each package")
            self.assertTrue(pkg.qr_code, "QR code data should be non-empty")

    def test_asn_submitted_status(self):
        """Test submission status update"""
        supplier = self._create_supplier()
        po = self._create_purchase_order(supplier)
        item = self._create_item()

        asn = frappe.get_doc({
            "doctype": "Advance Shipment Notice",
            "supplier": supplier,
            "purchase_order": po,
            "asn_date": frappe.utils.nowdate(),
            "expected_delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 3),
            "delivery_challan_no": "DC-2025-003",
            "challan_date": frappe.utils.nowdate(),
            "num_packages": 1,
            "vehicle_no": "MH12AB9012",
            "items": [{
                "item_code": item,
                "item_name": item,
                "dispatch_qty": 50,
                "uom": "Nos",
                "batch_no": "BATCH-003"
            }]
        })
        asn.insert(ignore_permissions=True)
        asn.submit()
        self.assertEqual(asn.status, "Submitted")
        self.assertEqual(asn.docstatus, 1)
