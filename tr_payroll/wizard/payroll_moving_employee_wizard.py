from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollMovingEmployeeWizard(models.TransientModel):
    _name ='payroll.moving.employee.wizard'
    _description = 'Payroll Moving Employee Wizard'

    from_employee = fields.Many2one('payroll.employees', string='From Employee', required=True)
    to_employee = fields.Many2one('payroll.employees', string='To Employee', required=True)

    def submit(self):
        """
        Submit"""
        self.ensure_one()

        if not self.from_employee or not self.to_employee:
            raise UserError('Please select both employees.')

        if self.from_employee == self.to_employee:
            raise UserError('From and To Employees cannot be the same.')

        try:
            self._update_employee_data(self.from_employee.id, self.to_employee.id)
            self._remove_old_employee(self.from_employee.id)

            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            
        except Exception as e:
            raise UserError(f'Error while moving employee data: {str(e)}')

    def _update_employee_data(self, from_emp_id, to_emp_id):
        queries = [
            "UPDATE payroll_attendance_log SET employee_id = %s WHERE employee_id = %s",
            "UPDATE payroll_mistake_entries_details SET employee_id = %s WHERE employee_id = %s",
            "UPDATE payroll_payroll_summaries SET employee_id = %s WHERE employee_id = %s",
            "UPDATE payroll_shift_assign_details SET employee_id = %s WHERE employee_id = %s",
            "UPDATE payroll_salary_adjustment_detail SET employee_id = %s WHERE employee_id = %s",
            "UPDATE payroll_time_off_request SET created_by = %s WHERE created_by = %s",
            "UPDATE payroll_shift_assign_header SET assign_by_id = %s WHERE assign_by_id = %s",
            # "UPDATE payroll_emp_movement SET employee_id = %s WHERE employee_id = %s",
            "UPDATE payroll_employee_salary SET employee_id = %s WHERE employee_id = %s",
            "UPDATE payroll_approval_entries SET request_by_employee = %s WHERE request_by_employee = %s",
            "UPDATE payroll_approval_entries SET approved_by = %s WHERE approved_by = %s",
            "UPDATE payroll_employee_appraisals SET employee_assessed = %s WHERE employee_assessed = %s",
            "UPDATE payroll_time_off_request_approval SET approver = %s WHERE approver = %s",
        ]

        with self.env.cr.savepoint():
            for query in queries:
                self.env.cr.execute(query, (to_emp_id, from_emp_id))

            self._merge_employee_details(from_emp_id, to_emp_id)
            self._merge_employee_shifts(from_emp_id, to_emp_id)

            from_employee = self.env['payroll.employees'].browse(from_emp_id)
            to_employee = self.env['payroll.employees'].browse(to_emp_id)
            new_login = f"{from_employee.name.lower().replace(' ', '')}{to_employee.nik}-{to_employee.department_id.name}"

            if from_employee.user_id:
                self.env.cr.execute("""
                    DELETE FROM mail_activity WHERE user_id = %s
                """, (from_employee.user_id.id,))

                to_employee.user_id.write({
                    'login': new_login,
                    'name': new_login
                })
                to_employee.user_id = to_employee.user_id.id
                
            to_employee.write({
                'is_moving': True,
                'name': from_employee.name,
                'address': from_employee.address,
                'address_2': from_employee.address_2,
                'phone': from_employee.phone,
                'email': from_employee.email,
                'emergency_contact': from_employee.emergency_contact,
                'emergency_phone': from_employee.emergency_phone,
                'gender': from_employee.gender,
                'manager_id': from_employee.manager_id.id,
                'active_leave_date': from_employee.active_leave_date,
                'active_date': from_employee.active_date,
                'inactive_date': from_employee.inactive_date,
                'working_status': from_employee.working_status,
                'contract_id': from_employee.contract_id.id,
                'contract_start_date': from_employee.contract_start_date,
                'contract_end_date': from_employee.contract_end_date,
                'employee_status_id': from_employee.employee_status_id.id,
                'company_id': from_employee.company_id.id,
                'current_website': from_employee.current_website.id,
                'category_id': to_employee.category_id.id,
                'current_position': from_employee.current_position.id,
                'last_leave_date': from_employee.last_leave_date,
                'date_of_birth': from_employee.date_of_birth,
                'country_id': from_employee.country_id.id,
                'city_id': from_employee.city_id.id,
                'visa_number': from_employee.visa_number,
                'visa_expire_date': from_employee.visa_expire_date,
                'passport_number': from_employee.passport_number,
                'passport_expire_date': from_employee.passport_expire_date,
                'case_of_inactivity': from_employee.case_of_inactivity,
                'bank_id': from_employee.bank_id.id,
                'bank_account_number': from_employee.bank_account_number,
                'username': new_login
                # 'user_id': from_employee.user_id.id,
                # 'emp_salary_ids': [(0, 0, {
                #     'salary_component_id': salary.salary_component_id.id,
                #     'amount': salary.amount,
                #     'currency_id': salary.currency_id.id,
                #     'recurring': salary.recurring,
                #     'minimum_working_duration': salary.minimum_working_duration,
                #     'meal_type': salary.meal_type,
                #     'pro_rate': salary.pro_rate,
                #     'is_basic_salary': salary.is_basic_salary,
                #     'condition': salary.condition,
                #     'last_increment_salary_date': salary.last_increment_salary_date,
                #     'last_increment_salary_amount': salary.last_increment_salary_amount,
                #     'employee_id': to_emp_id,
                # }) for salary in from_employee.emp_salary_ids],
                # 'emp_shift_ids': [(0, 0, {
                #     'shifts_id': shift.shifts_id.id,
                #     'start_date': shift.start_date,
                #     'end_date': shift.end_date,
                #     'employee_id': to_emp_id,
                #     'companies_id': shift.companies_id.id,
                #     'website_id': shift.website_id.id,
                #     'is_night_diff': shift.is_night_diff,
                #     'shift_assign_id': shift.shift_assign_id,
                # }) for shift in from_employee.emp_shift_ids],
                # 'emp_deduction_ids': [(0, 0, {
                #     'deduction_id': deduction.deduction_id.id,
                #     'amount': deduction.amount,
                #     'currency_id': deduction.currency_id.id,
                #     'employee_id': to_emp_id,
                # }) for deduction in from_employee.emp_deduction_ids]
            })

        to_employee.write({
            'is_moving': False,
        })

    def _merge_employee_details(self, from_emp_id, to_emp_id):
        from_employee_details = self.env['payroll.employee.details'].search([('employee_id', '=', from_emp_id)])
        for detail in from_employee_details:
            existing_detail = self.env['payroll.employee.details'].search([
                ('employee_id', '=', to_emp_id),
                ('date', '=', detail.date),
                ('type', '=', detail.type),
                ('type_id', '=', detail.type_id)
            ], limit=1)
            if not existing_detail:
                detail.write({'employee_id': to_emp_id})
            else:
                detail.unlink()

    def _merge_employee_shifts(self, from_emp_id, to_emp_id):
        from_employee_shifts = self.env['payroll.employee.shift'].search([('employee_id', '=', from_emp_id)])
        for shift in from_employee_shifts:
            existing_shift = self.env['payroll.employee.shift'].search([
                ('employee_id', '=', to_emp_id),
                # ('shifts_id', '=', shift.shifts_id.id)
                ('start_date', '=', shift.start_date)
            ])
            if not existing_shift:
                shift.write({'employee_id': to_emp_id})
            else:
                shift.unlink()

    def _remove_old_employee(self, from_emp_id):
        queries = [
            "DELETE FROM payroll_attendance_log WHERE employee_id = %s",
            "DELETE FROM payroll_mistake_entries_details WHERE employee_id = %s",
            "DELETE FROM payroll_payroll_summaries WHERE employee_id = %s",
            "DELETE FROM payroll_shift_assign_details WHERE employee_id = %s",
            "DELETE FROM payroll_salary_adjustment_detail WHERE employee_id = %s",
            "DELETE FROM payroll_time_off_request WHERE created_by = %s",
            "DELETE FROM payroll_shift_assign_header WHERE assign_by_id = %s",
            # "DELETE FROM payroll_emp_movement WHERE employee_id = %s",
            "DELETE FROM payroll_employee_salary WHERE employee_id = %s",
            "DELETE FROM payroll_approval_entries WHERE request_by_employee = %s",
            "DELETE FROM payroll_approval_entries WHERE approved_by = %s",
            "DELETE FROM payroll_employee_appraisals WHERE employee_assessed = %s",
            "DELETE FROM payroll_time_off_request_approval WHERE approver = %s",
        ]

        with self.env.cr.savepoint():
            for query in queries:
                self.env.cr.execute(query, (from_emp_id,))

        from_employee = self.env['payroll.employees'].browse(from_emp_id)
        from_employee.unlink()
        return True