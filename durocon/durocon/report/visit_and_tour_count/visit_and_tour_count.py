# import frappe
# from frappe.utils import get_first_day, get_last_day, add_days

# def execute(filters=None):
#     if not filters:
#         filters = {}
        
#     columns = get_columns()
#     data = get_data(filters)
#     return columns, data

# def get_columns():
#     return [
#         {"label": "Employee ID", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 250},
#         {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
#         {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
#         {"label": "Visit Count", "fieldname": "visit_count", "fieldtype": "Int", "width": 120},
#         {"label": "Tour Count", "fieldname": "tour_count", "fieldtype": "Int", "width": 120},
#         # {"label": "Day", "fieldname": "day", "fieldtype": "Int", "width": 80}
#         {"label": "Total Visit", "fieldname": "total_visit", "fieldtype": "Int", "width": 120},
        
#     ]

# def get_data(filters):
#     from_date = filters.get("from_date")
#     to_date = filters.get("to_date")
#     employee_filter = filters.get("employee")  # get the employee filter

#     if not from_date or not to_date:
#         frappe.throw("Please set From Date and To Date")

#     # Find employees who have at least one Visit or Tour in the date range
#     visit_employees = frappe.get_all(
#         "Visit",
#         filters={"date": ["between", [from_date, to_date]], "docstatus": ["<", 2]},
#         fields=["employee"]
#     )
#     tour_employees = frappe.get_all(
#         "Tours",
#         filters={"date": ["between", [from_date, to_date]], "docstatus": ["<", 2]},
#         fields=["emplyoee"]  # keep the typo as it exists in the doctype
#     )

#     # Combine employee ids
#     employee_ids = list({e.employee for e in visit_employees} | {e.emplyoee for e in tour_employees})

#     # Apply employee filter if selected
#     if employee_filter:
#         employee_ids = [emp for emp in employee_ids if emp == employee_filter]

#     if not employee_ids:
#         return []

#     employees = frappe.get_all(
#         "Employee",
#         filters={"name": ["in", employee_ids]},
#         fields=["name", "employee_name"]
#     )

#     # Generate date list
#     dates = []
#     current = get_first_day(from_date)
#     last = get_last_day(to_date)
#     while current <= last:
#         dates.append(current)
#         current = add_days(current, 1)

#     data = []

#     for emp in employees:
#         for date in dates:
#             visit_count = frappe.db.count(
#                 "Visit",
#                 filters={"employee": emp.name, "date": date, "docstatus": ["<", 2]}
#             )
#             tour_count = frappe.db.count(
#                 "Tours",
#                 filters={"emplyoee": emp.name, "date": date, "docstatus": ["<", 2]}  # keep typo
#             )
#             data.append({
#                 "employee": emp.name,
#                 "employee_name": emp.employee_name,
#                 "date": date,
#                 "visit_count": visit_count,
#                 "tour_count": tour_count,
#                 "day": date.day
#             })
        
#         # Add blank row after each employee's month data
#         data.append({
#             "employee": "",
#             "employee_name": "",
#             "date": "",
#             "visit_count": "",
#             "tour_count": "",
#             "day": ""
#         })

#     return data



import frappe
from frappe.utils import get_first_day, get_last_day, add_days

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Employee ID", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 250},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
        {"label": "Visit Count", "fieldname": "visit_count", "fieldtype": "Int", "width": 120},
        # {"label": "Tour Count", "fieldname": "tour_count", "fieldtype": "Int", "width": 120},
        {"label": "Tour Total Calls", "fieldname": "tour_total_calls", "fieldtype": "Int", "width": 150},
        {"label": "Pending Visit", "fieldname": "total_visit", "fieldtype": "Int", "width": 120},
    ]


def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    employee_filter = filters.get("employee")

    if not from_date or not to_date:
        frappe.throw("Please set From Date and To Date")

    # Employees having Visit
    visit_employees = frappe.get_all(
        "Visit",
        filters={
            "date": ["between", [from_date, to_date]],
            "docstatus": ["<", 2]
        },
        fields=["employee"]
    )

    # Employees having Tours (keep typo)
    tour_employees = frappe.get_all(
        "Tours",
        filters={
            "date": ["between", [from_date, to_date]],
            "docstatus": ["<", 2]
        },
        fields=["emplyoee"]
    )

    employee_ids = list(
        {e.employee for e in visit_employees} |
        {e.emplyoee for e in tour_employees}
    )

    if employee_filter:
        employee_ids = [emp for emp in employee_ids if emp == employee_filter]

    if not employee_ids:
        return []

    employees = frappe.get_all(
        "Employee",
        filters={"name": ["in", employee_ids]},
        fields=["name", "employee_name"]
    )

    # Generate date range (month-wise)
    dates = []
    current = get_first_day(from_date)
    last = get_last_day(to_date)

    while current <= last:
        dates.append(current)
        current = add_days(current, 1)

    data = []

    for emp in employees:
        for date in dates:

            visit_count = frappe.db.count(
                "Visit",
                filters={
                    "employee": emp.name,
                    "date": date,
                    "docstatus": ["<", 2]
                }
            )

            tour_count = frappe.db.count(
                "Tours",
                filters={
                    "emplyoee": emp.name,
                    "date": date,
                    "docstatus": ["<", 2]
                }
            )

            # ✅ Sum of total_calls from Tours
            tour_total_calls = frappe.db.sql("""
                SELECT SUM(total_calls)
                FROM `tabTours`
                WHERE emplyoee = %s
                  AND date = %s
                  AND docstatus < 2
            """, (emp.name, date))[0][0] or 0

            total_pending_visit = tour_total_calls - visit_count

            data.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "date": date,
                "visit_count": visit_count,
                "tour_count": tour_count,
                "tour_total_calls": tour_total_calls,
                "total_visit": total_pending_visit if total_pending_visit > 0 else 0
            })

        # Blank row after each employee
        data.append({
            "employee": "",
            "employee_name": "",
            "date": "",
            "visit_count": "",
            "tour_count": "",
            "tour_total_calls": "",
            "total_visit": ""
        })

    return data
