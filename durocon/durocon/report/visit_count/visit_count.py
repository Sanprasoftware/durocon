# Copyright (c) 2026, Sanpra Software and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, add_days


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": "Employee",
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 180,
		},
		{
			"label": "Employee Name",
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": "Date",
			"fieldname": "date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": "Day Status",
			"fieldname": "day_status",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": "Total Visit",
			"fieldname": "total_visit",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": "9-11",
			"fieldname": "visit_9_11",
			"fieldtype": "Int",
			"width": 60,
		},
		{
			"label": "11-1",
			"fieldname": "visit_11_1",
			"fieldtype": "Int",
			"width": 60,
		},
		{
			"label": "1-3",
			"fieldname": "visit_1_3",
			"fieldtype": "Int",
			"width": 60,
		},
		{
			"label": "3-5",
			"fieldname": "visit_3_5",
			"fieldtype": "Int",
			"width": 60,
		},
		{
			"label": "5-6",
			"fieldname": "visit_5_6",
			"fieldtype": "Int",
			"width": 60,
		},
		{
			"label": "New Customer",
			"fieldname": "lead_count",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": "Existing Customer",
			"fieldname": "customer_count",
			"fieldtype": "Int",
			"width": 120,
		},
	]

	
def get_holiday_dates(employee=None):
	holiday_dates = set()

	holiday_list = None

	if employee:
		holiday_list = frappe.db.get_value(
			"Employee",
			employee,
			"holiday_list"
		)

	# if not holiday_list:
	# 	holiday_list = frappe.db.get_single_value(
	# 		"HR Settings",
	# 		"default_holiday_list"
	# 	)

	if holiday_list:
		holidays = frappe.get_all(
			"Holiday",
			filters={"parent": holiday_list},
			fields=["holiday_date"]
		)

		holiday_dates = {
			str(h.holiday_date)
			for h in holidays
		}

	return holiday_dates


def get_data(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	employee_filter = filters.get("employee")

	if not from_date or not to_date:
		frappe.throw("Please set From Date and To Date")

	conditions = [
		"v.docstatus < 2",
		"v.date BETWEEN %(from_date)s AND %(to_date)s"
	]

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
		LEFT JOIN `tabEmployee` e
			ON e.name = v.employee
		WHERE {" AND ".join(conditions)}
		GROUP BY v.employee, e.employee_name, v.date
		ORDER BY v.employee, v.date
	"""

	visit_data = frappe.db.sql(
		query,
		{
			"from_date": from_date,
			"to_date": to_date,
			"employee": employee_filter,
		},
		as_dict=True,
	)

	visit_map = {
		(row.employee, str(row.date)): row
		for row in visit_data
	}

	employee_filters = {}

	if employee_filter:
		employee_filters["name"] = employee_filter

	employees = frappe.get_all(
		"Employee",
		filters=employee_filters,
		fields=["name", "employee_name"],
		order_by="name"
	)

	all_dates = []
	current_date = getdate(from_date)
	end_date = getdate(to_date)

	while current_date <= end_date:
		all_dates.append(current_date)
		current_date = add_days(current_date, 1)

	data = []

	holiday_cache = {}
	leave_cache = {}

	for emp in employees:

		if emp.name not in holiday_cache:
			holiday_cache[emp.name] = get_holiday_dates(emp.name)

		if emp.name not in leave_cache:
			leave_cache[emp.name] = get_leave_dates(emp.name)

		holiday_dates = holiday_cache[emp.name]
		leave_dates, half_day_dates = leave_cache[emp.name]

		for date in all_dates:

			date_str = str(date)
			day_status = ""

			# Priority:
			# Half Day > On Leave > W/O > Holiday

			if date_str in half_day_dates:
				day_status = "Half Day"

			elif date_str in leave_dates:
				day_status = "On Leave"

			elif date.weekday() == 6:
				day_status = "W/O"

			elif date_str in holiday_dates:
				day_status = "Holiday"

			key = (emp.name, date_str)

			if key in visit_map:
				row = visit_map[key]

				data.append({
					"employee": row.employee,
					"employee_name": emp.employee_name,
					"date": row.date,
					"day_status": day_status,
					"total_visit": row.total_visit or 0,
					"visit_9_11": row.visit_9_11 or 0,
					"visit_11_1": row.visit_11_1 or 0,
					"visit_1_3": row.visit_1_3 or 0,
					"visit_3_5": row.visit_3_5 or 0,
					"visit_5_6": row.visit_5_6 or 0,
					"lead_count": row.lead_count or 0,
					"customer_count": row.customer_count or 0,
				})
			else:
				data.append({
					"employee": emp.name,
					"employee_name": emp.employee_name,
					"date": date,
					"day_status": day_status,
					"total_visit": 0,
					"visit_9_11": 0,
					"visit_11_1": 0,
					"visit_1_3": 0,
					"visit_3_5": 0,
					"visit_5_6": 0,
					"lead_count": 0,
					"customer_count": 0,
				})

	return data




def get_leave_dates(employee):
	leave_dates = set()
	half_day_dates = set()

	leave_applications = frappe.get_all(
		"Leave Application",
		filters={
			"employee": employee,
			"docstatus": 1
		},
		fields=[
			"from_date",
			"to_date",
			"half_day",
			"half_day_date"
		]
	)

	for leave in leave_applications:

		if leave.half_day:
			half_day_date = leave.half_day_date or leave.from_date
			half_day_dates.add(str(getdate(half_day_date)))
			continue

		current_date = getdate(leave.from_date)

		while current_date <= getdate(leave.to_date):
			leave_dates.add(str(current_date))
			current_date = add_days(current_date, 1)

	return leave_dates, half_day_dates