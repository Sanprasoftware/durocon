import frappe
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from frappe.utils import flt
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip as HRMSSalarySlip


class CustomSalarySlip(HRMSSalarySlip):
	def get_working_days_details(self, lwp=None, for_preview=0):
		super().get_working_days_details(lwp=lwp, for_preview=for_preview)
		if for_preview:
			return

		extra_days = self._get_extra_working_days_from_holidays()
		if extra_days:
			self.total_working_days = flt(self.total_working_days) + extra_days
			self.payment_days = flt(self.payment_days) + extra_days

	def _get_extra_working_days_from_holidays(self) -> int:
		holiday_list = get_holiday_list_for_employee(self.employee)
		if not holiday_list:
			return 0

		holiday_dates = frappe.get_all(
			"Holiday",
			filters={
				"parent": holiday_list,
				"parenttype": "Holiday List",
				"holiday_date": ("between", [self.start_date, self.end_date]),
				"custom__add_hd_in_sp": 1,
			},
			pluck="holiday_date",
		)

		return len(set(holiday_dates))
