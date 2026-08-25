// // Copyright (c) 2026, Sanpra Software and contributors
// // For license information, please see license.txt

// frappe.query_reports["Territory Scheme"] = {
// 	"filters": [

// 	]
// };
 

frappe.query_reports["Territory Scheme"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "territory",
            "label": __("Territory"),
            "fieldtype": "Link",
            "options": "Territory"
        },
        {
            "fieldname": "scheme",
            "label": __("Scheme"),
            "fieldtype": "Link",
            "options": "Scheme Master"
        },
        {
            "fieldname": "item_code",
            "label": __("Item Code"),
            "fieldtype": "Link",
            "options": "Item"
        }
    ]
}