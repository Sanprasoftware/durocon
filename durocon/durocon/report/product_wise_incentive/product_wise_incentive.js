// Copyright (c) 2026, Sanpra Software and contributors
// For license information, please see license.txt

frappe.query_reports["Product Wise Incentive"] = {
	"filters": [
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": "\nJan\nFeb\nMar\nApr\nMay\nJun\nJul\nAug\nSep\nOct\nNov\nDec",
			"reqd": 1
		},
		{
			"fieldname": "sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"options": "Sales Person"
		},
		{
			"fieldname": "target_qty_template",
			"label": __("Target Qty Template"),
			"fieldtype": "Link",
			"options": "Target Qty Template"
		}
	]
};
