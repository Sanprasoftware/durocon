import frappe

@frappe.whitelist()
def get_data(doc, method):
    customers = frappe.get_all("Customer",filters={"name": doc.customer},fields=["custom_warehouse"])
    # company_sw = frappe.get_all("Company",filters={"name": doc.company},fields=["custom_source_warehouse"])
    company_source_wh = frappe.get_value("Company",doc.company,"custom_source_warehouse")

    for cust in customers:
        if doc.update_stock == 1:
            warehouses = frappe.get_all("Warehouse",filters={"name": cust.custom_warehouse},fields=["company"] )
            for wh in warehouses:
                data = frappe.new_doc("Stock Entry")
                data.stock_entry_type = "Material Transfer",  
                # data.company = wh.company,
                data.company = doc.company,
                data.custom_sales_invoice = doc.name

                for item in doc.items:
                    # frappe.throw(str(item.rate))
                    data.append("items",{
                        "item_code": item.item_code,
                        "qty": item.qty,
                        "basic_rate": item.rate,
                        "uom": item.uom,
                        "t_warehouse": cust.custom_warehouse,
                        "s_warehouse": company_source_wh
                        })
                data.save()
                data.submit()
        # else:
        #     frappe.throw("No custom warehouse found for this customer.")

    


    # disributor = frappe.get_value("Company",filters={"default_warehouse_for_sales_return": custo},fieldname=["name"])
    # frappe.throw(str(disributor))
    # match_warehouse = frappe.get_all("Warehouse", filters={"name": custo}, fields={"company"})
    # for m in match_warehouse:
    #     frappe.throw(str(m))

    # data = frappe.new_doc("Stock Entry")

    # data.stock_entry_type = "Material Receipt",  
    # data.company = match_warehouse,
    # data.custom_sales_invoice = doc.name

    # for item in doc.items:
    #     # frappe.throw(str(item.rate))
    #     data.append("items",{
    #         "item_code": item.item_code,
    #         "qty": item.qty,
    #         "basic_rate": item.rate,
    #         "uom": item.uom,
    #         "t_warehouse": "Om Sai Traders - DCD"
    #     })
    # data.save()
    # data.submit()