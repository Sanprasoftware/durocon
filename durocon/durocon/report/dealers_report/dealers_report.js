// Copyright (c) 2026, Sanpra Software and contributors
// For license information, please see license.txt

frappe.query_reports["Dealers Report"] = {
	"filters": [
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"get_query": function() {
				return {
					"filters": {
						"custom_retailerdealer": "Dealer"
					}
				};
			}
		},
		{
			"fieldname": "territory",
			"label": __("Territory"),
			"fieldtype": "Link",
			"options": "Territory"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nNon Active"
		}
	]
};
 
