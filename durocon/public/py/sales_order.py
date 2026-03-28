import frappe

@frappe.whitelist()
def set_cost_center_warehouse(doc, method=None):
    if doc.company == "DUROCON CONCARE PVT LTD":
        doc.set_warehouse = "Finished Goods - DC"
        doc.cost_center = "Main - DC"
        for row in doc.items:   
            row.cost_center =  "Main - DC"