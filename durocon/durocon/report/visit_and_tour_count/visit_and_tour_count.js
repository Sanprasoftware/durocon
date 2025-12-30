const now = new Date();

frappe.query_reports["Visit and Tour Count"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": frappe.datetime.obj_to_str(
                new Date(now.getFullYear(), now.getMonth(), 1),
                "dd-mm-yyyy"
            )
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "default": frappe.datetime.obj_to_str(
                new Date(now.getFullYear(), now.getMonth() + 1, 0),
                "dd-mm-yyyy"
            )
        },
        {
            "fieldname": "employee",
            "label": "Employee",
            "fieldtype": "Link",
            "options": "Employee"
        }
    ]
};
