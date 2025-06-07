# Copyright (c) 2025, Sanpra Software and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	if not filters:
		filters = {}  

	if not filters.get("from_date"):
		frappe.throw("From Date is missing.")	

	if not filters.get("to_date"):  
		frappe.throw("To Date is missing.")

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	customer_filter = filters.get("customer")
	achieved = filters.get("status")

	# Report Columns
	columns = [
		{"label": "Scheme Name", "fieldname": "scheme_name", "fieldtype": "Data", "width": 200},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
		{"label": "Area", "fieldname": "area", "fieldtype": "Link", "options": "Territory", "width": 150},
		{"label": "Scheme Start", "fieldname": "effective_from", "fieldtype": "Date", "width": 120},
		{"label": "Scheme End", "fieldname": "effective_to", "fieldtype": "Date", "width": 120},
		{"label": "Target", "fieldname": "target", "fieldtype": "Currency", "width": 120},
		{"label": "Sales Achieved", "fieldname": "achieved", "fieldtype": "Currency", "width": 120},
		{"label": "Achieved?", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Price", "fieldname": "price", "fieldtype": "Select", "options": "Gift\nAmount", "width": 100},
		{"label": "Gift", "fieldname": "gift", "fieldtype": "Data", "width": 150},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
	]

	data = []

	# Step 1: Get Schemes matching date range and Retailer-based type
	scheme_filters = {
		"scheme_type_for": "Retailer",
		"effective_from": ["<=", to_date],
		"effective_to": [">=", from_date]
	}
	scheme_list = frappe.get_list("Scheme", filters=scheme_filters, pluck='name')

	# Step 2: Get all Retailer customers
	customer_filters = {"custom_retailerdealer": "Retailer"}
	if customer_filter:
		customer_filters["name"] = customer_filter
	customers = frappe.get_all("Customer", filters=customer_filters, fields=["name", "territory"])

	# Step 3: Match schemes with customers directly
	for scheme_name in scheme_list:
		sch_doc = frappe.get_doc("Scheme", scheme_name)

		# Determine applicable retailers
		if sch_doc.applicable_for_all_retailers:
			applicable_customers = [cust["name"] for cust in customers]
		else:
			applicable_customers = [cust.customer for cust in sch_doc.applicable_for_retailers]

		# Step 4: For each matching customer, check achievement
		for cust in customers:
			if cust["name"] in applicable_customers:

				# Get total Sales Order amount for customer within scheme period
				so_total = frappe.db.sql("""
					SELECT SUM(base_net_total) FROM `tabSales Order`
					WHERE customer = %s AND docstatus = 1
					AND transacti	on_date BETWEEN %s AND %s
				""", (cust["name"], sch_doc.effective_from, sch_doc.effective_to))[0][0] or 0.0

				is_achieved = sch_doc.target and so_total >= sch_doc.target
				status = "✅ Achieved" if is_achieved else "❌ Not Achieved"

				# Filter based on achieved status if provided
				if achieved:
					if achieved == "Achieved" and not is_achieved:
						continue
					if achieved == "Not Achieved" and is_achieved:
						continue

				data.append({
					"scheme_name": sch_doc.name,
					"customer": cust["name"],
					"area": cust["territory"],
					"effective_from": sch_doc.effective_from,
					"effective_to": sch_doc.effective_to,
					"target": sch_doc.target,
					"achieved": so_total,
					"status": status,
					"price": sch_doc.price,
					"gift": sch_doc.gift,
					"amount": sch_doc.amount,
				})

	return columns, data
