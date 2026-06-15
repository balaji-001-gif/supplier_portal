# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import json
import io
import base64


@frappe.whitelist()
def generate_qr_code(data, size=10):
    """Generate QR code image from data"""
    try:
        import qrcode
        from qrcode.image.pil import PilImage

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=int(size),
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return {
            "success": True,
            "image": "data:image/png;base64,{0}".format(img_str)
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "QR Code Generation Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_package_qr_pdf(asn_name):
    """Generate PDF with all package QR codes for printing"""
    from frappe.utils.pdf import get_pdf

    asn = frappe.get_doc("Advance Shipment Notice", asn_name)
    user_supplier = frappe.db.get_value("User", frappe.session.user, "supplier")
    if user_supplier and user_supplier != asn.supplier and frappe.session.user != "Administrator":
        frappe.throw(frappe._("You don't have permission to access this ASN"))

    html = frappe.render_template(
        "supplier_portal/templates/print_formats/asn_qr_labels.html",
        {"doc": asn}
    )
    pdf = get_pdf(html)

    frappe.local.response.filename = "{0}_QR_Labels.pdf".format(asn_name)
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"


@frappe.whitelist()
def get_package_qr_image(asn_name, package_id):
    """Generate QR code image for a specific package"""
    asn = frappe.get_doc("Advance Shipment Notice", asn_name)
    for pkg in asn.packages:
        if pkg.package_id == package_id and pkg.qr_generated:
            img_base64 = asn.generate_qr_image(package_id)
            frappe.local.response.filename = "{0}_{1}_QR.png".format(asn_name, package_id)
            frappe.local.response.filecontent = base64.b64decode(
                img_base64.split(",")[1] if "," in img_base64 else img_base64
            )
            frappe.local.response.type = "png"
            return
    frappe.throw(frappe._("Package not found or QR not generated"))
