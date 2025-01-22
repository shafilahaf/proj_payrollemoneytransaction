from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
import logging
from datetime import datetime
from datetime import date

_logger = logging.getLogger(__name__)
class PayrollCalculateBenefitLeavesWizard(models.TransientModel):
    _name = 'payroll.calculate.benefit.leaves.wizard'
    _description = 'Payroll Calculate Benefit Leaves Wizard'

    calculate_until_date = fields.Date(string='Calculate Until Date', required=True)
    employee = fields.Many2one('payroll.employees', string='Employee')

    def calculate_benefit_leaves(self):
        if self.calculate_until_date:
            # employees = self.env['payroll.employees'].search([
            #     ('id', '=', self.employee.id)
            # ])
            if self.employee:
                employees = self.env['payroll.employees'].search([('id', '=', self.employee.id)])
            else:
                employees = self.env['payroll.employees'].search([])

            calcdate = self.calculate_until_date

            domain_emp_dateil = [
                ('date', '>', calcdate)
            ]
            if self.employee:
                domain_emp_dateil.append(('employee_id','=',self.employee.id))

            emp_detail = self.env['payroll.employee.details'].search(domain_emp_dateil)

            unique_dates = []
            for detail in emp_detail:
                if detail.date not in unique_dates:
                    unique_dates.append(detail.date)

            # total_emp = self.fnCalcultateEmployeeDetail(calcdate, employees.id)
            total_emp = 0
            for employee in employees:
                total_emp += self.fnCalcultateEmployeeDetail(calcdate, employee.id)

            total_emp2 = 0
            for unique_date in sorted(unique_dates):
                # total_emp2 += self.fnCalcultateEmployeeDetail(unique_date, employees.id)
                for employee in employees:
                    total_emp2 += self.fnCalcultateEmployeeDetail(unique_date, employee.id)


            message = f"Calculate Benefit and Leaves : {total_emp + total_emp2} employees have been calculated"
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Calculation Complete',
                    'message': message,
                    'sticky': False,
            }
        }

    def fnCalcultateEmployeeDetail(self, calcdate, employee_id):
        _logger.info('Check parameter: %s and %s' % (calcdate, employee_id))
        # Check expired date
        # emp_details = self.env['payroll.employee.details'].search([
        #     ('isActive', '=', True),
        #     ('employee_id', '=', employee_id) if employee_id else ('employee_id', '!=', False)
        # ])

        domain_emp_det = [
            ('isActive', '=', True),
        ]
        if employee_id:
            domain_emp_det.append(('employee_id', '=', employee_id))

        emp_details = self.env['payroll.employee.details'].search(domain_emp_det)
        
        for detail in emp_details:
            if isinstance(detail.expired_date, date):  # expired_date is a valid date
                if detail.type == 3:
                    if detail.expired_date <= calcdate - relativedelta(months=1) - relativedelta(days=1):
                        detail.isActive = False
                        detail.write({'isActive': False})
                else:
                    if detail.expired_date <= calcdate - relativedelta(days=1):
                        detail.isActive = False
                        detail.write({'isActive': False})
        
        # Delete emp detail yg lebih dari tgl calcdate
        emp_category = self.env['payroll.employee.categories'].search([
            ('salary_cut_off', '=', calcdate.day)
        ], limit=1)
        
        if emp_category:
            domain = [('date', '>=', calcdate)]
            
            if employee_id:
                domain.append(('employee_id', '=', employee_id))
            
            emp_details_to_delete = self.env['payroll.employee.details'].search(domain)
            
            for detail in emp_details_to_delete:
                detail.unlink()
        
        emp_count = 0
        # employees = self.env['payroll.employees'].search([
        #     ('working_status', '=', 1),
        #     ('active_date', '<=', calcdate),
        #     ('id', '=', employee_id) if employee_id else ('id', '!=', False)
        # ])

        domain_emp = [
            ('working_status', '=', 1),
            ('active_date', '<=', calcdate),
        ]
        if employee_id:
            domain_emp.append((('id', '=', employee_id)))
        employees = self.env['payroll.employees'].search(domain_emp)
        
        for emp in employees.with_progress(msg="Processing"):
            if calcdate.day == emp.category_id.salary_cut_off:
                emp_count += 1

                # Check benefit
                benefits = self.env['payroll.emp.cat.benefit'].search([
                    ('categories_id', '=', emp.category_id.id)
                ])
                
                for benefit in benefits:
                    create_data = False
                    active_date = False
                    expired_date = False
                    month_act = 12

                    last_emp_detail = self.env['payroll.employee.details'].search([
                        ('employee_id', '=', emp.id),
                        ('type_text', '=', benefit.benefit_id.name)
                    ], order='active_date desc', limit=1)

                    if not last_emp_detail:
                        create_data = True
                        if benefit.cut_off_year:
                            active_date = fields.Date.from_string('%s-01-01' % emp.active_date.year)
                            expired_date = fields.Date.from_string('%s-12-31' % emp.active_date.year)
                            # month_act = emp.active_date.month
                            month_act = 13 - emp.active_date.month
                        else:
                            active_date = emp.active_date + relativedelta(months=benefit.minimum_working_duration)
                            expired_date = emp.active_date + relativedelta(months=benefit.recurring_month)
                    else:
                        if benefit.recurring_month:
                            last_date = last_emp_detail.expired_date
                            if last_date is None:
                                raise UserError('Expired date is empty for employee: %s' % emp.id)
                            if last_date <= calcdate:
                                create_data = True
                                active_date = last_date
                                expired_date = last_date + relativedelta(months=benefit.recurring_month)

                    emp_detail_exists = self.env['payroll.employee.details'].search([
                        ('employee_id', '=', emp.id),
                        ('type_text', '=', benefit.benefit_id.name),
                        ('date', '=', calcdate)
                    ], limit=1)

                    if not emp_detail_exists and create_data:
                        if active_date <= calcdate:
                            try:
                                qty = benefit.limit_days * month_act / 12 if benefit.cut_off_year else benefit.limit_days
                                amount = benefit.amount * month_act / 12 if benefit.cut_off_year else benefit.amount


                                self.env['payroll.employee.details'].create({
                                    'type': benefit.benefit_id.type,
                                    'type_text': benefit.benefit_id.name,
                                    'calculation_date': calcdate,
                                    'active_date': active_date,
                                    'expired_date': expired_date,
                                    'quantity': qty,
                                    'currency': benefit.currency_id.id,
                                    'amount': amount,
                                    'isActive': True,
                                    'employee_id': emp.id,
                                    'date': calcdate
                                })
                            except Exception as e:
                                raise UserError('Error creating employee detail: %s' % str(e))

                # Check leave
                leaves = self.env['payroll.emp.cat.timeoff.setup'].search([
                    ('categories_id', '=', emp.category_id.id)
                ])
                
                for leave in leaves:

                    if leave.type is None:
                        _logger.warning('Leave type is None for leave: %s', leave)
                        continue

                    create_data_leave = False
                    # active_date = False
                    expired_date = False

                    last_emp_detail = self.env['payroll.employee.details'].search([
                        ('employee_id', '=', emp.id),
                        ('type', '=', leave.type)
                    ], order='active_date desc', limit=1)

                    if not last_emp_detail:
                        create_data_leave = True
                        if leave.type == "1":
                            if emp.active_leave_date and emp.active_leave_date != datetime.min:
                                active_date = emp.active_date + relativedelta(months=leave.minimum_working_duration) if leave.reccuring_month == 0 else emp.active_leave_date 
                            else:
                                active_date = emp.active_date + relativedelta(months=leave.minimum_working_duration)
                        else:
                            active_date = emp.active_date + relativedelta(months=leave.minimum_working_duration)

                        expired_date = active_date + relativedelta(months=leave.reccuring_month)
                        
                        if leave.type == "2":
                            expired_date = fields.Date.from_string('%s-%s-%s' % (calcdate.year, calcdate.month, emp.category_id.salary_cut_off))
                    else:
                        if leave.reccuring_month:
                            if last_emp_detail and isinstance(last_emp_detail.expired_date, (date, datetime)):
                                last_date = last_emp_detail.expired_date
                                if last_date is None:
                                    raise UserError('Expired date is empty for employee: %s' % emp.id)
                                if last_date <= calcdate:
                                    create_data_leave = True
                                    active_date = last_date
                                    expired_date = active_date + relativedelta(months=leave.reccuring_month)

                                    if leave.type == "2":
                                        expired_date = fields.Date.from_string('%s-%s-%s' % (expired_date.year, expired_date.month, emp.category_id.salary_cut_off))
                                    
                                    if leave.type == "1" and emp.last_leave_date and emp.last_leave_date > expired_date:
                                        active_date = emp.last_leave_date
                                        expired_date = active_date + relativedelta(months=leave.reccuring_month)
                                    
                                    emp_detail_check = self.env['payroll.employee.details'].search([
                                        ('employee_id', '=', emp.id),
                                        ('type_id', '=', leave.id),
                                        ('active_date', '=', active_date),
                                        ('expired_date', '=', expired_date)
                                    ], limit=1)

                                    if emp_detail_check:
                                        create_data_leave = False
                        elif leave.reccuring_month == 0 and leave.type == "1":
                            leave_text = 'Leave' if leave.type == "1" else 'Day Off'
                            empdet = self.env['payroll.employee.details'].search([
                                    ('employee_id', '=', emp.id),
                                    ('type_text', '=', leave_text),
                                ], limit=1)
                            if not empdet:
                                create_data_leave = True
                            else:
                                create_data_leave = False

                    if isinstance(active_date, date) and active_date <= calcdate and create_data_leave == True:
                        try:
                            if active_date == expired_date and leave.type == "1":
                                expired_date = expired_date + relativedelta(months=6)
                            leave_text = 'Leave' if leave.type == "1" else 'Day Off'
                            self.env['payroll.employee.details'].create({
                                'employee_id': emp.id,
                                'calculation_date': calcdate,
                                'type': leave.type,
                                'type_text': leave_text,
                                'active_date': active_date,
                                'expired_date': expired_date,
                                'quantity': leave.days_off,
                                'amount': 0,
                                'isActive': True,
                            })
                            total_days = leave.days_off
                            time_off_requests = self.env['payroll.time.off.request'].search([
                                ('created_by', '=', emp.user_id.id),
                                ('request_type', 'in', [1, 6]),
                                ('status', 'in', [False, 1, 2]),
                                ('request_date', '>=', active_date),
                                ('request_date', '<=', expired_date)
                            ])
                            
                            for tor in time_off_requests:
                                total_days -= tor.duration
                            attendance_logs = self.env['payroll.attendance.log'].search([
                                ('employee_id', '=', emp.id),
                                ('time_off_type', '=', 1),
                                ('date', '>=', active_date),
                                ('date', '<=', expired_date)
                            ])
                            
                            total_days -= len(attendance_logs)
                            if total_days <= 0:
                                self.env['payroll.employee.details'].write({
                                    'isActive': False,
                                })
                        except Exception as e:
                            raise UserError('Error creating leave detail: %s' % str(e))
        return emp_count 