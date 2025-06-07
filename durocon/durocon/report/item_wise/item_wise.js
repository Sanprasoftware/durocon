// Copyright (c) 2025, Sanpra Software and contributors
// For license information, please see license.txt

frappe.query_reports["Item wise"] = {
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
			"fieldname": "customer_name",
			"label": "Customer Name",
			"fieldtype": "Link",
			"options": "Customer"
		}
	]
};
