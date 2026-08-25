# Copyright (c) 2026, Sanpra Software and contributors
# For license information, please see license.txt

import frappe
from datetime import date
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": "Sales Person",
			"fieldname": "sales_person",
			"fieldtype": "Link",
			"options": "Sales Person",
			"width": 220,
		},
		{
			"label": "Item Name",
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 240,
		},
		{
			"label": "Target Qty",
			"fieldname": "target_qty",
			"fieldtype": "Float",
			"width": 120,
			"precision": 2,
		},
		{
			"label": "Achive Qty",
			"fieldname": "achive_qty",
			"fieldtype": "Float",
			"width": 120,
			"precision": 2,
		},
		{
			"label": "Pending",
			"fieldname": "pending",
			"fieldtype": "Float",
			"width": 120,
			"precision": 2,
		},
		{
			"label": "Achive Percentage",
			"fieldname": "achive_percentage",
			"fieldtype": "Percent",
			"width": 140,
			"precision": 2,
		},
		{
			"label": "Achieved",
			"fieldname": "achieved",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": "Incentive Rate",
			"fieldname": "incentive_rate",
			"fieldtype": "Currency",
			"width": 140,
		},
	]


def get_data(filters):
	month = get_month(filters)
	if not month:
		return []

	sales_persons = get_sales_persons(filters)
	if not sales_persons:
		return []

	template_names = {row.custom_target_qty_template for row in sales_persons if row.custom_target_qty_template}
	targets = get_targets(template_names, month)
	if not targets:
		return []

	achieved_qty_map = get_achieved_qty_map(sales_persons, targets, month)

	data = []
	for sales_person in sales_persons:
		template = sales_person.custom_target_qty_template
		for target in targets.get(template, []):
			achive_qty = achieved_qty_map.get((sales_person.name, target.item_code), 0)
			target_qty = flt(target.target_qty)
			achive_percentage = (flt(achive_qty) / target_qty * 100) if target_qty else 0
			data.append(
				{
					"sales_person": sales_person.name,
					"item_name": target.item_name,
					"target_qty": target_qty,
					"achive_qty": achive_qty,
					"pending": max(target_qty - achive_qty, 0),
					"achive_percentage": achive_percentage,
					"achieved": "Yes" if achive_percentage >= 100 else "No",
					"incentive_rate": target.incentive_rate,
				}
			)

	return data


def get_sales_persons(filters):
	conditions = ["sp.custom_target_qty_template IS NOT NULL", "sp.custom_target_qty_template != ''"]
	values = {}

	if filters.get("sales_person"):
		conditions.append("sp.name = %(sales_person)s")
		values["sales_person"] = filters.sales_person

	if filters.get("target_qty_template"):
		conditions.append("sp.custom_target_qty_template = %(target_qty_template)s")
		values["target_qty_template"] = filters.target_qty_template

	return frappe.db.sql(
		"""
		SELECT
			sp.name,
			sp.custom_target_qty_template,
			tqt.fiscal_year
		FROM `tabSales Person` sp
		INNER JOIN `tabTarget Qty Template` tqt
			ON tqt.name = sp.custom_target_qty_template
		WHERE {conditions}
		ORDER BY sp.name
		""".format(conditions=" AND ".join(conditions)),
		values,
		as_dict=True,
	)


def get_month(filters):
	month = (filters.get("month") or "").strip().lower()
	month_map = {
		"jan": {"fieldname": "jan", "month_number": 1},
		"feb": {"fieldname": "feb", "month_number": 2},
		"mar": {"fieldname": "mar", "month_number": 3},
		"apr": {"fieldname": "apr", "month_number": 4},
		"may": {"fieldname": "may", "month_number": 5},
		"jun": {"fieldname": "jun", "month_number": 6},
		"jul": {"fieldname": "jul", "month_number": 7},
		"aug": {"fieldname": "aug", "month_number": 8},
		"sep": {"fieldname": "sep", "month_number": 9},
		"oct": {"fieldname": "oct", "month_number": 10},
		"nov": {"fieldname": "nov", "month_number": 11},
		"dec": {"fieldname": "dec", "month_number": 12},
	}
	return month_map.get(month[:3])


def get_targets(template_names, month):
	if not template_names:
		return {}

	rows = frappe.db.sql(
		"""
		SELECT
			parent,
			item_code,
			COALESCE(NULLIF(item_name, ''), item_code) AS item_name,
			`{month_field}` AS target_qty,
			incentive_rate
		FROM `tabItem based target`
		WHERE parenttype = 'Target Qty Template'
			AND parent IN %(template_names)s
			AND item_code IS NOT NULL
			AND item_code != ''
		ORDER BY idx
		""".format(month_field=month["fieldname"]),
		{"template_names": tuple(template_names)},
		as_dict=True,
	)

	targets = {}
	for row in rows:
		targets.setdefault(row.parent, []).append(row)

	return targets


def get_achieved_qty_map(sales_persons, targets, month):
	item_codes = {
		target.item_code
		for template_targets in targets.values()
		for target in template_targets
		if target.item_code
	}
	if not item_codes:
		return {}

	date_range_sales_persons = {}
	for sales_person in sales_persons:
		date_range = get_month_date_range(sales_person.fiscal_year, month["month_number"])
		if date_range:
			date_range_sales_persons.setdefault(date_range, []).append(sales_person.name)

	achieved_qty_map = {}
	for date_range, date_range_sales_person_names in date_range_sales_persons.items():
		rows = frappe.db.sql(
			"""
			SELECT
				st.sales_person,
				sii.item_code,
				SUM(sii.qty * IFNULL(NULLIF(st.allocated_percentage, 0), 100) / 100) AS achive_qty
			FROM `tabSales Invoice` si
			INNER JOIN `tabSales Invoice Item` sii
				ON sii.parent = si.name
			INNER JOIN `tabSales Team` st
				ON st.parent = si.name
				AND st.parenttype = 'Sales Invoice'
			WHERE si.docstatus = 1
				AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND st.sales_person IN %(sales_persons)s
				AND sii.item_code IN %(item_codes)s
			GROUP BY st.sales_person, sii.item_code
			""",
			{
				"from_date": date_range[0],
				"to_date": date_range[1],
				"sales_persons": tuple(date_range_sales_person_names),
				"item_codes": tuple(item_codes),
			},
			as_dict=True,
		)

		for row in rows:
			achieved_qty_map[(row.sales_person, row.item_code)] = flt(row.achive_qty)

	return achieved_qty_map


def get_month_date_range(fiscal_year, month_number):
	fiscal_year_dates = frappe.db.get_value(
		"Fiscal Year",
		fiscal_year,
		["year_start_date", "year_end_date"],
		as_dict=True,
	)
	if not fiscal_year_dates:
		return None

	fiscal_year_start = frappe.utils.getdate(fiscal_year_dates.year_start_date)
	fiscal_year_end = frappe.utils.getdate(fiscal_year_dates.year_end_date)

	for year in range(fiscal_year_start.year, fiscal_year_end.year + 1):
		month_start = date(year, month_number, 1)
		next_month = date(year + 1, 1, 1) if month_number == 12 else date(year, month_number + 1, 1)
		month_end = date.fromordinal(next_month.toordinal() - 1)

		if month_start <= fiscal_year_end and month_end >= fiscal_year_start:
			return max(month_start, fiscal_year_start), min(month_end, fiscal_year_end)

	return None
