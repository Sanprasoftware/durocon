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


from frappe.utils import add_days, add_months, getdate


def delete_attachment(doc, method=None):
    """Delete all files attached to check-ins dated exactly three months earlier."""
    target_date = add_months(getdate(doc.creation), -3)
    next_date = add_days(target_date, 1)

    lead_names = frappe.get_all(
        "Lead",
        filters=[
            ["creation", ">=", target_date],
            ["creation", "<", next_date],
        ],
        pluck="name",
    )
    

    if not lead_names:
        return

    attachment_names = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Lead",
            "attached_to_name": ["in", lead_names],
        },
        pluck="name",
    )

    for attachment_name in attachment_names:
        frappe.delete_doc("File", attachment_name, ignore_permissions=True)
