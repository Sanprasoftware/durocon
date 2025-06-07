import frappe
from datetime import date

def execute(filters=None):
    columns,data = get_columns(filters), get_data(filters)

def get_columns(filters):
    columns = []
    if filters.get("scheme_name"):
        scheme_based_on = frappe.get_value("Scheme",filters.get("scheme_name"),"scheme_based_on")
        if scheme_based_on == "Amount":
            columns =  [
                {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 200},
                {"label": "Territory", "fieldname": "territory", "fieldtype": "Data", "width": 150},
                {"label": "Total Amount", "fieldname": "tot_amt", "fieldtype": "Float", "width": 120},
                {"label": "Prize", "fieldname": "prizes", "fieldtype": "Data", "width": 150},
                {"label": "Gift", "fieldname": "gift", "fieldtype": "Data", "width": 150},
            ]
        elif scheme_based_on == "Quantity":
            columns = [
                {"label": "Territory", "fieldname": "territory", "fieldtype": "Data", "width": 200},
                {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
                {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 180},
                {"label": "Min Amount", "fieldname": "min_amt", "fieldtype": "Float", "width": 120},
                {"label": "Max Amount", "fieldname": "max_amt", "fieldtype": "Float", "width": 120},
                {"label": "Total Amount", "fieldname": "total_value", "fieldtype": "Float", "width": 160},
                {"label": "Prize", "fieldname": "prizes", "fieldtype": "Data", "width": 150},
                {"label": "Gift", "fieldname": "gift", "fieldtype": "Data", "width": 150},
            ]
    return columns

def get_data(filters):
    data = []
    if filters.get("scheme_name"):
        scheme_doc = frappe.get_doc("Scheme",filters.get("scheme_name"))
        if scheme_doc.scheme_based_on == "Amount":
            if not scheme_doc.applicable_for_all_retailers:
                invoice_total = 0
                for retailer in scheme_doc.get("applicable_for_retailer"):
                    si_doc = frappe.get_all("Sales Invoice",{"customer":retailer.customer},["territory","sum(total) as total"]) or 0
                    invoice_total += si_doc.total
                    prize,gift = "",""
                    for item in scheme_doc.get("scheme_items"):
                        if item.min_amt < invoice_total < item.max_amt:
                            prize = item.prizes
                            gift = item.gift
                    data.append({
                        "customer":retailer.customer,
                        "territory": si_doc.territory,
                        "tot_amt":invoice_total,
                        "prizes":prize,
                        "gift":gift
                    })
            elif scheme_doc.applicable_for_all_retailers:
                invoice_total = 0
                all_customers = frappe.get_all("Sales Invoice","distinct(customer) as customer")
                for retailer in all_customers:
                    si_doc = frappe.get_all("Sales Invoice",{"customer":retailer.customer},["territory","sum(total) as total"]) or 0
                    invoice_total += si_doc.total
                    prize,gift = "",""
                    for item in scheme_doc.get("scheme_items"):
                        if item.min_amt < invoice_total < item.max_amt:
                            prize = item.prizes
                            gift = item.gift
                    data.append({
                        "customer":retailer.customer,
                        "territory": si_doc.territory,
                        "tot_amt":invoice_total,
                        "prizes":prize,
                        "gift":gift
                    })
    return data
