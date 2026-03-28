# Copyright (c) 2026, Sanpra Software and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	return columns, data

 
def get_columns():
	return [
		{"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 250},
		# {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
		{"label": "Total Visit", "fieldname": "total_visit", "fieldtype": "Int", "width": 100},
		{"label": "9-11", "fieldname": "visit_9_11", "fieldtype": "Int", "width": 60},
		{"label": "11-1", "fieldname": "visit_11_1", "fieldtype": "Int", "width": 60},
		{"label": "1-3", "fieldname": "visit_1_3", "fieldtype": "Int", "width": 60},
		{"label": "3-5", "fieldname": "visit_3_5", "fieldtype": "Int", "width": 60},
		{"label": "5-6", "fieldname": "visit_5_6", "fieldtype": "Int", "width": 60},
		{"label": "New Customer", "fieldname": "lead_count", "fieldtype": "Int", "width": 120},
		{"label": "Existing Customer", "fieldname": "customer_count", "fieldtype": "Int", "width": 120},
	]


def get_data(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	employee_filter = filters.get("employee")

	if not from_date or not to_date:
		frappe.throw("Please set From Date and To Date")

	conditions = ["v.docstatus < 2", "v.date BETWEEN %(from_date)s AND %(to_date)s"]
	if employee_filter:
		conditions.append("v.employee = %(employee)s")

	query = f"""
		SELECT
			v.employee,
			e.employee_name,
			v.date,
			COUNT(v.name) AS total_visit,
			SUM(CASE WHEN v.visit_to = 'Lead' THEN 1 ELSE 0 END) AS lead_count,
			SUM(CASE WHEN v.visit_to = 'Customer' THEN 1 ELSE 0 END) AS customer_count,
			SUM(CASE WHEN v.visit_time >= '09:00:00' AND v.visit_time < '11:00:00' THEN 1 ELSE 0 END) AS visit_9_11,
			SUM(CASE WHEN v.visit_time >= '11:00:00' AND v.visit_time < '13:00:00' THEN 1 ELSE 0 END) AS visit_11_1,
			SUM(CASE WHEN v.visit_time >= '13:00:00' AND v.visit_time < '15:00:00' THEN 1 ELSE 0 END) AS visit_1_3,
			SUM(CASE WHEN v.visit_time >= '15:00:00' AND v.visit_time < '17:00:00' THEN 1 ELSE 0 END) AS visit_3_5,
			SUM(CASE WHEN v.visit_time >= '17:00:00' AND v.visit_time < '18:00:00' THEN 1 ELSE 0 END) AS visit_5_6
		FROM (
			SELECT
				name,
				employee,
				`date`,
				docstatus,
				visit_to,
				COALESCE(`time`, TIME(visit_in_time)) AS visit_time
			FROM `tabVisit`
		) v
		LEFT JOIN `tabEmployee` e ON e.name = v.employee
		WHERE {" AND ".join(conditions)}
		GROUP BY v.employee, e.employee_name, v.date
		ORDER BY v.employee, v.date
	"""

	return frappe.db.sql(
		query,
		{"from_date": from_date, "to_date": to_date, "employee": employee_filter},
		as_dict=True,
	)
 
