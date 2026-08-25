import frappe

def execute(filters=None):
    columns = [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": "Territory", "fieldname": "territory", "fieldtype": "Link", "options": "Territory", "width": 150},
        {"label": "Total Qty", "fieldname": "total_qty", "fieldtype": "Float", "width": 120}
    ]
    
    data = frappe.db.sql("""
        SELECT 
            soi.item_code,
            soi.item_name,
            so.territory,
            SUM(soi.qty) as total_qty
        FROM `tabSales Order` so
        JOIN `tabSales Order Item` soi ON so.name = soi.parent
        WHERE so.docstatus = 1
        {conditions}
        GROUP BY so.territory, soi.item_code
        ORDER BY so.territory, soi.item_code
    """.format(conditions=get_conditions(filters)), filters, as_dict=True)
    
    return columns, data

def get_conditions(filters):
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND so.transaction_date BETWEEN %(from_date)s AND %(to_date)s"
    if filters.get("territory"):
        conditions += " AND so.territory = %(territory)s"
    if filters.get("item_code"):
        conditions += " AND soi.item_code = %(item_code)s"
    return conditions