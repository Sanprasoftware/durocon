import frappe
from frappe.utils import add_days, add_months, getdate


def delete_attachment(doc, method=None):
    """Delete all files attached to check-ins dated exactly three months earlier."""
    target_date = add_months(getdate(doc.time), -3)
    next_date = add_days(target_date, 1)

    checkin_names = frappe.get_all(
        "Employee Checkin",
        filters=[
            ["time", ">=", target_date],
            ["time", "<", next_date],
        ],
        pluck="name",
    )

    if not checkin_names:
        return

    attachment_names = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Employee Checkin",
            "attached_to_name": ["in", checkin_names],
        },
        pluck="name",
    )

    for attachment_name in attachment_names:
        frappe.delete_doc("File", attachment_name, ignore_permissions=True)
