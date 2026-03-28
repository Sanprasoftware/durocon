import frappe

# def create_address(doc, method=None):
#     pass
    # new_doc = frappe.new_doc("Address")
    # new_doc.address_title = doc.lead_name
    # new_doc.address_type = "Billing"
    # new_doc.address_line1 = doc.custom_address
    # new_doc.city = doc.city
    # new_doc.state = doc.state
    # new_doc.country = doc.country

    # # ✅ FIX: convert pincode to string
    # if doc.custom_pincode:
    #     new_doc.pincode = str(doc.custom_pincode)

    # new_doc.email_id = doc.email_id
    # new_doc.phone = doc.phone

    # new_doc.append("links", {
    #     "link_doctype": "Lead",
    #     "link_name": doc.name
    # })
    # new_doc.save(ignore_permissions=True)
