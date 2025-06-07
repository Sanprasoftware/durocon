// Copyright (c) 2025, Sanpra Software and contributors
// For license information, please see license.txt

frappe.query_reports["Retailer Target"] = {
	"filters": [
		{
			"fieldname": "effective_from",
			"label": "Form Date",
			"fieldtype": "Date"
		},
		{
			"fieldname": "effective_to",
			"label": "To Date",
			"fieldtype": "Date"
		},
		{
			"fieldname": "customer_name",
			"label": "Customer Name",
			"fieldtype": "Link",	
			"options": "Customer"
		},
		{
			"fieldname": "scheme_name",
			"label": "Scheme",
			"fieldtype": "Link",
			"options": "Scheme",
			"reqd": 1,  
			"default":"Retailer Wise"
		},
		// {
		// 	"fieldname": "scheme_based_on",
		// 	"label": "Scheme Based On",
		// 	"fieldtype": "Select",  
		// 	"options": ["Quantity", "Amount"]
		// },	  
	]
};
  