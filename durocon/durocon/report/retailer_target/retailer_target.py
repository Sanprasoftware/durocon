
import frappe
from datetime import date

def execute(filters=None):
    filters = filters or {}

    if not filters.get("effective_to"):
        filters["effective_to"] = date.today().isoformat()
    
    scheme_doc = frappe.get_doc("Scheme", filters.get("scheme_name"))
    if scheme_doc.name == "Area Wise":
        return get_columns(filters), get_area_wise_scheme_data(filters)
    else:
        return get_columns(filters), get_data(filters) 
  
    # return get_columns(filters), get_area_wise_scheme_data(filters)

def get_columns(filters):
    scheme_doc = frappe.get_doc("Scheme", filters.get("scheme_name"))
    if scheme_doc.scheme_based_on == "Quantity":
        return [
            {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 250},
            # {"label": "Territory", "fieldname": "territory", "fieldtype": "Data", "width": 150},
            {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 220},
            {"label": "Target Qty", "fieldname": "target_qty", "fieldtype": "Float", "width": 120, "precision": 2},
            {"label": "Total Qty", "fieldname": "total_value", "fieldtype": "Float", "width": 120, "precision": 2},
            {"label": "Prize", "fieldname": "prizes", "fieldtype": "Data", "width": 140},
            {"label": "Gift", "fieldname": "gift", "fieldtype": "Data", "width": 140},
        ]
    else:
        return [
            {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 250},
            # {"label": "Territory", "fieldname": "territory", "fieldtype": "Data", "width": 150},
            # {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
            {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220},
            {"label": "Min Amount", "fieldname": "min_amt", "fieldtype": "Float", "width": 150, "precision": 2},
            {"label": "Max Amount", "fieldname": "max_amt", "fieldtype": "Float", "width": 150, "precision": 2},
            {"label": "Total Amount", "fieldname": "total_value", "fieldtype": "Float", "width": 120, "precision": 2},
            {"label": "Prize", "fieldname": "prizes", "fieldtype": "Data", "width": 140},
            {"label": "Gift", "fieldname": "gift", "fieldtype": "Data", "width": 140},
        ]

def get_area_wise_scheme_data(filters):
    scheme_name = filters.get("scheme_name")
    scheme_doc = frappe.get_doc("Scheme", scheme_name)

    effective_from = filters.get("effective_from")
    effective_to = filters.get("effective_to")

    scheme_based_on = scheme_doc.scheme_based_on
    applicable_for_all_areas = scheme_doc.get("applicable_for_all_areas")
    allowed_territories = None
    if not applicable_for_all_areas:
        allowed_territories = [r.territory for r in scheme_doc.get("applicable_for_areas") if r.territory]

    conditions = ["si.docstatus = 1"]
    params = {"effective_from": effective_from, "effective_to": effective_to}
    if effective_from:
        conditions.append("si.posting_date >= %(effective_from)s")
    if effective_to:
        conditions.append("si.posting_date <= %(effective_to)s")
    if allowed_territories:
        conditions.append("c.territory IN %(allowed_territories)s")
        params["allowed_territories"] = tuple(allowed_territories)

    if scheme_based_on == "Quantity":
        # Fetch scheme product targets
        product_rules = frappe.get_all(
            "Scheme Product Items",
            filters={"parent": scheme_name},
            fields=["product", "target_qty", "prizes_gift", "gift"]
        )
        rule_map = {r.product: r for r in product_rules if r.product}

        product_filter = ""
        if rule_map:
            product_filter = "AND sii.item_code IN %(product_codes)s"
            params["product_codes"] = tuple(rule_map.keys())

        query = f"""
            SELECT
                si.customer,
                c.territory,
                sii.item_code,
                SUM(sii.qty) AS total_value
            FROM `tabSales Invoice` si
            JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            LEFT JOIN `tabCustomer` c ON c.name = si.customer
            WHERE {" AND ".join(conditions)} {product_filter}
            GROUP BY si.customer, c.territory, sii.item_code
        """
        results = frappe.db.sql(query, params, as_dict=True)
        data = []
        for row in results:
            rule = rule_map.get(row.item_code)
            if not rule:
                continue
            if row.total_value >= (rule.target_qty or 0):
                row.update({
                    "target_qty": rule.target_qty,
                    "prizes": rule.prizes_gift,
                    "gift": rule.gift
                })
                data.append(row)
        return data

    else:  # Amount-based
        amount_rules = frappe.get_all(
            "Scheme Amount Items",
            filters={"parent": scheme_name},
            fields=["min_amt", "max_amt", "prizes", "gift"]
        )
        min_amt = min((r.min_amt for r in amount_rules if r.min_amt), default=0)
        max_amt = max((r.max_amt for r in amount_rules if r.max_amt), default=0)

        query = f"""
            SELECT
                si.customer,
                c.territory,
                sii.item_code,
                sii.item_name,
                SUM(sii.amount) AS total_value
            FROM `tabSales Invoice` si
            JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            LEFT JOIN `tabCustomer` c ON c.name = si.customer
            WHERE {" AND ".join(conditions)}
            GROUP BY si.customer, c.territory, sii.item_code, sii.item_name
        """
        results = frappe.db.sql(query, params, as_dict=True)
        data = []
        for row in results:
            row.update({
                "min_amt": min_amt,
                "max_amt": max_amt,
                "prizes": "❌ Not Applicable",
                "gift": "❌ Not Applicable"
            })
            for r in amount_rules:
                if (r.min_amt or 0) <= row.total_value <= (r.max_amt or 0):
                    row.update({
                        "prizes": r.prizes,
                        "gift": r.gift
                    })
                    break
            data.append(row)
        return data



