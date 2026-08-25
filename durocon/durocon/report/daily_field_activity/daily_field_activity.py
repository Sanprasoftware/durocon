# Copyright (c) 2026
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, add_days


def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Employee",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": "Date",
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": "Day Status",
            "fieldname": "day_status",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": "Tour(Route)",
            "fieldname": "tour_route",
            "fieldtype": "Data",
            "width": 300
        },
        {
            "label": "Total KM",
            "fieldname": "total_km",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "Total No Of Visits",
            "fieldname": "total_visit",
            "fieldtype": "Int",
            "width": 140
        },
        {
            "label": "Total No Of Leads",
            "fieldname": "total_lead",
            "fieldtype": "Int",
            "width": 140
        }
    ]


def get_data(filters):
    data = []

    if not filters.get("from_date") or not filters.get("to_date"):
        return data

    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))

    employee_filters = {"status": "Active"}

    if filters.get("employee"):
        employee_filters["name"] = filters.get("employee")

    employees = frappe.get_all(
        "Employee",
        filters=employee_filters,
        fields=[
            "name",
            "employee_name",
            "user_id",
            "holiday_list"
        ],
        order_by="employee_name"
    )

    for emp in employees:

        # -------------------------
        # Holiday Dates
        # -------------------------
        holiday_dates = set()

        if emp.holiday_list:
            holidays = frappe.get_all(
                "Holiday",
                filters={
                    "parent": emp.holiday_list
                },
                fields=["holiday_date"]
            )

            holiday_dates = {
                getdate(d.holiday_date)
                for d in holidays
                if d.holiday_date
            }

        # -------------------------
        # Leave Dates
        # -------------------------
        leave_dates = set()
        half_day_dates = set()

        leave_applications = frappe.get_all(
            "Leave Application",
            filters={
                "employee": emp.name,
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

            # Half Day Leave
            if leave.half_day and leave.half_day_date:
                half_day_dates.add(getdate(leave.half_day_date))

            leave_date = getdate(leave.from_date)

            while leave_date <= getdate(leave.to_date):

                # Skip half-day date from full leave dates
                if not (
                    leave.half_day
                    and leave.half_day_date
                    and leave_date == getdate(leave.half_day_date)
                ):
                    leave_dates.add(leave_date)

                leave_date = add_days(leave_date, 1)

        # -------------------------
        # Date Loop
        # -------------------------
        current_date = from_date

        while current_date <= to_date:

            # Status Priority:
            # 1. Half Day
            # 2. On Leave
            # 3. W/O
            # 4. Holiday
            # 5. Blank

            is_half_day = current_date in half_day_dates
            is_on_leave = current_date in leave_dates
            is_sunday = current_date.weekday() == 6
            is_holiday = current_date in holiday_dates

            if is_half_day:
                day_status = "Half Day"
            elif is_on_leave:
                day_status = "On Leave"
            elif is_sunday:
                day_status = "W/O"
            elif is_holiday:
                day_status = "Holiday"
            else:
                day_status = ""

            # -------------------------
            # Tour Route
            # -------------------------
            tours = frappe.get_all(
                "Tours",
                filters={
                    "emplyoee": emp.name,
                    "date": current_date
                },
                fields=["description"]
            )

            tour_route = ", ".join(
                [row.description for row in tours if row.description]
            )

            # -------------------------
            # Total KM
            # -------------------------
            total_km = frappe.db.sql(
                """
                SELECT IFNULL(SUM(distance), 0)
                FROM `tabEmployee Location`
                WHERE user = %s
                AND DATE(creation) = %s
                """,
                (emp.user_id, current_date)
            )[0][0] or 0

            # -------------------------
            # Total Visits
            # -------------------------
            total_visit = 0

            if frappe.db.exists("DocType", "Visit"):
                try:
                    total_visit = frappe.db.count(
                        "Visit",
                        {
                            "employee": emp.name,
                            "date": current_date
                        }
                    )
                except Exception:
                    total_visit = 0

            # -------------------------
            # Total Leads
            # -------------------------
            total_lead = frappe.db.sql(
                """
                SELECT COUNT(name)
                FROM `tabLead`
                WHERE lead_owner = %s
                AND DATE(creation) = %s
                """,
                (emp.user_id, current_date)
            )[0][0] or 0

            data.append({
                "employee_name": emp.employee_name,
                "date": current_date,
                "day_status": day_status,
                "tour_route": tour_route,
                "total_km": total_km,
                "total_visit": total_visit,
                "total_lead": total_lead
            })

            current_date = add_days(current_date, 1)

    return data