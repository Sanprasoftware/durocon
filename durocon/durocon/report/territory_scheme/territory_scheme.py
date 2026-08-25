import frappe
from frappe import _

def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "label": _("Territory"),
            "fieldname": "territory",
            "fieldtype": "Link",
            "options": "Territory",
            "width": 150
        },
        {
            "label": _("Scheme"),
            "fieldname": "scheme",
            "fieldtype": "Link",
            "options": "Scheme Master",
            "width": 150
        },
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Scheme Qty"),
            "fieldname": "scheme_qty",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Qty"),
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("YES/NO"),
            "fieldname": "is_exceeded",
            "fieldtype": "Data",
            "width": 100
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    sales_data = frappe.db.sql("""
        SELECT 
            so.territory,
            soi.item_code,
            soi.item_name,
            SUM(soi.qty) as qty
        FROM `tabSales Order` so
        JOIN `tabSales Order Item` soi ON so.name = soi.parent
        WHERE so.docstatus = 1
        {conditions}
        GROUP BY so.territory, soi.item_code, soi.item_name
    """.format(conditions=conditions), filters, as_dict=True)
    
    result = []
    
    for row in sales_data:
        applicable_schemes = get_applicable_schemes(
            row.territory,
            filters.get("from_date"),
            filters.get("to_date"),
            filters.get("scheme"),
        )
        
        for scheme in applicable_schemes:
            scheme_item = get_scheme_item(scheme, row.item_code)
            
            if scheme_item:
                scheme_qty = scheme_item.get("qty", 0)
                is_exceeded = "Yes" if row.qty > scheme_qty else "No"
                
                result.append({
                    "territory": row.territory,
                    "scheme": scheme,
                    "item_code": row.item_code,
                    "item_name": row.item_name,
                    "scheme_qty": scheme_qty,
                    "qty": row.qty,
                    "is_exceeded": is_exceeded
                })
            else:
                result.append({
                    "territory": row.territory,
                    "scheme": scheme,
                    "item_code": row.item_code,
                    "item_name": row.item_name,
                    "scheme_qty": 0,
                    "qty": row.qty,
                    "is_exceeded": "No"
                })
    
    return result

def get_applicable_schemes(territory, from_date=None, to_date=None, scheme=None):
    """Get all schemes mapped to a territory and active during the selected period."""
    scheme_condition = ""
    date_condition = ""
    values = [territory]

    if from_date and to_date:
        date_condition = """
          AND sm.from_date <= %s
          AND sm.to_date >= %s
        """
        values.extend([to_date, from_date])

    if scheme:
        scheme_condition = " AND sai.scheme = %s"
        values.append(scheme)

    scheme_rows = frappe.db.sql("""
        SELECT DISTINCT sai.scheme
        FROM `tabScheme Apply` sa
        JOIN `tabScheme Apply Items` sai ON sai.parent = sa.name
        JOIN `tabScheme Master` sm ON sm.name = sai.scheme
        WHERE sa.territory = %s
          AND sa.docstatus < 2
          {date_condition}
          {scheme_condition}
    """.format(
        date_condition=date_condition,
        scheme_condition=scheme_condition
    ), tuple(values), as_dict=True)

    return [row.scheme for row in scheme_rows if row.scheme]

def get_scheme_item(scheme_name, item_code):
    """Get scheme item details for a specific item"""
    return frappe.db.get_value(
        "Scheme Master Items",
        {"parent": scheme_name, "item_code": item_code},
        ["item_code", "item_name", "qty"],
        as_dict=True
    )

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND so.transaction_date BETWEEN %(from_date)s AND %(to_date)s"
    
    if filters.get("territory"):
        conditions += " AND so.territory = %(territory)s"
    
    if filters.get("item_code"):
        conditions += " AND soi.item_code = %(item_code)s"
    
    return conditions