def get_data(filters):
    scheme_name = filters.get("scheme_name")
    scheme_doc = frappe.get_doc("Scheme", scheme_name)
    scheme_based_on = scheme_doc.scheme_based_on
    based_on_area = scheme_doc.get("based_on_area")

    effective_from = filters.get("effective_from")
    effective_to = filters.get("effective_to")

    if scheme_based_on == "Quantity":
        rules = frappe.get_all("Scheme Product Items", filters={"parent": scheme_name}, fields=["product", "target_qty", "prizes_gift", "gift"])

        applicable_products = None if scheme_doc.get("applicable_for_all_products") else {
            r.item for r in scheme_doc.get("applicable_for_products") if r.item
        }

        product_map = {
            r.product: r
            for r in rules
            if r.product and (not applicable_products or r.product in applicable_products)
        }

        allowed_customers = None if scheme_doc.get("applicable_for_all_retailers") else [
            r.customer for r in scheme_doc.get("applicable_for_retailer") if r.customer
        ]

        conditions = ["si.docstatus = 1"]
        params = {"effective_from": effective_from, "effective_to": effective_to}

        if effective_from:
            conditions.append("si.posting_date >= %(effective_from)s")
        if effective_to:
            conditions.append("si.posting_date <= %(effective_to)s")
        if allowed_customers:
            conditions.append("si.customer IN %(allowed_customers)s")
            params["allowed_customers"] = tuple(allowed_customers)
        if applicable_products:
            conditions.append("sii.item_code IN %(applicable_products)s")
            params["applicable_products"] = tuple(applicable_products)

        if based_on_area:
            query = f"""
                SELECT 
                    c.territory, t.territory_name, sii.item_code, SUM(sii.qty) AS total_value
                FROM `tabSales Invoice` si
                JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
                LEFT JOIN `tabCustomer` c ON si.customer = c.name
                LEFT JOIN `tabTerritory` t ON c.territory = t.name
                WHERE {" AND ".join(conditions)}
                GROUP BY c.territory, t.territory_name, sii.item_code
            """
            results = frappe.db.sql(query, params, as_dict=True)
            data = []
            for row in results:
                item_code = row.item_code
                rule = product_map.get(item_code)
                if rule and row.total_value >= (rule.target_qty or 0):
                    row.update({
                        "territory": row.territory_name,
                        "target_qty": rule.target_qty,
                        "prizes": rule.prizes_gift,
                        "gift": rule.gift
                    })
                    data.append(row)
            return data
        else:
            query = f"""
                SELECT 
                    si.customer, c.territory, sii.item_code, SUM(sii.qty) AS total_value
                FROM `tabSales Invoice` si
                JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
                LEFT JOIN `tabCustomer` c ON si.customer = c.name
                WHERE {" AND ".join(conditions)}
                GROUP BY si.customer, c.territory, sii.item_code
            """
            results = frappe.db.sql(query, params, as_dict=True)
            data = []
            for row in results:
                item_code = row.item_code
                rule = product_map.get(item_code)
                if rule and row.total_value >= (rule.target_qty or 0):
                    row.update({
                        "target_qty": rule.target_qty,
                        "prizes": rule.prizes_gift,
                        "gift": rule.gift
                    })
                    data.append(row)
            return data

    else:
        rules = frappe.get_all("Scheme Amount Items", filters={"parent": scheme_name}, fields=["min_amt", "max_amt", "prizes", "gift"])
        overall_min_amt = min((r.min_amt for r in rules if r.min_amt), default=0)
        overall_max_amt = max((r.max_amt for r in rules if r.max_amt), default=0)

        allowed_customers = None if scheme_doc.get("applicable_for_all_retailers") else [
            r.customer for r in scheme_doc.get("applicable_for_retailer") if r.customer
        ]

        allowed_items = None if scheme_doc.get("applicable_for_all_products") else [
            r.item for r in scheme_doc.get("applicable_for_products") if r.item
        ]

        conditions = ["si.docstatus = 1"]
        params = {"effective_from": effective_from, "effective_to": effective_to}

        if effective_from:
            conditions.append("si.posting_date >= %(effective_from)s")
        if effective_to:
            conditions.append("si.posting_date <= %(effective_to)s")
        if allowed_customers:
            conditions.append("si.customer IN %(allowed_customers)s")
            params["allowed_customers"] = tuple(allowed_customers)
        if allowed_items:
            conditions.append("sii.item_code IN %(allowed_items)s")
            params["allowed_items"] = tuple(allowed_items)

        if based_on_area:
            # ✅ Add area restriction
            allowed_territories = None
            if not scheme_doc.get("applicable_for_all_areas"):
                allowed_territories = [
                    r.territory for r in scheme_doc.get("applicable_for_areas") if r.territory
                ]
                if allowed_territories:
                    conditions.append("c.territory IN %(allowed_territories)s")
                    params["allowed_territories"] = tuple(allowed_territories)

            query = f"""
                SELECT 
                    c.territory, t.territory_name, sii.item_code, sii.item_name, SUM(sii.amount) AS total_value
                FROM `tabSales Invoice` si
                JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
                LEFT JOIN `tabCustomer` c ON si.customer = c.name
                LEFT JOIN `tabTerritory` t ON c.territory = t.name
                WHERE {" AND ".join(conditions)}
                GROUP BY c.territory, t.territory_name, sii.item_code, sii.item_name
            """
            results = frappe.db.sql(query, params, as_dict=True)
            data = []
            for row in results:
                amount = float(row.total_value or 0)
                row.update({
                    "territory": row.territory_name,
                    "min_amt": overall_min_amt,
                    "max_amt": overall_max_amt,
                    "prizes": "❌ Not Applicable",
                    "gift": "❌ Not Applicable"
                })
                for rule in rules:
                    if (rule.min_amt or 0) <= amount <= (rule.max_amt or 0):
                        row.update({
                            "prizes": rule.prizes,
                            "gift": rule.gift
                        })
                        break
                data.append(row)
            return data
        else:
            query = f"""
                SELECT 
                    si.customer, c.territory, sii.item_code, sii.item_name, SUM(sii.amount) AS total_value
                FROM `tabSales Invoice` si
                JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
                LEFT JOIN `tabCustomer` c ON si.customer = c.name
                WHERE {" AND ".join(conditions)}
                GROUP BY si.customer, c.territory, sii.item_code, sii.item_name
            """
            results = frappe.db.sql(query, params, as_dict=True)
            data = []
            for row in results:
                amount = float(row.total_value or 0)
                row.update({
                    "min_amt": overall_min_amt,
                    "max_amt": overall_max_amt,
                    "prizes": "❌ Not Applicable",
                    "gift": "❌ Not Applicable"
                })
                for rule in rules:
                    if (rule.min_amt or 0) <= amount <= (rule.max_amt or 0):
                        row.update({
                            "prizes": rule.prizes,
                            "gift": rule.gift
                        })
                        break
                data.append(row)
            return data

  