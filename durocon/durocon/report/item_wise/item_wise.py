# Copyright (c) 2025, Sanpra Software and contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):    	
	return [
		{
			"label": "Scheme Type",
			"fieldname": "scheme_type",
			"fieldtype": "Link",
			"options": "Scheme Type"  
		},
		{
			"label": "Customer Name",
			"fieldname": "customer_name",
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"label": "Scheme Start", 
			"fieldname": "effective_from", 
			"fieldtype": "Date", 
			"width": 120
		},
		{
			"label": "Scheme End", 
			"fieldname": "effective_to", 
			"fieldtype": "Date", 
			"width": 120
		},  
		{
			"label": "Target Amout",
			"fieldname": "target",
			"fieldtype": "Currency",
		},
		{
			"label": "Sales Order",
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options": "Sales Order"
		},
		{
			"label": "Sales Order Date",
			"fieldname": "transaction_date",
			"fieldtype": "Date"
		},
		{
			"label": "Amount",
			"fieldname": "amount",
			"fieldtype": "Currency"
		},
	]  

def get_data(filters):
	data = []

	scheme_filters = {
		"scheme_type_for": "Retailer",
		"effective_from": ["<=", to_date],
		"effective_to": [">=", from_date]
	}
	schemes = frappe.get_list("Scheme", filters=scheme_filters, pluck='name')

	for scheme in schemes:
		sch_doc = frappe.get_doc("Scheme", scheme.name)

		if sch_doc.applicable_for_all_retailers:
			customers = frappe.get_all("Customer", filters={"custom_retailerdealer": "Retailer"}, fields=["name", "customer_name"])
		else:
			customer_names = [row.customer for row in sch_doc.applicable_for_retailers]
			customers = frappe.get_all("Customer", filters={"name": ["in", customer_names]}, fields=["name", "customer_name", "territory"])

		for customer in customers:
			sales_orders = frappe.get_all(
				"Sales Order",
				filters={"customer": customer["name"]},
				fields=["name", "transaction_date", "base_net_total"]
			)

			total_amount = sum(so["base_net_total"] for so in sales_orders) if sales_orders else 0
			latest_so = sorted(sales_orders, key=lambda so: so["transaction_date"], reverse=True)[0] if sales_orders else None
   
			data.append({
				"scheme_type": scheme["scheme_type"],
				"effective_from": scheme["effective_from"],
				"effective_to": scheme["effective_to"],
				"customer_name": customer["customer_name"],
				"target": customer["target"],
				"sales_order": latest_so["name"] if latest_so else "",
				"transaction_date": latest_so["transaction_date"] if latest_so else "",
				"amount": total_amount,
			})
	return data
