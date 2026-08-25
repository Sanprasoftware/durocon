# Copyright (c) 2026, Sanpra Software and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_months, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Customer Name",
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 220,
		},
		{
			"label": "Territory",
			"fieldname": "territory",
			"fieldtype": "Link",
			"options": "Territory",
			"width": 160,
		},
		{
			"label": "Last Purchase Date",
			"fieldname": "last_purchase_date",
			"fieldtype": "Date",
			"width": 150,
		},
		{
			"label": "Non-GST Amount",
			"fieldname": "non_gst_amount",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": "Status",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": "Contact No",
			"fieldname": "contact_no",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": "Address",
			"fieldname": "address",
			"fieldtype": "Data",
			"width": 300,
		},
	]


def get_data(filters):
	conditions = ["c.custom_retailerdealer = %(dealer_type)s"]
	values = {
		"dealer_type": "Dealer",
		"active_from": add_months(nowdate(), -4),
	}

	if filters.get("customer"):
		conditions.append("c.name = %(customer)s")
		values["customer"] = filters.customer

	if filters.get("territory"):
		conditions.append("c.territory = %(territory)s")
		values["territory"] = filters.territory

	status_filter = filters.get("status")
	if status_filter == "Active":
		conditions.append("activity.last_purchase_date >= %(active_from)s")
	elif status_filter == "Non Active":
		conditions.append("(activity.last_purchase_date IS NULL OR activity.last_purchase_date < %(active_from)s)")

	return frappe.db.sql(
		"""
		SELECT
			c.name AS customer,
			c.territory,
			activity.last_purchase_date,
			COALESCE(invoice_amount.non_gst_amount, order_amount.non_gst_amount, 0) AS non_gst_amount,
			CASE
				WHEN activity.last_purchase_date >= %(active_from)s THEN 'Active'
				ELSE 'Non Active'
			END AS status,
			COALESCE(
				NULLIF(c.mobile_no, ''),
				NULLIF(primary_contact.mobile_no, ''),
				NULLIF(primary_contact.phone, ''),
				linked_contact.contact_no,
				''
			) AS contact_no,
			COALESCE(
				NULLIF(primary_address.address, ''),
				linked_address.address,
				NULLIF(c.primary_address, ''),
				''
			) AS address
		FROM `tabCustomer` c
		LEFT JOIN (
			SELECT
				customer,
				MAX(transaction_date) AS last_purchase_date
			FROM (
				SELECT customer, posting_date AS transaction_date
				FROM `tabSales Invoice`
				WHERE docstatus = 1
				UNION ALL
				SELECT customer, transaction_date
				FROM `tabSales Order`
				WHERE docstatus = 1
			) sales_activity
			GROUP BY customer
		) activity ON activity.customer = c.name
		LEFT JOIN (
			SELECT
				customer,
				SUM(base_net_total) AS non_gst_amount
			FROM `tabSales Invoice`
			WHERE docstatus = 1
			GROUP BY customer
		) invoice_amount ON invoice_amount.customer = c.name
		LEFT JOIN (
			SELECT
				customer,
				SUM(base_net_total) AS non_gst_amount
			FROM `tabSales Order`
			WHERE docstatus = 1
			GROUP BY customer
		) order_amount ON order_amount.customer = c.name
		LEFT JOIN `tabContact` primary_contact
			ON primary_contact.name = c.customer_primary_contact
		LEFT JOIN (
			SELECT
				dl.link_name,
				MAX(
					COALESCE(
						NULLIF(contact.mobile_no, ''),
						NULLIF(contact.phone, '')
					)
				) AS contact_no
			FROM `tabDynamic Link` dl
			INNER JOIN `tabContact` contact
				ON contact.name = dl.parent
			WHERE dl.parenttype = 'Contact'
				AND dl.link_doctype = 'Customer'
			GROUP BY dl.link_name
		) linked_contact ON linked_contact.link_name = c.name
		LEFT JOIN (
			SELECT
				name,
				CONCAT_WS(
					', ',
					NULLIF(address_line1, ''),
					NULLIF(address_line2, ''),
					NULLIF(city, ''),
					NULLIF(state, ''),
					NULLIF(pincode, '')
				) AS address
			FROM `tabAddress`
		) primary_address ON primary_address.name = c.customer_primary_address
		LEFT JOIN (
			SELECT
				dl.link_name,
				MAX(
					CONCAT_WS(
						', ',
						NULLIF(address.address_line1, ''),
						NULLIF(address.address_line2, ''),
						NULLIF(address.city, ''),
						NULLIF(address.state, ''),
						NULLIF(address.pincode, '')
					)
				) AS address
			FROM `tabDynamic Link` dl
			INNER JOIN `tabAddress` address
				ON address.name = dl.parent
			WHERE dl.parenttype = 'Address'
				AND dl.link_doctype = 'Customer'
			GROUP BY dl.link_name
		) linked_address ON linked_address.link_name = c.name
		WHERE {conditions}
		ORDER BY c.customer_name, c.name
		""".format(conditions=" AND ".join(conditions)),
		values,
		as_dict=True,
	)
 
