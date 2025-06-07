// Copyright (c) 2025, Sanpra Software and contributors
// For license information, please see license.txt

frappe.query_reports["Retailer Area Wise Scheme Report"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "reqd": 1
        },
        {  
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "reqd": 1
        },
        {
            "fieldname": "customer",
            "label": "Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "reqd": 0
        },
        {
            "fieldname": "area",
            "label": "Area",
            "fieldtype": "Link",
            "options": "Territory",
            "reqd": 0
        },
		{
			"fieldname": "status",
			"label": "Achieved?",
			"fieldtype": "Select",
			"options": "\nAchieved\nNot Achieved",
			"reqd": 0
		}
    ]
};
