# Supplier Portal for ERPNext V15

Comprehensive two-sided supplier portal with ASN (Advanced Shipment Notice), QR code package tracking, gate entry management, and role-based access control.

## Features

- ✅ **Two-sided portal** - Role-based access splits supplier vs internal views
- ✅ **ASN Management** - Full advance shipment notice workflow with batch/serial tracking
- ✅ **QR Code Generation** - Per-package QR with complete JSON data payload
- ✅ **Gate Entry** - QR scan pre-populates all fields at gate, zero manual entry
- ✅ **Purchase Receipt Integration** - Auto-created from gate entry
- ✅ **Supplier Filtering** - All queries filtered by logged-in supplier
- ✅ **Document Attachments** - Challan, COA, certs upload
- ✅ **Status Tracking** - Real-time visibility for suppliers
- ✅ **Permission System** - Strict role-based security

## DocTypes

| DocType | Description |
|---------|-------------|
| Advance Shipment Notice | Supplier-submitted shipment notification with items, batch, vehicle info |
| ASN Item | Child table for ASN line items with dispatch/received/accepted qty |
| ASN Package | Child table for package-level breakdown with QR code generation |
| Gate Entry | Warehouse gate entry with QR scan, vehicle, unloading tracking |
| Supplier Invoice Submission | Supplier-submitted invoices against Purchase Receipts |
| Supplier Scorecard | Performance tracking with OTIF, quality, documentation metrics |
| Supplier Query | Two-way communication channel between supplier and buyer |

## Installation

```bash
# From frappe-bench directory
bench get-app https://github.com/yourcompany/supplier_portal
bench --site your-site.local install-app supplier_portal
bench --site your-site.local migrate
bench build --app supplier_portal
bench restart
```

## Architecture

```
Supplier Portal (Web)          Internal ERPNext (Full)
┌─────────────────────┐       ┌──────────────────────────┐
│ • Their POs only     │       │ • All suppliers          │
│ • Create ASN         │       │ • Gate queue management  │
│ • Track shipments    │       │ • Rack/bin assignment    │
│ • Submit invoices    │       │ • Batch & location       │
│ • View scorecard     │       │ • Full AP & scorecards   │
│ • Raise queries      │       │ • Query response         │
└─────────────────────┘       └──────────────────────────┘
         ↕                              ↕
         └────────── ERPNext ───────────┘
              Role-based access split
```

## Roles

| Role | Access |
|------|--------|
| Supplier Portal User | Web portal login, filtered data only |
| Warehouse Staff | Gate inward, rack assignment, bin management |
| Purchase Manager | Full ERPNext, approve invoices, all scorecards |
