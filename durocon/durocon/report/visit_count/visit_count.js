// Copyright (c) 2026, Sanpra Software and contributors
// For license information, please see license.txt

frappe.query_reports["Visit Count"] = {
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
			"fieldname": "employee",
			"label": "Employee",
			"fieldtype": "Link",
			"options": "Employee"
		}
	]
};
  
