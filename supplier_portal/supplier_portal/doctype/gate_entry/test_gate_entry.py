# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import unittest


class TestGateEntry(unittest.TestCase):
    """Test Gate Entry doctype"""

    def setUp(self):
        frappe.db.sql("DELETE FROM `tabGate Entry`")

    def _create_gate_entry(self):
        """Helper to create a basic gate entry"""
        entry = frappe.get_doc({
            "doctype": "Gate Entry",
            "supplier": "_Test Supplier",
            "vehicle_no": "MH12AB1234",
            "driver_name": "Test Driver",
            "driver_mobile": "9876543210",
            "entry_date": frappe.utils.nowdate(),
            "entry_time": frappe.utils.nowtime(),
            "num_packages": 3,
            "status": "At Gate"
        })
        entry.insert(ignore_permissions=True)
        return entry

    def test_gate_entry_creation(self):
        """Test basic gate entry creation"""
        entry = self._create_gate_entry()
        self.assertTrue(entry.name)
        self.assertEqual(entry.status, "At Gate")

    def test_unloading_duration_calculation(self):
        """Test unloading duration is calculated correctly"""
        entry = self._create_gate_entry()
        entry.unloading_start_time = frappe.utils.now_datetime()
        entry.unloading_end_time = frappe.utils.add_to_date(
            frappe.utils.now_datetime(), minutes=45
        )
        entry.save(ignore_permissions=True)
        self.assertTrue(entry.unloading_duration > 0)
        self.assertAlmostEqual(entry.unloading_duration, 45, delta=1)

    def test_status_transitions(self):
        """Test proper status values"""
        entry = self._create_gate_entry()
        valid_statuses = [
            "At Gate", "Document Verification", "Waiting for Unloading",
            "Unloading", "Completed", "Rejected"
        ]
        self.assertIn(entry.status, valid_statuses)
