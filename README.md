# Supplier Portal for ERPNext V15

> A comprehensive two-sided supplier collaboration platform with Advanced Shipment Notice (ASN), QR code package tracking, gate entry management, automated Purchase Receipt creation, invoice submission, supplier scorecards, and query management.

---

## Table of Contents

1. [Overview & Architecture](#1-overview--architecture)
2. [Installation & Setup](#2-installation--setup)
3. [Roles & Permissions](#3-roles--permissions)
4. [DocType Reference](#4-doctype-reference)
5. [End-to-End Working Flow](#5-end-to-end-working-flow)
6. [Standard Operating Procedures (SOPs)](#6-standard-operating-procedures-sops)
7. [Supplier Portal Web Pages](#7-supplier-portal-web-pages)
8. [Email Notifications](#8-email-notifications)
9. [Scheduled Tasks (Automation)](#9-scheduled-tasks-automation)
10. [API Endpoints](#10-api-endpoints)
11. [Custom Fields](#11-custom-fields)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Overview & Architecture

### What It Does

The Supplier Portal bridges the gap between suppliers and the internal purchasing/warehouse team through a **two-sided architecture**:

- **Suppliers** log into a web portal where they see only their own data — their POs, their ASNs, their invoices, their scorecard.
- **Internal teams** (Purchase, Warehouse, Accounts) work inside full ERPNext with complete visibility across all suppliers.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  SUPPLIER PORTAL (Web)                    │
│  /supplier_portal                                        │
│  ┌───────────┐ ┌──────────┐ ┌─────────┐ ┌───────────┐  │
│  │ Dashboard  │ │ ASN Mgmt │ │Invoice  │ │ Scorecard  │  │
│  │ (Stats)    │ │ (CRUD)   │ │Submit   │ │ (View)    │  │
│  └───────────┘ └──────────┘ └─────────┘ └───────────┘  │
│         ▲                           ▲                   │
│         │      Filtered by          │                   │
│         │   supplier = logged_in    │                   │
├─────────┼───────────────────────────┼───────────────────┤
│         │     ERPNext CORE          │                   │
│  ┌──────┴───────────────────────────┴──────────────┐    │
│  │              Purchase Order                     │    │
│  │              Advance Shipment Notice            │    │
│  │              Gate Entry                         │    │
│  │              Purchase Receipt                   │    │
│  │              Supplier Invoice Submission        │    │
│  │              Purchase Invoice                   │    │
│  │              Supplier Scorecard                 │    │
│  │              Supplier Query                     │    │
│  └─────────────────────────────────────────────────┘    │
│                    ▲          ▲                          │
│         ┌─────────┘          └──────────┐               │
│         ▼                               ▼               │
│  ┌──────────────┐              ┌──────────────┐         │
│  │ Warehouse    │              │ Accounts     │         │
│  │ Staff        │              │ / Purchase   │         │
│  │ (Gate, Rack) │              │ (Invoices)   │         │
│  └──────────────┘              └──────────────┘         │
└─────────────────────────────────────────────────────────┘
```

### Two-Sided Data Visibility

| Area | Supplier Portal Sees | Internal Team Sees |
|------|---------------------|-------------------|
| Purchase Orders | Their POs only (open, not fully received) | All suppliers' POs, cross-supplier analytics |
| ASN | Their ASNs only — create, track status | All incoming ASNs, gate prep view |
| Gate Entry | Vehicle arrival status, unloading status | Full gate queue, unloading bay assignment, rack/bin location |
| Rack / Bin / Location | ❌ NOT VISIBLE | Full warehouse management, row/rack/bin per item |
| Batch & Serial | What was accepted/rejected per batch | All batches, locations, expiry, consumption, balance |
| Invoices | Submit invoices against their PR, track approval | Full AP — approve, hold, pay, debit notes |
| Scorecard | Their own performance metrics | All supplier scorecards — compare, rank, flag risk |
| Queries | Raise and track queries | Query inbox — respond, add internal notes |

---

## 2. Installation & Setup

### Prerequisites

- ERPNext V15 (Frappe V15) installed on a bench
- Python 3.10+
- Node.js 18+ (for assets)
- Redis and MariaDB running

### Step 1: Get the App

```bash
# Navigate to your frappe-bench directory
cd ~/frappe-bench

# Get the app from GitHub
bench get-app https://github.com/balaji-001-gif/supplier_portal

# OR if you have the app locally:
bench get-app /path/to/supplier_portal
```

### Step 2: Install on Site

```bash
bench --site your-site.local install-app supplier_portal
```

### Step 3: Run Migrations

```bash
bench --site your-site.local migrate
```

This will:
- Create all 7 DocTypes (Advance Shipment Notice, ASN Item, ASN Package, Gate Entry, Supplier Invoice Submission, Supplier Scorecard, Supplier Query)
- Add custom fields to User, Supplier, and Purchase Receipt
- Create the "Supplier Portal" Workspace
- Create "Supplier Portal User" and "Warehouse Staff" roles

### Step 4: Build Assets & Restart

```bash
bench build --app supplier_portal
bench restart
```

### Step 5: Initial Configuration

```bash
# Open your site
bench --site your-site.local console
```

In the ERPNext UI:

1. **Go to:**
   - *Supplier* → Open a supplier → Check **"Portal Access Enabled"** → Save
2. **Go to:**
   - *User* → Open a user → Set **"Supplier"** field to link them → The "Supplier Portal User" role will be auto-assigned via migration patch
3. **Assign Roles:**
   - **Supplier Portal User** → Suppliers (web access only, filtered data)
   - **Warehouse Staff** → Gate guards, warehouse operators
   - **Purchase Manager** → Full access to approve invoices

### Requirements

```
frappe
qrcode[pil]
pillow
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 3. Roles & Permissions

### Role Profiles

| Role | Desk Access | Portal Access | Can Create | Can Submit | Can Approve | Can View All |
|------|:-----------:|:-------------:|:----------:|:----------:|:-----------:|:------------:|
| **Supplier Portal User** | ❌ | ✅ | Own data | Own ASN/Invoices | ❌ | ❌ |
| **Warehouse Staff** | ✅ | ❌ | Gate Entry | Gate Entry | ❌ | ❌ |
| **Stock User** | ✅ | ❌ | PR | PR | ❌ | ❌ |
| **Stock Manager** | ✅ | ❌ | All | All | ✅ | ✅ |
| **Purchase User** | ✅ | ❌ | PO, ASN | PO, ASN | ❌ | All suppliers |
| **Purchase Manager** | ✅ | ❌ | All | All | ✅ | All suppliers |
| **Accounts User** | ✅ | ❌ | PI | PI | ❌ | ❌ |
| **Accounts Manager** | ✅ | ❌ | All | All | ✅ | ✅ |
| **System Manager** | ✅ | ❌ | All | All | ✅ | ✅ |

### Permission Query Conditions

All Supplier Portal Data is automatically filtered:

```python
# Example: When a Supplier Portal User logs in,
# they ONLY see documents where:
# supplier = (their linked supplier from User doctype)
```

**Filtered DocTypes:**
- Purchase Order → `supplier = user's supplier`
- Advance Shipment Notice → `supplier = user's supplier`
- Supplier Invoice Submission → `supplier = user's supplier`
- Supplier Scorecard → `supplier = user's supplier`
- Supplier Query → `supplier = user's supplier`

**Hidden DocTypes (1=0 for portal users):**
- Gate Entry → Portal users cannot see gate entries at all

### Custom Roles Created

| Role | Created By | Purpose |
|------|-----------|---------|
| **Supplier Portal User** | Patch `v1_0/setup_roles_and_permissions.py` | Web-only access for suppliers |
| **Warehouse Staff** | Patch `v1_0/setup_roles_and_permissions.py` | Gate entry, unloading, rack assignment |

---

## 4. DocType Reference

### 4.1 Advance Shipment Notice

| Field | Type | Description |
|-------|------|-------------|
| `naming_series` | Select | Series: `ASN-.YYYY.-` |
| `supplier` | Link → Supplier | Who is sending the shipment |
| `purchase_order` | Link → Purchase Order | PO this ASN is against |
| `asn_date` | Date | Date of ASN creation |
| `expected_delivery_date` | Date | Estimated arrival date |
| `expected_arrival_time` | Time | Estimated arrival time |
| `status` | Select | Draft → Submitted → In Transit → At Gate → Unloading → Received → Cancelled |
| `delivery_challan_no` | Data | Supplier's delivery challan number |
| `challan_date` | Date | Date on the delivery challan |
| `num_packages` | Int | Number of packages in shipment |
| `vehicle_no` | Data | Vehicle number |
| `driver_name` | Data | Driver's name |
| `driver_mobile` | Data | Driver's phone number |
| `transport_company` | Data | Transporter name |
| `lr_no` | Data | LR / Waybill number |
| `eway_bill_no` | Data | E-Way bill number |
| **Child: Items** | Table (ASN Item) | Line items with dispatch/received qty |
| **Child: Packages** | Table (ASN Package) | Package breakdown with QR codes |
| `delivery_challan_attachment` | Attach | PDF of delivery challan |
| `test_certificate` | Attach | COA / test report |
| `packing_list` | Attach | Packing list |
| `remarks` | Text | Special instructions |
| `submitted_by` | Link → User | Who submitted (auto-set) |
| `submitted_on` | Datetime | When submitted (auto-set) |
| **Submittable** | Yes | Can be Submitted/Cancelled |
| **Amendable** | Yes | Can be amended after cancel |

**Validation Rules:**
- Supplier can only create ASN for their own POs
- PO must be submitted (docstatus = 1)
- Dispatch qty cannot exceed pending PO qty (accounts for all previous ASNs)
- On submit: QR codes are auto-generated for each package
- On submit: Warehouse and supplier are notified via email

### 4.2 ASN Item (Child Table)

| Field | Type | Description |
|-------|------|-------------|
| `item_code` | Link → Item | The item being dispatched |
| `item_name` | Read Only | Fetched from item_code |
| `po_detail` | Link → Purchase Order Item | Links back to PO line |
| `po_qty` | Float | Qty ordered (read from PO) |
| `uom` | Link → UOM | Unit of measure |
| `dispatch_qty` | Float | Qty being dispatched (required) |
| `received_qty` | Float | Qty received at warehouse (updated by PR) |
| `accepted_qty` | Float | Qty accepted after inspection (updated by PR) |
| `rejected_qty` | Float | Qty rejected (updated by PR) |
| `short_qty` | Float | Short quantity (auto-calculated) |
| `excess_qty` | Float | Excess quantity (auto-calculated) |
| `batch_no` | Data | Batch/Lot number |
| `manufacturing_date` | Date | Date of manufacture |
| `expiry_date` | Date | Expiry date |
| `serial_nos` | Text | Serial numbers (one per line) |

### 4.3 ASN Package (Child Table)

| Field | Type | Description |
|-------|------|-------------|
| `package_id` | Data | Unique package identifier (e.g., PKG-01) |
| `package_type` | Select | Carton, Pallet, Crate, Bundle, Other |
| `gross_weight` | Float | Gross weight in kg |
| `net_weight` | Float | Net weight in kg |
| `length`, `width`, `height` | Float | Dimensions in cm |
| `volume` | Float (Read Only) | Auto-calculated volume in m³ |
| `qr_code` | Text (Read Only) | JSON payload stored as QR data |
| `qr_generated` | Check (Read Only) | Whether QR has been generated |
| `scanned_at_gate` | Check (Read Only) | Whether package was scanned at gate |
| `scan_timestamp` | Datetime (Read Only) | When the package was scanned |
| `package_status` | Select | Ready → In Transit → At Gate → Unloading → Received → Damaged |

### QR Code Payload Structure

```json
{
  "doc_type": "Advance Shipment Notice",
  "doc_id": "ASN-2025-00001",
  "asn_date": "2025-06-15",
  "supplier_id": "SUPP-00001",
  "supplier_name": "Apex Components Pvt Ltd",
  "po_no": "PO-2025-00891",
  "vehicle_no": "MH12AB1234",
  "driver_name": "Rajesh Kumar",
  "driver_mobile": "+91-9876543210",
  "package_id": "PKG-01",
  "package_type": "Carton",
  "num_packages": 3,
  "challan_no": "DC/2025/00421",
  "challan_date": "2025-06-14",
  "eta_date": "2025-06-17",
  "eta_time": "10:30:00",
  "items": [
    {
      "item_code": "BEARING-6205",
      "item_name": "Bearing Assy 6205",
      "dispatch_qty": 500,
      "uom": "Nos",
      "batch_no": "BATCH-2025-06-001",
      "manufacturing_date": "2025-03-15",
      "expiry_date": "2027-03-15"
    }
  ],
  "scan_url": "https://your-site.local/api/method/supplier_portal.api.gate_entry.scan_qr"
}
```

### 4.4 Gate Entry

| Field | Type | Description |
|-------|------|-------------|
| `naming_series` | Select | Series: `GE-.YYYY.-` |
| `asn_reference` | Link → ASN | Which ASN this gate entry is for |
| `supplier` | Link → Supplier | Supplier name |
| `entry_date` | Date | Date of gate entry |
| `entry_time` | Time | Time of gate entry |
| `status` | Select | At Gate → Document Verification → Waiting for Unloading → Unloading → Completed → Rejected |
| `vehicle_no` | Data | Vehicle number |
| `driver_name` | Data | Driver name |
| `driver_mobile` | Data | Driver mobile |
| `transport_company` | Data | Transporter |
| `lr_no` | Data | LR number |
| `num_packages` | Int | Number of packages |
| `scanned_package_id` | Data (Read Only) | Package ID from QR scan |
| `scan_timestamp` | Datetime (Read Only) | Timestamp of QR scan |
| `gate_guard` | Link → User (Read Only) | Who performed the scan |
| `unloading_bay` | Link → Warehouse | Bay assigned for unloading |
| `unloading_start_time` | Datetime | When unloading began |
| `unloading_end_time` | Datetime | When unloading ended |
| `unloading_duration` | Duration (Read Only) | Auto-calculated |
| `delivery_challan_verified` | Check | DC verified |
| `eway_bill_verified` | Check | E-Way bill verified |
| `physical_inspection_done` | Check | Physical inspection done |
| `remarks` | Text | Notes |
| `purchase_receipt` | Link → PR (Read Only) | Auto-created PR |
| `pr_status` | Data (Read Only) | Draft / Submitted |
| **Submittable** | Yes | |

**Workflow Events:**
- On Submit: Updates ASN status to "At Gate"
- On Submit: Updates scanned package status
- On Submit: Auto-creates a Draft Purchase Receipt with items pre-filled from ASN
- On Cancel: Reverts ASN status back to "Submitted"

### 4.5 Supplier Invoice Submission

| Field | Type | Description |
|-------|------|-------------|
| `naming_series` | Select | Series: `INV-SUB-.YYYY.-` |
| `supplier` | Link → Supplier | Supplier |
| `purchase_receipt` | Link → PR | Which PR this invoice is against |
| `submission_date` | Date | Date of submission |
| `status` | Select | Draft → Pending Approval → Approved → Rejected → Cancelled |
| `invoice_number` | Data | Supplier's invoice number |
| `invoice_date` | Date | Date on the invoice |
| `invoice_amount` | Currency | Invoice amount |
| `tax_amount` | Currency | Tax amount |
| `invoice_attachment` | Attach | PDF of invoice (required) |
| `e_invoice_attachment` | Attach | E-Invoice JSON/XML |
| `remarks` | Text | Notes |
| `approved_by` | Link → User (Read Only) | Who approved |
| `approved_on` | Datetime (Read Only) | When approved |
| `rejection_reason` | Text | Why rejected |
| `purchase_invoice` | Link → PI (Read Only) | Auto-created PI |
| `pi_status` | Data (Read Only) | Draft / Submitted |
| **Submittable** | Yes | Internal approval workflow |

**Workflow Events:**
- On Submit (approval): Auto-creates a Draft Purchase Invoice with items and taxes mapped from PR
- Validation: PR must belong to the same supplier

### 4.6 Supplier Scorecard

| Field | Type | Description |
|-------|------|-------------|
| `supplier` | Link → Supplier | Supplier being scored |
| `fiscal_year_start` | Date | Start of fiscal period |
| `fiscal_year_end` | Date | End of fiscal period |
| `overall_score` | Percent (Read Only) | Weighted average |
| `rating` | Data (Read Only) | A+ to D rating |
| `on_time_delivery_rate` | Percent (Read Only) | % of deliveries on/before schedule |
| `quality_acceptance_rate` | Percent (Read Only) | % accepted vs total received |
| `documentation_compliance_rate` | Percent (Read Only) | % of ASNs with all docs attached |
| `invoice_accuracy_rate` | Percent (Read Only) | % of invoices approved without rejection |
| `calculation_notes` | Text Editor | Notes on calculation |

**Rating Scale:**

| Score | Rating |
|-------|--------|
| 90%+ | A+ — Excellent |
| 80–89% | A — Very Good |
| 70–79% | B — Good |
| 60–69% | C — Average |
| Below 60% | D — Needs Improvement |

**Weighted Formula:**
```
Overall Score = (OTIF × 30%) + (Quality × 30%) + (Documentation × 20%) + (Invoice Accuracy × 20%)
```

### 4.7 Supplier Query

| Field | Type | Description |
|-------|------|-------------|
| `supplier` | Link → Supplier | Who raised the query |
| `subject` | Data | Short subject line |
| `query_category` | Select | Invoice/Payment, PO/Contract, Quality/Rejection, Delivery/Logistics, Documentation, Portal Access, Other |
| `priority` | Select | Low, Medium, High, Urgent |
| `status` | Select | Draft → Open → Responded → Closed |
| `submitted_by` | Link → User (Read Only) | Who submitted |
| `submitted_on` | Datetime (Read Only) | When submitted |
| `query_message` | Text Editor | Detailed query description |
| `reference_doctype` | Select | Optional link: PO, ASN, PR, Invoice, Scorecard |
| `reference_docname` | Dynamic Link | Reference document number |
| `attachment` | Attach | Supporting file |
| `response` | Text Editor | Response from internal team |
| `responded_by` | Link → User (Read Only) | Who responded |
| `responded_on` | Datetime (Read Only) | When responded |
| **Submittable** | Yes | |

**Workflow:**
- Supplier creates & submits → Status = Open → Email sent to purchase team
- Purchase team responds → Status = Responded → Email sent to supplier
- Supplier or team closes → Status = Closed

---

## 5. End-to-End Working Flow

### Complete Lifecycle of a Shipment

```
┌────────────────────────────────────────────────────────────────────┐
│                     END-TO-END WORKFLOW                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  PHASE 1: PO CREATION                                             │
│  ┌──────────┐                                                     │
│  │ Purchase │──► PO Created & Submitted                           │
│  │  Team    │──► Email notification sent to supplier               │
│  └──────────┘    PO appears in supplier portal                     │
│                                                                    │
│  PHASE 2: ASN CREATION (Supplier Portal)                          │
│  ┌──────────┐                                                     │
│  │ Supplier │──► Logs into /supplier_portal                        │
│  │          │──► Clicks "Create ASN"                               │
│  │          │──► Selects PO (loads items automatically)            │
│  │          │──► Enters: dispatch qty, batch no., mfg/expiry      │
│  │          │──► Enters vehicle, driver, challan details           │
│  │          │──► Uploads DC, COA, packing list                     │
│  │          │──► Clicks "Submit ASN & Generate QR"                 │
│  │          │    │                                                 │
│  │          │    ├──► QR codes generated per package               │
│  │          │    ├──► ASN Status: Draft → Submitted               │
│  │          │    ├──► Warehouse notified via email                 │
│  │          │    └──► Supplier gets confirmation email             │
│  └──────────┘                                                      │
│                                                                    │
│  PHASE 3: PRINT & AFFIX QR LABELS (Supplier)                      │
│  ┌──────────┐                                                     │
│  │ Supplier │──► Downloads QR labels PDF from portal               │
│  │          │──► Prints and affixes on each package               │
│  │          │──► Dispatches shipment                               │
│  └──────────┘                                                      │
│                                                                    │
│  PHASE 4: VEHICLE ARRIVES AT GATE (Warehouse)                     │
│  ┌──────────┐                                                     │
│  │  Gate    │──► Vehicle arrives at security gate                  │
│  │  Guard   │──► Guard scans QR code on any package                │
│  │          │    │                                                 │
│  │          │    ├──► System identifies ASN, supplier, PO          │
│  │          │    ├──► Gate Entry pre-filled automatically          │
│  │          │    ├──► Vehicle no, driver, packages all set         │
│  │          │    ├──► No manual typing needed at gate              │
│  │          │    └──► ASN Status: Submitted → At Gate              │
│  │          │                                                      │
│  │          │──► Guard verifies documents (DC, E-Way bill)         │
│  │          │──► Guard submits Gate Entry                          │
│  │          │    │                                                 │
│  │          │    ├──► Draft Purchase Receipt auto-created          │
│  │          │    └──► Unloading queue updated                      │
│  └──────────┘                                                      │
│                                                                    │
│  PHASE 5: UNLOADING & VERIFICATION (Warehouse)                    │
│  ┌──────────┐                                                     │
│  │Warehouse │──► Vehicle moves to unloading bay                    │
│  │  Staff   │──► Operator clocks "Start Unloading"                 │
│  │          │──► Physical count vs ASN items                       │
│  │          │──► Rejects recorded (damaged, wrong, shortage)       │
│  │          │──► Operator clocks "End Unloading"                    │
│  │          │    │                                                 │
│  │          │    ├──► Duration auto-calculated                     │
│  │          │    └──► ASN Status: At Gate → Unloading → ...       │
│  └──────────┘                                                      │
│                                                                    │
│  PHASE 6: PURCHASE RECEIPT (Warehouse/Stores)                     │
│  ┌──────────┐                                                     │
│  │  Stores  │──► Opens the Draft PR created from Gate Entry        │
│  │          │──► Items, qty, batch pre-filled from ASN             │
│  │          │──► Enters accepted qty (may differ from dispatch)    │
│  │          │──► Records rejection reasons                          │
│  │          │──► Assigns warehouse location (rack/bin)              │
│  │          │──► Submits Purchase Receipt                           │
│  │          │    │                                                 │
│  │          │    ├──► ASN Items: received/accepted/rejected updated │
│  │          │    ├──► ASN Status: Unloading → Received            │
│  │          │    ├──► Package Status: → Received                   │
│  │          │    ├──► Gate Entry PR status: Draft → Submitted      │
│  │          │    └──► Supplier notified via email                  │
│  └──────────┘                                                      │
│                                                                    │
│  PHASE 7: INVOICE SUBMISSION (Supplier Portal)                    │
│  ┌──────────┐                                                     │
│  │ Supplier │──► Logs into /supplier_portal/invoices               │
│  │          │──► Clicks "Submit New Invoice"                       │
│  │          │──► Selects the Purchase Receipt                      │
│  │          │──► Uploads invoice PDF                               │
│  │          │──► Enters invoice number, date, amount               │
│  │          │──► Submits                                           │
│  │          │    │                                                 │
│  │          │    ├──► Invoice Status: Pending Approval             │
│  │          │    └──► Accounts team notified                       │
│  └──────────┘                                                      │
│                                                                    │
│  PHASE 8: INVOICE APPROVAL (Accounts)                             │
│  ┌──────────┐                                                     │
│  │ Accounts │──► Reviews invoice submission                        │
│  │  Team    │──► Verifies against PR, rate contract                │
│  │          │──► If OK: Submit (approve)                           │
│  │          │    │                                                 │
│  │          │    ├──► Draft Purchase Invoice auto-created          │
│  │          │    └──► Items & taxes mapped from PR                 │
│  │          │──► If issues: Set rejection reason, Cancel           │
│  └──────────┘                                                      │
│                                                                    │
│  PHASE 9: SCORECARD (Automated - Daily)                           │
│  ┌──────────┐                                                     │
│  │  System  │──► Daily cron recalculates supplier scorecards       │
│  │          │──► Based on actual transaction data                  │
│  │          │──► 4 weighted metrics → Overall Score → Rating       │
│  │          │──► Visible to supplier in portal                     │
│  │          │──► Purchase team can compare across suppliers        │
│  └──────────┘                                                      │
│                                                                    │
│  PHASE 10: QUERIES (As Needed)                                     │
│  ┌──────────┐                                                     │
│  │ Supplier │──► Can raise queries at any point                    │
│  │  OR      │──► Subject, category, priority, reference doc        │
│  │Purchase  │──► Purchase team responds                            │
│  │  Team    │──► Two-way email notifications                       │
│  └──────────┘                                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 6. Standard Operating Procedures (SOPs)

### SOP 1: Supplier Onboarding

**Objective:** Set up a new supplier for portal access.

**Steps:**

1. **Create/Open Supplier:**
   - ERPNext → Buying → Supplier
   - Enter all standard supplier details

2. **Enable Portal Access:**
   - In the Supplier form, check **"Portal Access Enabled"**
   - Set **"Portal User"** to the user who will log in
   - Save

3. **Link User to Supplier:**
   - ERPNext → Users → [The user's name]
   - Set the **"Supplier"** field to the supplier name
   - Save
   - The "Supplier Portal User" role is auto-assigned via patch

4. **Verify Access:**
   - Log out, log in as the supplier user
   - Access: `https://your-site.local/supplier_portal`
   - Verify they see: Dashboard, Purchase Orders, Create ASN, My ASNs, Invoices, Scorecard, Queries

5. **Communicate to Supplier:**
   - Send portal URL, login credentials
   - Share the QR label printing instructions
   - Share the ASN creation SOP below

### SOP 2: ASN Creation (For Suppliers)

**Objective:** Supplier creates and submits an Advance Shipment Notice before dispatching goods.

**Steps:**

1. **Log in**
   - Navigate to `https://your-site.local/supplier_portal`
   - Use your credentials

2. **Start New ASN**
   - Click **"Create ASN"** from the dashboard or
   - Navigate to ASNs → **"+ Create New ASN"**

3. **Select Purchase Order**
   - Choose from open POs (only your POs are listed)
   - Items auto-load with pending quantities

4. **Enter Shipment Details**
   - ASN Date (defaults to today)
   - Expected Delivery Date and Time
   - Delivery Challan No. and Challan Date
   - Number of Packages
   - E-Way Bill No. (if applicable)
   - LR / Way Bill No.

5. **Enter Vehicle & Driver Details**
   - Vehicle Number (required)
   - Driver Name, Driver Mobile
   - Transport Company

6. **Enter Item Details**
   - For each item: Dispatch Qty, Batch No., Mfg Date, Expiry Date
   - Dispatch qty cannot exceed pending PO qty

7. **Upload Documents**
   - Delivery Challan (PDF) — recommended
   - Test Certificate / COA (if applicable)
   - Packing List (if applicable)

8. **Add Remarks** (optional)
   - Special handling instructions, if any

9. **Submit**
   - Click **"Submit ASN & Generate QR Codes"**
   - System validates, creates QR codes per package
   - You will receive a confirmation email

10. **Print QR Labels**
    - Open the ASN detail view
    - Click **"Print QR Labels"**
    - Print and affix one label per package
    - Dispatch the shipment

### SOP 3: Gate Entry (For Warehouse / Gate Staff)

**Objective:** Record vehicle arrival, scan QR codes, initiate unloading process.

**Steps:**

1. **Vehicle Arrives at Gate**
   - Driver presents delivery challan

2. **Scan QR Code**
   - Open **Gate Entry** list
   - Click **"Open QR Scanner"**
   - Point camera at any package QR code
   - System auto-creates/pre-fills Gate Entry:
     - Supplier, ASN, PO
     - Vehicle No., Driver, Mobile
     - Number of packages
     - All from QR data — zero manual typing

3. **Verify Documents**
   - Check Delivery Challan against ASN
   - Verify E-Way Bill (if applicable)
   - Mark checkboxes accordingly

4. **Submit Gate Entry**
   - Click **Submit**
   - System:
     - Updates ASN status to "At Gate"
     - Marks the scanned package as "scanned_at_gate"
     - Adds vehicle to unloading queue
     - Auto-creates a Draft Purchase Receipt
     - Notifies warehouse staff

5. **Direct Vehicle to Unloading Bay**
   - Inform driver of bay number

### SOP 4: Unloading Process (For Warehouse Staff)

**Objective:** Unload, count, inspect, and record received quantities.

**Steps:**

1. **Start Unloading**
   - Open the Gate Entry form
   - Set **"Unloading Bay"** (select warehouse bay)
   - Click **"Start Unloading"** → Sets start timestamp
   - Status changes to "Unloading"

2. **Unload & Inspect**
   - Count all items against ASN quantities
   - Inspect for damage, correctness
   - Record any discrepancies

3. **End Unloading**
   - Click **"End Unloading"** → Sets end timestamp
   - Duration auto-calculated
   - Status changes to "Completed"

4. **Complete Purchase Receipt**
   - Open the Draft PR (linked from Gate Entry)
   - Verify items, quantities, batch numbers
   - Enter **accepted qty** (may differ from dispatch qty)
   - Enter **rejected qty** with rejection reason
   - Assign warehouse location (rack/bin)
   - Submit the Purchase Receipt
   - ASN Status → "Received"
   - Supplier gets notified

### SOP 5: Invoice Submission (For Suppliers)

**Objective:** Submit invoices against delivered Purchase Receipts.

**Steps:**

1. **Log in to Supplier Portal**
   - Navigate to **Invoices**

2. **Submit New Invoice**
   - Click **"+ Submit New Invoice"**
   - Select the Purchase Receipt (only your completed PRs are listed)
   - Enter:
     - Invoice Number (your reference)
     - Invoice Date
     - Invoice Amount (suggested from PR total)
     - Tax Amount (if applicable)
   - Upload Invoice PDF (required)
   - Upload E-Invoice (optional)
   - Add remarks (optional)

3. **Submit** → Status becomes "Pending Approval"

4. **Track Status**
   - View invoice list to see approval status
   - Once approved → Purchase Invoice auto-created in ERPNext
   - Track payment through standard ERPNext process

### SOP 6: Invoice Approval (For Accounts Team)

**Objective:** Review and approve supplier invoice submissions.

**Steps:**

1. **Open Invoice Submission**
   - ERPNext → Supplier Portal → Supplier Invoice Submission
   - Filter: Status = "Pending Approval"

2. **Verify**
   - Invoice matches Purchase Receipt quantities and rates
   - Tax calculations are correct
   - Invoice PDF is legible and matches data

3. **Approve**
   - Click **Submit** (approve action)
   - System auto-creates a Draft Purchase Invoice:
     - Items mapped from PR
     - Taxes mapped from PR
     - Supplier, bill details pre-filled

4. **If Issues Found**
   - Enter rejection reason
   - Click **Cancel**
   - Notify supplier via query or email

5. **Complete Purchase Invoice**
   - Open the Draft Purchase Invoice
   - Verify all details
   - Submit the Purchase Invoice (standard ERPNext PI process)

### SOP 7: Scorecard Review (For Purchase Team)

**Objective:** Monitor supplier performance periodically.

**Steps:**

1. **View Scorecards**
   - ERPNext → Supplier Portal → Supplier Scorecard
   - Or view individual supplier scorecard

2. **Analyze Metrics**
   - On-Time Delivery Rate: Are they meeting schedule dates?
   - Quality Acceptance Rate: Are rejections high?
   - Documentation Compliance: Do they submit all documents?
   - Invoice Accuracy: Are invoices correct first time?

3. **Take Action**
   - Low-rated suppliers: Schedule review meeting
   - Use **Supplier Query** to communicate improvement areas
   - Use data for supplier segmentation (strategic vs. transactional)

4. **Manual Recalculation**
   - Open a scorecard → Click **"Recalculate Score"** to refresh from current data

### SOP 8: Query Management (For Purchase Team)

**Objective:** Respond to supplier queries in a timely manner.

**Steps:**

1. **Monitor Queries**
   - Email notification received for new queries
   - Or check: Supplier Portal → Supplier Query (filter: Status = Open)

2. **Respond**
   - Open the query
   - Click **"Respond to Query"**
   - Enter response in the dialog
   - Click **"Send Response"**
   - Status changes to "Responded"
   - Supplier gets email notification

3. **Close Resolved Queries**
   - Once supplier confirms resolution
   - Click **"Close Query"**
   - Status changes to "Closed"

---

## 7. Supplier Portal Web Pages

The following web pages are available at `/supplier_portal`:

| Route | Page | Description |
|-------|------|-------------|
| `/supplier_portal` | Dashboard | Stats cards, recent ASNs, recent POs, quick links |
| `/supplier_portal/asn` | ASN List | All supplier's ASNs with status filter |
| `/supplier_portal/asn/new` | Create ASN | Full form with PO selection, item loading, docs upload |
| `/supplier_portal/purchase_orders` | PO List | Open POs with progress bars |
| `/supplier_portal/invoices` | Invoices | Invoice list + modal submission form |
| `/supplier_portal/scorecard` | Scorecard | Visual metrics with rating and progress bars |
| `/supplier_portal/queries` | Queries | Query list + modal raise form |

### Dashboard Page Layout

```
┌────────────────────────────────────────────────────────────┐
│  Welcome, [Supplier Name]                                  │
│  Supplier Portal Dashboard                                 │
├────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ 📦 Create │ │ 📋 My    │ │ 📄 POs  │ │ 🧾 Invoice│    │
│  │   ASN     │ │  ASNs    │ │         │ │          │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│  ┌──────────┐ ┌──────────┐                                │
│  │ 📊 Score- │ │ 💬 Queries│                                │
│  │  card     │ │          │                                │
│  └──────────┘ └──────────┘                                │
├────────────────────────────────────────────────────────────┤
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐           │
│  │Open  │ │Pending│ │Pending│ │This  │ │Score │           │
│  │POs: 5│ │ASNs: 3│ │Inv: 2 │ │Mo Dlv│ │ 85%  │           │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘           │
├────────────────────────────────────────────────────────────┤
│  Recent Advance Shipment Notices                           │
│  ┌──────┬────────┬────────┬──────────┬────────┐           │
│  │ASN No│ Date   │ PO No │ Expected │ Status │           │
│  ├──────┼────────┼────────┼──────────┼────────┤           │
│  │ASN.. │06/14  │PO-0891 │ 06/17    │Submitted│          │
│  │ASN.. │06/10  │PO-0876 │ 06/12    │Received │          │
│  └──────┴────────┴────────┴──────────┴────────┘           │
└────────────────────────────────────────────────────────────┘
```

---

## 8. Email Notifications

| Event | Sender | Recipient | Template |
|-------|--------|-----------|----------|
| ASN Submitted | System | Warehouse Staff | `asn_submitted.html` |
| ASN Submitted | System | Supplier (confirmation) | Inline HTML + link to portal |
| Gate Entry Created | System | Warehouse Staff | Inline text |
| PO Issued | System | Supplier | Inline HTML + link to portal |
| PR Submitted | System | Supplier | Inline HTML |
| Query Raised | System | Purchase Team | Inline text |
| Query Responded | System | Supplier | Inline HTML + link to portal |
| ASN Reminder (Draft) | System | Supplier (daily cron) | Inline HTML + link |

---

## 9. Scheduled Tasks (Automation)

### Hourly Tasks

**Task:** `update_asn_eta_status`
**Schedule:** Every hour

**Logic:**
- ASNs with status "Submitted" and expected delivery date = today → Status becomes "In Transit"
- ASNs past expected delivery date with no gate entry → Status becomes "In Transit"

### Daily Tasks

**Task 1:** `send_daily_asn_reminder`
**Schedule:** Daily (e.g., 8:00 AM)

**Logic:**
- Finds ASNs in "Draft" status with expected delivery within 3 days
- Sends reminder emails to suppliers

**Task 2:** `supplier_scorecard_calculation`
**Schedule:** Daily (e.g., 2:00 AM)

**Logic:**
- For each supplier with "portal_access_enabled = 1"
- Creates/updates Supplier Scorecard for current fiscal year
- Calculates all 4 metrics from actual transaction data

---

## 10. API Endpoints

### Internal Whitelisted Methods

| Method | URL | Description |
|--------|-----|-------------|
| `frappe.client.insert` | Standard | Create Supplier Query |
| `frappe.client.get_value` | Standard | Get single field values |
| `frappe.client.get` | Standard | Get full document |
| `frappe.client.get_list` | Standard | List documents |

### Custom API Endpoints

All endpoints: `https://your-site.local/api/method/supplier_portal.api.*`

| Endpoint | Method | Parameters | Returns |
|----------|--------|------------|---------|
| `asn.create_asn` | POST | `data` (JSON) | `{success, asn, message}` |
| `asn.submit_asn` | POST | `asn_name` | `{success, asn, qr_codes, message}` |
| `asn.get_supplier_asn_list` | GET | `filters` (JSON, optional) | `[{asn}]` |
| `asn.get_asn_tracking` | GET | `asn_name` | `{asn, gate_entry, pr, packages}` |
| `asn.get_asn_items` | GET | `purchase_order, asn` | `[{item}]` |
| `gate_entry.scan_qr` | POST | `qr_data` (JSON string) | `{success, gate_entry, asn, ...}` |
| `gate_entry.get_gate_queue` | GET | — | `[{gate_entry}]` |
| `gate_entry.create_gate_entry_from_asn` | POST | `asn_data` (JSON) | Gate Entry doc |
| `gate_entry.start_unloading` | POST | `gate_entry_name, unloading_bay` | `{success, message}` |
| `gate_entry.complete_unloading` | POST | `gate_entry_name` | `{success, message}` |
| `qr_code.generate_qr_code` | POST | `data, size` | `{success, image}` |
| `qr_code.get_package_qr_pdf` | GET | `asn_name` | PDF download |
| `qr_code.get_package_qr_image` | GET | `asn_name, package_id` | PNG download |
| `invoice.submit_invoice` | POST | `data` (JSON) | `{success, invoice, message}` |
| `invoice.get_supplier_invoices` | GET | `filters` (JSON, optional) | `[{invoice}]` |

### QR Scan Endpoint (Gate Scanner)

The QR code on each package contains a `scan_url` that points to:
```
POST /api/method/supplier_portal.api.gate_entry.scan_qr
```

The payload is the QR data itself. On scan:
1. Parses QR JSON
2. Validates ASN exists and is submitted
3. Creates or updates Gate Entry
4. Pre-fills: supplier, vehicle, driver, packages
5. Returns Gate Entry name and ASN summary

---

## 11. Custom Fields

The following custom fields are added to standard DocTypes:

### Purchase Receipt

| Field | Type | Purpose |
|-------|------|---------|
| `gate_entry_reference` | Link → Gate Entry | Tracks which gate entry created this PR |
| `asn_reference` | Link → ASN | Tracks which ASN this PR is from |

### User

| Field | Type | Purpose |
|-------|------|---------|
| `supplier` | Link → Supplier | Links a user to their supplier account for portal filtering |

### Supplier

| Field | Type | Purpose |
|-------|------|---------|
| `portal_access_enabled` | Check | Enable/disable portal access for this supplier |
| `portal_user` | Link → User | Reference to the user account acting as portal login |

---

## 12. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Supplier can't see POs | User not linked to supplier | Set "Supplier" field on User record |
| ASN submission fails "exceeds pending qty" | Another ASN already dispatched the full qty | Check previous ASNs, create partial dispatch |
| QR codes not generating | qrcode library not installed | Run `pip install qrcode[pil]` and restart bench |
| Gate Entry QR scan fails | QR data is malformed or ASN not submitted | Ensure ASN is submitted, QR was generated |
| Purchase Receipt not auto-creating | Gate Entry doesn't have asn_reference set | Create Gate Entry from ASN (QR scan method) |
| Scorecard shows 0% | No transaction data for the period | Check fiscal year settings, recalculate manually |
| Supplier can't log into portal | Portal access not enabled on Supplier | Check "Portal Access Enabled" on Supplier form |
| Web pages not rendering | Assets not built | Run `bench build --app supplier_portal && bench restart` |
| "Supplier Portal User" role not assigned | Migration patch didn't run | Run `bench --site your-site.local migrate` |

### Debugging

**Check if the app is installed:**
```bash
bench --site your-site.local list-apps | grep supplier_portal
```

**Check migrations ran:**
```bash
bench --site your-site.local migrate
```

**View logs:**
```bash
bench --site your-site.local console
frappe.log_error("Debug message", "Supplier Portal")
```

**Re-build assets if portal pages show 404:**
```bash
bench build --app supplier_portal
bench clear-cache
bench restart
```

---

## License

MIT License — See `license.txt`

## Support

For issues, feature requests, or contributions, please use the GitHub repository issue tracker.
