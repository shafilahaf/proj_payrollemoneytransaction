from odoo import models, fields, api # type: ignore
from odoo.exceptions import UserError, ValidationError # type: ignore
from datetime import timedelta
from dateutil.relativedelta import relativedelta # type: ignore
from datetime import datetime


class PayrollCalculateSalaryWizard(models.TransientModel):
    _name = 'payroll.calculate.salary.wizard'
    _description = 'Payroll Calculate Salary Wizard'

    calculate_date = fields.Date(string='Calculate Date')
    employee_ids = fields.Many2one('payroll.employees', string='Employee')
    category_ids = fields.Many2one('payroll.employee.categories', string='Category')
    department_ids = fields.Many2one('payroll.device.department', string='Department')

    def calculate_salary(self):
        """
        Func in C# :
        CalculateSalary DONE
        fnCalculateSalary DONE
        fnCalculateSalaryPH DONE
        """
        self.ensure_one()
        calc_date = self.calculate_date
        employee = self.employee_ids
        category = self.category_ids
        department = self.department_ids

        schsetup = self.env['payroll.scheduler.setup'].search([
            ('id', '=', 1)
        ], limit=1)
        if not schsetup:
            raise UserError('Please configure the scheduler setup first!')
        
        end_date = calc_date - timedelta(days=1)
        start_date = calc_date + relativedelta(months=-1)

        total_emp = 0
        domain = [
            ('blocked', '=', False),
            ('salary_cut_off', '=', calc_date.day), #calc_date.weekday()
            ('salary_cut_off_2', '=', 0),
        ]

        domain_ph = [
            ('blocked', '=', False),
            ('salary_cut_off', '=', calc_date.day),
            ('salary_cut_off_2', '!=', 0),
        ]

        domain_ph_2 = [
            ('blocked', '=', False),
            ('salary_cut_off_2', '=', calc_date.day),
        ]

        emp_cats = self.env['payroll.employee.categories'].search(domain)
        for category in emp_cats:
            employee_domain = [
                ('working_status', '=', '1'),
                ('category_id', '=', category.id),
            ]
            if self.employee_ids:
                employee_domain.append(('id', '=', self.employee_ids.id))
            if self.department_ids:
                employee_domain.append(('department_id', '=', self.department_ids.id))

            employees = self.env['payroll.employees'].search(employee_domain)
            for emp in employees.with_progress(msg="Processing"):
                if (calc_date.day == category.salary_cut_off): #calc_date.weekday()
                    if emp.active_date <= end_date:
                        self._fn_calculate_salary(emp, schsetup, start_date, end_date, True, category)
                        total_emp += 1

        emp_cats_ph = self.env['payroll.employee.categories'].search(domain_ph)
        for category in emp_cats_ph:
            employee_domain = [
                ('working_status', '=', '1'),
                ('category_id', '=', category.id),
            ]

            if self.employee_ids:
                employee_domain.append(('id', '=', self.employee_ids.id))

            if self.department_ids:
                employee_domain.append(('department_id', '=', self.department_ids.id))

            employees = self.env['payroll.employees'].search(employee_domain)
            for emp in employees.with_progress(msg="Processing"):
                if emp.active_date <= end_date:
                    start_date2 = datetime(start_date.year, start_date.month, category.salary_cut_off_2)
                    self._fn_calculate_salary_ph(emp, schsetup, start_date2, end_date, True, category, 1)
                    total_emp += 1
        
        emp_cats_ph_2 = self.env['payroll.employee.categories'].search(domain_ph_2)
        for category in emp_cats_ph_2:
            employee_domain = [
                ('working_status', '=', '1'),
                ('category_id', '=', category.id),
            ]

            if self.employee_ids:
                employee_domain.append(('id', '=', self.employee_ids.id))
            
            if self.department_ids:
                employee_domain.append(('department_id', '=', self.department_ids.id))

            employees = self.env['payroll.employees'].search(employee_domain)
            for emp in employees.with_progress(msg="Processing"):
                if emp.active_date <= end_date:
                    start_date2 = datetime(calc_date.year, calc_date.month, category.salary_cut_off)
                    self._fn_calculate_salary_ph(emp, schsetup, start_date2, end_date, True, category, 2)
                    total_emp += 1
        
        message = f'{total_emp} employee(s) salary has been calculated!'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Calculate Salary',
                'message': message,
                'sticky': False
            }
        }
    
    def _fn_calculate_salary(self, employee, schsetup, start_date, end_date, flag, category):
        """
        Func in C# :
        fnCalculateSalary DONE
        fnUpdatePayrollSummary DONE
        """
        enddate = end_date
        startdate = start_date

        year, month = enddate.year, enddate.month

        if category.salary_cut_off != 1:
            diff = 31 - category.salary_cut_off + 1
            if enddate.weekday() >= category.salary_cut_off:
                new_date = enddate + timedelta(days=diff)
                year, month = new_date.year, new_date.month
            else:
                year, month = enddate.year, enddate.month
        else:
            year, month = enddate.year, enddate.month
        
        totdays = (enddate - startdate).days + 1
        empdata = self.env['payroll.employees'].search([
            ('id', '=', employee.id)
        ], limit=1)

        paysum = self.env['payroll.payroll.summaries'].search([
            ('employee_id', '=', empdata.id),
            ('year', '=', year),
            ('month', '=', month),
        ])

        if paysum:
            paysum.unlink()

        # Create a new payroll summary record
        paysum = self.env['payroll.payroll.summaries'].create({
            'employee_id': empdata.id,
            'year': year,
            'month': month,
        })

        # Call the update function with the new record
        self._fn_update_payroll_summary(paysum.id, employee.id, startdate, enddate, schsetup, flag, empdata, totdays)
        
        # OLD
        # paysum = self.env['payroll.payroll.summaries'].search([
        #     ('employee_id', '=', empdata.id),
        #     ('year', '=', year),
        #     ('month', '=', month),
        # ])
        # if not paysum:
        #     paysum = self.env['payroll.payroll.summaries'].create({
        #         'employee_id': empdata.id,
        #         'year': year,
        #         'month': month,
        #     })
        #     self._fn_update_payroll_summary(paysum.id, employee.id, startdate, enddate, schsetup, flag, empdata, totdays)
        # else:
        #     payroll_detail = self.env['payroll.payroll.summary.detail'].search([
        #         ('payroll_summary_id', '=', paysum.id)
        #     ])
        #     for pd in payroll_detail:
        #         pd.unlink()

        #     self._fn_update_payroll_summary(paysum.id, employee.id, startdate, enddate, schsetup, flag, empdata, totdays)
        # OLD
       
    def _fn_update_payroll_summary(self, payroll_id, employee_id, start_date, end_date, schsetup, finished, empdata, totdays):
        """
        Func in C# :
        fnUpdatePayrollSummary DONE
        fnCalcabsensce DONE
        fnInsertPayrollDetailSalary DONE
        fnCalcReimburs DONE
        fnCalcTicketAmount DONE
        fnCalcLate DONE
        fnCallForgetCheckOut DONE
        fnCalcReward DONE
        fncalcmistake DONE
        fnInsertPayrollDetailDeduction DONE
        fnInsertPayrollDetailDeduction2 DONE
        fnCalcLeaveNotTaken DONE
        """
        paysum = self.env['payroll.payroll.summaries'].search([
            ('id', '=', payroll_id)
        ], limit=1)
        if paysum:
            abseninfo = self._fn_calc_absence(employee_id, start_date, end_date)
            empsaldata = self._fn_insert_payroll_detail_salary(paysum.id, empdata, totdays, start_date, end_date, int(abseninfo[1]), 0)

            paysum.currency_id = empsaldata[1]
            paysum.from_date = start_date
            paysum.to_date = end_date

            self._fn_calc_reimbursements(empdata, start_date, end_date, paysum.id)
            paysum.days_in = int(abseninfo[0])
            paysum.days_absent = int(abseninfo[1])
            paysum.days_leave = int(abseninfo[3])
            paysum.sick_permission = int(abseninfo[5])
            paysum.days_permission = int(abseninfo[6])
            paysum.days_off = int(abseninfo[8])
            paysum.total_work_days = int(abseninfo[9])

            if paysum.days_leave != 0:
                self._fn_calc_ticket_amount(paysum.id, empdata, start_date, end_date)

            lateinfo = self._fn_calc_late(employee_id, start_date, end_date)
            paysum.late = int(lateinfo[0])
            paysum.late2 = int(lateinfo[1])
            paysum.late3 = int(lateinfo[2])
            paysum.late4 = int(lateinfo[3])

            forgetcheckoutinfo = self._fn_calc_forget_checkout(employee_id, start_date, end_date)
            paysum.forget_checkout_count = int(forgetcheckoutinfo[0])

            if finished:
                self._fn_calc_reward(employee_id, start_date, end_date, paysum.id, int(paysum.late), int(paysum.forget_checkout_count), int(paysum.days_absent), int(paysum.days_permission), int(paysum.sick_permission))

            mistakeinfo = self._fn_calc_mistake(employee_id, start_date, end_date, paysum.id)
            paysum.mistake_1_count = int(mistakeinfo[0])
            paysum.mistake_2_count = int(mistakeinfo[2])

            deductcount = [0] * 10
            deductcount[1] = int(abseninfo[1])
            deductcount[2] = int(mistakeinfo[0])
            deductcount[3] = int(mistakeinfo[2])
            deductcount[4] = int(paysum.late)
            deductcount[5] = int(paysum.forget_checkout_count)
            deductcount[6] = int(paysum.days_permission)
            deductcount[7] = int(paysum.late2)
            deductcount[8] = int(paysum.late3)
            deductcount[9] = int(paysum.late4)

            # deductiondata = self._fn_insert_payroll_detail_deduction(paysum.id, empdata, int(paysum.total_work_days), deductcount)
            self._fn_insert_payroll_detail_deduction(paysum.id, empdata, int(paysum.total_work_days), deductcount)
            self._fn_insert_payroll_detail_deduction2(paysum.id, empdata, int(paysum.total_work_days), deductcount)
            self._fn_calc_leave_not_taken(paysum.id, empdata, start_date, end_date)

            paysum.finished = finished
            paysum.write({})
    
    def _fn_calc_absence(self, empid, startdate, enddate):
        absen = [0] * 11
        empdata = self.env['payroll.employees'].search([
            ('id', '=', empid)
        ], limit=1)
        ltotdays = (enddate - startdate).days + 1

        if empdata.active_date > startdate:
            ltotdays = (enddate - empdata.active_date).days + 1
        else:
            if (empdata.inactive_date != False) and (empdata.inactive_date <= enddate):
                enddate = empdata.inactive_date
                ltotdays = (enddate - startdate).days
            if (empdata.active_date > startdate) and (empdata.inactive_date != False) and (empdata.inactive_date <= enddate):
                startdate = empdata.active_date
                enddate = empdata.inactive_date
                ltotdays = (enddate - startdate).days

        if not empdata.category_id.without_attendance_logs:
            lattlog = self.env['payroll.attendance.log'].search([
                ('employee_id', '=', empid),
                ('date', '>=', startdate),
                ('date', '<=', enddate)
            ])
            if lattlog:
                totabsen = 0
                if len(lattlog) < ltotdays:
                    totabsen = ltotdays - len(lattlog)
                absen[0] = len(lattlog)
                absen[1] = totabsen
            else:
                tor = self.env['payroll.time.off.request'].search([
                    ('employee_id', '=', empid),
                    ('start_date', '>=', startdate),
                    ('end_date', '<=', enddate),
                    ('status', '=', '5'),
                    ('request_type', '=', '99')
                ])
                absen[0] = ltotdays - len(tor)
                absen[1] = len(tor)

            attlogleave = self.env['payroll.attendance.log'].search([
                ('employee_id', '=', empid),
                ('date', '>=', startdate),
                ('date', '<=', enddate),
                ('time_off_type', '=', '1')
            ])
            if attlogleave:
                absen[0] -= len(attlogleave)
                absen[3] = len(attlogleave)
            
            attlogsick = self.env['payroll.attendance.log'].search([
                ('employee_id', '=', empid),
                ('date', '>=', startdate),
                ('date', '<=', enddate),
                ('time_off_type', '=', '2')
            ])
            if attlogsick:
                absen[0] -= len(attlogsick)
                absen[5] = len(attlogsick)

            attlogpermission = self.env['payroll.attendance.log'].search([
                ('employee_id', '=', empid),
                ('date', '>=', startdate),
                ('date', '<=', enddate),
                ('time_off_type', '=', '3')
            ])
            if attlogpermission:
                absen[0] -= len(attlogpermission)
                absen[6] = len(attlogpermission)

            attlogdayoff = self.env['payroll.attendance.log'].search([
                ('employee_id', '=', empid),
                ('date', '>=', startdate),
                ('date', '<=', enddate),
                ('time_off_type', '=', '4')
            ])
            if attlogdayoff:
                absen[0] -= len(attlogdayoff)
                absen[8] = len(attlogdayoff)

            absen[9] = ltotdays

        return absen

    def _fn_insert_payroll_detail_salary(self, payroll_id, empdata, totdays, startdate, enddate, absencecount, periode):
        employeesalary = self.env['payroll.employee.salary']
        payroll_detail = self.env['payroll.payroll.summary.detail']

        empsal = self.env['payroll.employee.salary'].search([
            ('employee_id', '=', empdata.id),
            ('condition', '=', False)
        ])

        salamount = 0

        # Handling case where no salary record is found
        if not empsal:
            return [salamount, None]  # Return None or a default currency ID if needed

        totalday = totdays
        if empdata.active_date > startdate:
            totalday = (enddate - empdata.active_date).days + 1

        if empdata.active_date and empdata.inactive_date and empdata.inactive_date <= enddate:
            totalday = (empdata.inactive_date - startdate).days

        if empdata.active_date > startdate and empdata.inactive_date and empdata.inactive_date <= enddate:
            totalday = (empdata.inactive_date - empdata.active_date).days

        for empsalaries in empsal:
            # activedate = empdata.active_date + timedelta(days=(empsalaries.minimum_working_duration * 30))
            activedate = empdata.active_date + relativedelta(months=empsalaries.minimum_working_duration)
            if enddate >= activedate:
                gaji = empsalaries.amount

                if totalday != totdays:
                    gaji = empsalaries.amount * (totalday / totdays)

                if empsalaries.pro_rate:
                    totalday2 = totalday - absencecount
                    gaji = empsalaries.amount * (totalday2 / totdays)

                if empsalaries.condition == False:
                    salamount += gaji

                paydet = payroll_detail.search([
                    ('payroll_summary_id', '=', payroll_id),
                    ('type_id', '=', empsalaries.salary_component_id.id),
                    ('type', '=', 1)
                ], limit=1)

                if paydet:
                    paydet.write({
                        'name': empsalaries.salary_component_id.name,
                        'amount': empsalaries.amount,
                        'net_amount': gaji,
                        'currency_id': empsalaries.currency_id.id,
                        'condition': empsalaries.condition,
                        'days_count': totdays,
                    })
                else:
                    payroll_detail.create({
                        'payroll_summary_id': payroll_id,
                        'type_id': empsalaries.salary_component_id.id,
                        'type': 1,
                        'type_text': 'Salary',
                        'name': empsalaries.salary_component_id.name,
                        'amount': empsalaries.amount,
                        'net_amount': gaji,
                        'currency_id': empsalaries.currency_id.id,
                        'condition': empsalaries.condition,
                        'days_count': totdays,
                    })

        return [salamount, empsal[0].currency_id.id]

    def _fn_calc_reimbursements(self, empid, startdate, enddate, payroll_id):
        time_off_request = self.env['payroll.time.off.request']
        payroll_detail = self.env['payroll.payroll.summary.detail']
        employee_detail = self.env['payroll.employee.details']

        reimburs = time_off_request.search([
            ('request_type', '=', '2'),
            ('employee_id', '=', empid.id),
            ('status', '=', '5'),
            ('start_date', '>=', startdate - relativedelta(months=1)),
            ('start_date', '<=', enddate)
        ])

        ramount = 0
        for r in reimburs:
            if r.start_date + timedelta(days=30) <= enddate and r.reimburse_amount:
                ramount += r.reimburse_amount

        # Insert to payroll summary detail
        if ramount > 0:
            empdtl = employee_detail.search([
                ('type', '=', '3'),
                ('employee_id', '=', empid.id),
                ('isActive', '=', True),
            ], order='active_date desc', limit=1)

            if empdtl:
                paydet = payroll_detail.search([
                    ('payroll_summary_id', '=', payroll_id),
                    ('type_id', '=', empdtl.type_id),
                    ('type', '=', '3')
                ], limit=1)

                if paydet:
                    paydet.write({
                        'name': f'Reimbursement {empdtl.type_text}',
                        'amount': ramount,
                        'net_amount': ramount,
                        'currency_id': empdtl.currency,
                    })
                else:
                    payroll_detail.create({
                        'payroll_summary_id': payroll_id,
                        'type_id': empdtl.type_id,
                        'type': 3,
                        'type_text': 'Reimbursement',
                        'name': f'Reimbursement {empdtl.type_text}',
                        'amount': ramount,
                        'net_amount': ramount,
                        'currency_id': empdtl.currency.id,
                    })

    def _fn_calc_ticket_amount(self, payroll_id, empdata, start_date, end_date):
        ticket_amount = 0

        attlogleave = self.env['payroll.attendance.log'].search([
            ('employee_id', '=', empdata.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('time_off_type', '=', '1')
        ], order='date desc', limit=1)

        if attlogleave:
            # tor = self.env['payroll.time.off.request'].search([
            #     ('id', '=', attlogleave.source_id)
            # ], limit=1) #TODO: aku matiin karena ngga ada source_id (12/13/2024)
            user = self.env['res.users'].search([('payroll_employee_id','=',empdata.id)], limit=1)

            tor = self.env['payroll.time.off.request'].search([
                '|',
                ('employee_id', '=', empdata.id),
                ('start_date', '<=', attlogleave.date),
                ('end_date', '>=', attlogleave.date)
            ], limit=1)

            tor2 = self.env['payroll.time.off.request'].search([
                ('id', '=', attlogleave.source_id)
            ], limit=1)

            if (tor and tor.start_date >= start_date) or tor2:
                cat = self.env['payroll.emp.cat.timeoff.setup'].search([
                    ('categories_id', '=', empdata.category_id.id),
                    ('type', '=', '1')
                ], limit=1)
                if cat and cat.ticket_amount != 0:
                    # Insert or update payroll detail for ticket amount
                    paydet = self.env['payroll.payroll.summary.detail'].search([
                        ('payroll_summary_id', '=', payroll_id),
                        ('type_id', '=', False),
                        ('type', '=', '1')
                    ], limit=1)
                    if paydet:
                        paydet.write({
                            'amount': cat.ticket_amount,
                            'net_amount': cat.ticket_amount,
                        })
                    else:
                        self.env['payroll.payroll.summary.detail'].create({
                            'payroll_summary_id': payroll_id,
                            'type_id': False,
                            'type': 1,
                            'type_text': 'Ticket Amount',
                            'amount': cat.ticket_amount,
                            'net_amount': cat.ticket_amount,
                            'currency_id': cat.ticket_currency_id.id,
                            'condition': False,
                            'days_count': 0,
                            'name': "Ticket"
                        })

        return ticket_amount            

    def _fn_calc_late(self, empid, start_date, end_date):
        latedate = [0, 0, 0, 0]

        empdata = self.env['payroll.employees'].search([
            ('id', '=', empid)
        ], limit=1)

        attlog = self.env['payroll.attendance.log'].search([
            ('employee_id', '=', empid),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('is_latelog', '=', True),
            ('time_off_type', '=', False)
        ])

        if attlog:
            latedate[0] = len(attlog)

        attlog2 = self.env['payroll.attendance.log'].search([
            ('employee_id', '=', empid),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('is_late_2', '=', True),
            ('time_off_type', '=', False)
        ])

        if attlog2:
            latedate[1] = len(attlog2)

        attlog3 = self.env['payroll.attendance.log'].search([
            ('employee_id', '=', empid),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('is_late_3', '=', True),
            ('time_off_type', '=', False)
        ])

        if attlog3:
            latedate[2] = len(attlog3)

        attlog4 = self.env['payroll.attendance.log'].search([
            ('employee_id', '=', empid),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('is_late_4', '=', True),
            ('time_off_type', '=', False)
        ])

        if attlog4:
            latedate[3] = len(attlog4)

        return latedate
    
    def _fn_calc_forget_checkout(self, empid, start_date, end_date):
        forgetcheckoutdata = [0, 0]

        empdata = self.env['payroll.employees'].search([
            ('id', '=', empid)
        ], limit=1)

        attlog = self.env['payroll.attendance.log'].search([
            ('employee_id', '=', empid),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('working_hours', '=', 0),
            ('time_off_type', '=', False)
        ])

        if attlog:
            forgetcheckoutdata[0] = len(attlog)

        return forgetcheckoutdata
    
    def _fn_calc_reward(self, empid, start_date, end_date, payroll_id, late_count, forget_checkout_count, absence_count, permission_count, sick_count):
        ramount = 0

        empdata = self.env['payroll.employees'].search([
            ('id', '=', empid)
        ], limit=1)

        empsal = self.env['payroll.employee.salary'].search([
            ('employee_id', '=', empid),
            ('condition', '=', "1")
        ])

        if empsal:
            activedate = empdata.active_date + timedelta(days=(empsal.minimum_working_duration))
            if end_date >= activedate:
                # mistake_entreis_header = self.env['payroll.mistake.entries.header'].search([
                #     ('created_by', '=', empdata.user_id.id),
                #     ('date', '>=', start_date),
                #     ('date', '<=', end_date),
                # ])

                mistake_entries_detail = self.env['payroll.mistake.entries.details'].search([
                    ('header_id.date', '>=', start_date),
                    ('header_id.date', '<=', end_date),
                    ('mistake','in', ["2", "3"]),
                    ('employee_id', '=', empid)
                ])

                # if not mistake_entreis_header and not sum(mistake_entries_detail.mapped('amount')) and late_count == 0 and forget_checkout_count == 0 and absence_count == 0 and permission_count == 0:
                #     ramount += empsal.amount
                if not sum(mistake_entries_detail.mapped('amount')) and late_count == 0 and forget_checkout_count == 0 and absence_count == 0 and permission_count == 0 and sick_count == 0:
                    ramount += empsal.amount
        
        if ramount > 0:
            paydet = self.env['payroll.payroll.summary.detail'].search([
                ('payroll_summary_id', '=', payroll_id),
                ('type_id', '=', empsal.salary_component_id.id),
                ('type', '=', '4')
            ], limit=1)

            if paydet:
                paydet.write({
                    'name': empsal.salary_component_id.name,
                    'currency_id': empsal.currency_id.id,
                    'amount': ramount,
                    'net_amount': ramount,
                })
            else:
                self.env['payroll.payroll.summary.detail'].create({
                    'payroll_summary_id': payroll_id,
                    'type_id': empsal.salary_component_id.id,
                    'type': 4,
                    'type_text': 'Reward',
                    'name': empsal.salary_component_id.name,
                    'currency_id': empsal.currency_id.id,
                    'amount': ramount,
                    'net_amount': ramount,
                })
    
    def _fn_calc_mistake(self, empid, start_date, end_date, payroll_id):
        mistakinfo = [0, 0, 0, 0, 0]

        empdata = self.env['payroll.employees'].search([
            ('id', '=', empid)
        ], limit=1)

        # mistake_entreis_header = self.env['payroll.mistake.entries.header'].search([
        #     ('date', '>=', start_date),
        #     ('date', '<=', end_date),
        # ])

        cat_deduction = self.env['payroll.emp.cat.deduction'].search([
            ('deduction_id.source', 'in', ['2', '3']),
        ])

        # for cat in cat_deduction:
        #     mistake_entries_detail = self.env['payroll.mistake.entries.details'].search([
        #         ('header_id.date', '>=', start_date),
        #         ('header_id.date', '<=', end_date),
        #         ('mistake','=', cat.deduction_id.source),
        #         ('employee_id', '=', empid), 
        #         ('deduction_id', '=', cat.deduction_id.id)
        #     ])

        mistake_entries_detail = self.env['payroll.mistake.entries.details'].search([
            ('header_id.date', '>=', start_date),
            ('header_id.date', '<=', end_date),
            ('employee_id', '=', empid),
            ('mistake_detail.deduction_source', '=', '2'),
            ('header_id.status', '=', '2')
        ])

        mistakinfo[0] = len(mistake_entries_detail)

        if sum(m.amount for m in mistake_entries_detail) == 0:
            mistakinfo[0] = 0

        mistake_entries_detail2 = self.env['payroll.mistake.entries.details'].search([
            ('header_id.date', '>=', start_date),
            ('header_id.date', '<=', end_date),
            ('employee_id', '=', empid),
            ('mistake_detail.deduction_source', '=', '3'),
            ('header_id.status', '=', '2')
        ])

        mistakinfo[2] = len(mistake_entries_detail2)

        if sum(m.amount for m in mistake_entries_detail2) == 0:
            mistakinfo[2] = 0

        mistakedetail = []
        catdeduction = self.env['payroll.emp.cat.deduction'].search([
            ('categories_id', '=', empdata.category_id.id),
            ('deduction_id.source', 'in', ['2', '3']),
        ])

        for empdeduct in catdeduction:
            misentry = self.env['payroll.mistake.entries.details'].search([
                ('mistake', '=', empdeduct.deduction_id.source),
                ('employee_id', '=', empid),
                ('header_id.status', '=', '2'),
                ('header_id.date', '>=', start_date),
                ('header_id.date', '<=', end_date),
            ]) 
            for mentry in misentry:
                misdetail = next((md for md in mistakedetail if md['mistake'] == empdeduct.deduction_id.source and md['currency_id'] == mentry.currency_id.id), None)

                if not misdetail:
                    misdetail = {
                        'deduction_id': empdeduct.deduction_id.id,
                        'name': empdeduct.deduction_id.name,
                        'currency_id': mentry.currency_id.id,
                        'amount': mentry.amount,
                        'mistake': empdeduct.deduction_id.source
                    }
                    mistakedetail.append(misdetail)
                else:
                    misdetail['amount'] += mentry.amount

        for m in mistakedetail:
            paydet = self.env['payroll.payroll.summary.detail'].search([
                ('payroll_summary_id', '=', payroll_id),
                ('type_id', '=', m['deduction_id']),
                ('type', '=', '2')
            ], limit=1)

            if paydet:
                paydet.write({
                    'name': m['name'],
                    'currency_id': m['currency_id'],
                    'amount': m['amount'],
                    'net_amount': m['amount'],
                })
            else:
                self.env['payroll.payroll.summary.detail'].create({
                    'payroll_summary_id': payroll_id,
                    'type_id': m['deduction_id'],
                    'type': 2,
                    'type_text': 'Deduction',
                    'name': m['name'],
                    'currency_id': m['currency_id'],
                    'amount': m['amount'],
                    'net_amount': m['amount'] * -1,
                })

        return mistakinfo

    def _fn_insert_payroll_detail_deduction(self, payroll_id, empdata_id, total_days, deduct_days):
        """
        Func in C# :
        fnCalcDeduction DONE
        """
        empdata = self.env['payroll.employees'].search([
            ('id', '=', empdata_id.id)
        ], limit=1)

        total_deduct_amount = 0

        catdeductions = self.env['payroll.emp.cat.deduction'].search([
            ('categories_id', '=', empdata.category_id.id),
            ('deduction_id.source', 'not in', ['2', '3']),
        ])

        if catdeductions:
            for empdeduct in catdeductions:
                empcase = self.env['payroll.employee.deduction'].search([
                    ('employee_id', '=', empdata.id),
                    ('deduction_id', '=', empdeduct.deduction_id.id),
                ], limit=1)

                deduct_amount = empcase.amount if empcase else empdeduct.amount

                # Calculate deduction data
                deduct_data = self._fn_calc_deduction(
                    empdeduct.deduction_id.source,
                    total_days,
                    deduct_days,
                    empdeduct.deduction_id.pro_rate,
                    deduct_amount,
                    empdeduct.amount_from_basic_salary,
                    empdata_id.id
                )

                prorate = " - By Amount" if not empdeduct.deduction_id.pro_rate else " - Pro rate"

                paydet = self.env['payroll.payroll.summary.detail'].search([
                    ('payroll_summary_id', '=', payroll_id),
                    ('type_id', '=', empdeduct.deduction_id.id),
                    ('type', '=', '2')
                ], limit=1)

                if paydet:
                    paydet.write({
                        'name': f'{empdeduct.deduction_id.name}',
                        'condition_text':f'{empdeduct.deduction_id.name}{prorate}',
                        'amount': deduct_data[0],
                        'net_amount': deduct_data[0],
                        'currency_id': empdeduct.currency_id.id,
                        'days_count': deduct_data[1],
                    })
                    total_deduct_amount += paydet.amount
                else:
                    self.env['payroll.payroll.summary.detail'].create({
                        'payroll_summary_id': payroll_id,
                        'type_id': empdeduct.deduction_id.id,
                        'type': 2,
                        'type_text': 'Deduction',
                        'name': f'{empdeduct.deduction_id.name}',
                        'condition_text':f'{empdeduct.deduction_id.name}{prorate}',
                        'amount': deduct_data[0],
                        'net_amount': deduct_data[0],
                        'currency_id': empdeduct.currency_id.id,
                        'days_count': deduct_data[1],
                    })
                    total_deduct_amount += paydet.amount

        return total_deduct_amount

    def _fn_calc_deduction(self, pardeduct_type, total_days, deduct_days, prorate, default_amount, amount_from_basic_salary, emp_id):
        deduct_amount = 0
        day_count = 0

        # Early return if total_days is 0
        # if total_days == 0:
        #     return 0, day_count  # Deduction amount is 0 if there are no working days

        # Map deduction type to day count index
        # day_count_index = {
        #     1: 1,   # Absen
        #     4: 4,   # Absen Late
        #     5: 5,   # Absen Not Check Out
        #     6: 6,   # Permision
        #     7: 7,   # Absen Late 2
        #     8: 8,   # Absen Late 3
        #     9: 9    # Absen Late 4
        #     # Add more cases as needed
        # }

        if pardeduct_type == '1':
            day_count = deduct_days[1]  # Absen
        elif pardeduct_type == '4':
            day_count = deduct_days[4]  # Absen Late
        elif pardeduct_type == '5':
            day_count = deduct_days[5]  # Absen Not Check Out
        elif pardeduct_type == '6':
            day_count = deduct_days[6]  # Permission
        elif pardeduct_type == '7':
            day_count = deduct_days[7]  # Absen Late 2
        elif pardeduct_type == '8':
            day_count = deduct_days[8]  # Absen Late 3
        elif pardeduct_type == '9':
            day_count = deduct_days[9]  # Absen Late 4


        # Retrieve day count based on deduction type
        # if pardeduct_type in day_count_index:
        #     day_count = deduct_days[day_count_index[pardeduct_type]]

        # Calculate deduction amount
        if total_days == 0:
            # raise ValidationError(f'Emp with total days 0: {emp_id}')
            pass
        else:
            if prorate == True and amount_from_basic_salary == False:
                prorate_dec = day_count / total_days
                deduct_amount = default_amount * prorate_dec
            elif prorate == True and amount_from_basic_salary == True:
                prorate_dec = day_count / total_days
                basic_salary = 0
                emp_sal = self.env['payroll.employee.salary'].search([
                    ('employee_id', '=', emp_id),
                    ('is_basic_salary', '=', True)
                ], limit=1) 
                if not emp_sal:
                    basic_salary = emp_sal.amount
                
                deduct_amount = basic_salary * prorate_dec
                # # Fetch basic salary amount
                # emp_sal = self.env['payroll.employee.salary'].search([
                #     ('employee_id', '=', emp_id),
                #     ('is_basic_salary', '=', True)
                # ], limit=1)
                # basicsalary = emp_sal.amount if emp_sal else 0
                # deduct_amount = basicsalary * prorate_dec
            else:
                deduct_amount = (default_amount * day_count) * -1

        return deduct_amount, day_count

    def _fn_insert_payroll_detail_deduction2(self, payroll_id, emp_data, total_days, deduct_days):
        emp_deducts = self.env['payroll.employee.deduction'].search([
            ('employee_id', '=', emp_data.id)
        ])

        for emp_case in emp_deducts:
            cat_deduction = self.env['payroll.emp.cat.deduction'].search([
                ('categories_id', '=', emp_data.category_id.id),
                ('deduction_id', '=', emp_case.deduction_id.id)
            ], limit=1)

            if not cat_deduction:
                deduct_amount, day_count = self._fn_calc_deduction(
                    emp_case.deduction_id.source,
                    total_days,
                    deduct_days,
                    emp_case.deduction_id.pro_rate,
                    emp_case.amount,
                    False,  # Assuming amount_from_basic_salary is False for employee deductions
                    emp_data.id
                )

                prorate = " - By Amount" if not emp_case.deduction_id.pro_rate else " - Pro rate"

                paydet = self.env['payroll.payroll.summary.detail'].search([
                    ('payroll_summary_id', '=', payroll_id),
                    ('type_id', '=', emp_case.deduction_id.id),
                    ('type', '=', '2')
                ], limit=1)

                if paydet:
                    paydet.write({
                        'name': f'{emp_case.deduction_id.name}',
                        'condition': emp_case.deduction_id.id,
                        'condition_text':f'{emp_case.deduction_id.name}{prorate}',
                        'amount': deduct_amount,
                        'net_amount': deduct_amount,
                        'currency_id': emp_case.currency_id.id,
                        'days_count': day_count,
                    })
                else:
                    self.env['payroll.payroll.summary.detail'].create({
                        'payroll_summary_id': payroll_id,
                        'type_id': emp_case.deduction_id.id,
                        'type': 2,
                        'type_text': 'Deduction',
                        'name': f'{emp_case.deduction_id.name}',
                        'condition': emp_case.deduction_id.id,
                        'condition_text':f'{emp_case.deduction_id.name}{prorate}',
                        'amount': deduct_amount,
                        'net_amount': deduct_amount,
                        'currency_id': emp_case.currency_id.id,
                        'days_count': day_count,
                    })
        return True        

    def _fn_calc_leave_not_taken(self, payroll_id, emp_data, start_date, end_date):
        context = dict(self._context or {})

        tor = self.env['payroll.time.off.request'].search([
            ('employee_id', '=', emp_data.id),
            ('start_date', '>=', start_date),
            ('start_date', '<=', end_date),
            ('status', '=', '5'),
            ('request_type', '=', '6')
        ])

        if tor:
            cat = self.env['payroll.emp.cat.timeoff.setup'].search([
                ('categories_id', '=', emp_data.category_id.id),
                ('type', '=', '1')
            ])

            if cat and cat.ticket_amount != 0:
                date_active = emp_data.active_leave_date or emp_data.active_date + relativedelta(months=cat.minimum_working_duration)

                if date_active <= end_date:
                    # Insert or update payroll detail for ticket not taken amount
                    paydet = self.env['payroll.payroll.summary.detail'].search([
                        ('payroll_summary_id', '=', payroll_id),
                        ('type_id', '=', False),
                        ('type', '=', "1")
                    ], limit=1)

                    if paydet:
                        paydet.write({
                            'amount': cat.ticket_amount,
                            'net_amount': cat.ticket_amount,
                            'name': 'Ticket Not Taken',
                            'currency_id': cat.ticket_currency_id.id,
                        })
                    else:
                        self.env['payroll.payroll.summary.detail'].create({
                            'payroll_summary_id': payroll_id,
                            'type_id': False,
                            'type': 1,
                            'type_text': 'Salaries',
                            'name': 'Ticket Not Taken',
                            'amount': cat.ticket_amount,
                            'net_amount': cat.ticket_amount,
                            'currency_id': cat.ticket_currency_id.id,
                            'condition': False,
                            'days_count': 0,
                        })
            emp_sal = self.env['payroll.employee.salary'].search([
                ('employee_id', '=', emp_data.id),
                ('condition', '=', '2')
            ], limit=1)

            if emp_sal and emp_sal.amount != 0:
                date_active = emp_data.active_leave_date or emp_data.active_date + relativedelta(months=emp_sal.minimum_working_duration)

                if date_active <= end_date:
                    # Insert or update payroll detail for ticket not taken amount
                    paydet = self.env['payroll.payroll.summary.detail'].search([
                        ('payroll_summary_id', '=', payroll_id),
                        ('type_id', '=', emp_sal.salary_component_id.id),
                        ('type', '=', "1")
                    ], limit=1)

                    if paydet:
                        paydet.write({
                            'amount': emp_sal.amount,
                            'net_amount': emp_sal.amount,
                            'name': emp_sal.salary_component_id.name,
                            'currency_id': emp_sal.currency_id.id,
                        })
                    else:
                        self.env['payroll.payroll.summary.detail'].create({
                            'payroll_summary_id': payroll_id,
                            'type_id': False,
                            'type': 1,
                            'type_text': 'Salaries',
                            'name': emp_sal.salary_component_id.name,
                            'amount': emp_sal.amount,
                            'net_amount': emp_sal.amount,
                            'currency_id': emp_sal.currency_id.id,
                            'condition': False,
                            'days_count': 0,
                        })
        return True

    def _fn_calculate_salary_ph(self, emp_id, sch_setup, calculate_start_date, calculate_end_date, finished, emp_category, period):
        """
        Func in C# :
        fnUpdatePayrollSummaryPH"""
        context = dict(self._context or {})

        end_date = calculate_end_date
        start_date = calculate_start_date

        year = end_date.year
        month = end_date.month

        totdays = (end_date - start_date.date()).days + 1

        emp_data = self.env['payroll.employees'].search([
            ('id', '=', emp_id.id)
        ], limit=1)


        payroll_summary = self.env['payroll.payroll.summaries'].search([
            ('employee_id', '=', emp_id.id),
            ('month', '=', month),
            ('year', '=', year),
            ('periode', '=', str(period))
        ])

        if not payroll_summary:
            payroll_summary = self.env['payroll.payroll.summaries'].create({
                'employee_id': emp_id.id,
                'month': month,
                'year': year,
                'periode': str(period),
                # 'date': end_date,
            })

            self._fn_update_payroll_summary_ph(payroll_summary.id, emp_id.id, start_date, end_date, sch_setup, finished, emp_data, totdays, period)
        else:
            pay_details = self.env['payroll.payroll.summary.detail'].search([
                ('payroll_summary_id', '=', payroll_summary.id)
            ])
            pay_details.unlink()

            self._fn_update_payroll_summary_ph(payroll_summary.id, emp_id.id, start_date, end_date, sch_setup, finished, emp_data, totdays, period)

    def _fn_update_payroll_summary_ph(self, pay_id, emp_id, start_date, end_date, sch_setup, finished, emp_data, total_days, period):
        """
        Func in C# :
        fnInsertPayrollGrossSalaryPH DONE"""
        paysum = self.env['payroll.payroll.summaries'].search([
            ('id', '=', pay_id)
        ], limit=1)

        if paysum:
            # Absence calculation
            absen_info = self._fn_calc_absence(emp_id, start_date.date(), end_date)
            emp_sal_data = self._fn_insert_payroll_detail_salary(paysum.id, emp_data, total_days, start_date.date(), end_date, absen_info[1], period)

            # Date updates
            paysum.from_date = start_date
            paysum.to_date = end_date

            self._fn_calc_reimbursements(emp_id.user_id.id, start_date, end_date, paysum.id)

            paysum.days_in = absen_info[0]
            paysum.days_absent = absen_info[1]
            paysum.days_leave = absen_info[3]
            paysum.sick_permission = absen_info[5]
            paysum.days_permission = absen_info[6]
            paysum.days_off = absen_info[8]
            paysum.total_work_days = absen_info[9]

            # Point calculation
            point_records = self.env['payroll.attendance.log'].search([
                ('employee_id', '=', emp_id),
                ('date', '>=', start_date),
                ('date', '<=', end_date)
            ])
            # total_point += 0.04
            total_point = sum(point_records.mapped('ph_points')) if point_records else 0.0
            total_point += 0.04
            paysum.total_point = total_point

            # Ticket payment
            if paysum.days_leave != 0:
                self._fn_calc_ticket_amount(paysum.id, emp_data, start_date, end_date)

            # Late calculation
            late_info = self._fn_calc_late(emp_id, start_date, end_date)
            paysum.late = late_info[0]
            paysum.late2 = late_info[1]

            # Forget checkout calculation
            forget_checkout_info = self._fn_calc_forget_checkout(emp_id, start_date, end_date)
            paysum.forget_checkout_count = forget_checkout_info[0]

            # Reward calculation if finished
            if finished:
                self._fn_calc_reward(emp_id, start_date, end_date, paysum.id, paysum.late, paysum.forget_checkout_count, paysum.days_absent, paysum.days_permission)

            # Mistake calculation
            mistake_info = self._fn_calc_mistake(emp_id, start_date, end_date, paysum.id)
            paysum.mistake_1_count = mistake_info[0]
            paysum.mistake_2_count = mistake_info[2]

            # Deduction calculation
            deduct_count = {
                1: absen_info[1],        # Days absence
                2: mistake_info[0],      # Mistake 1
                3: mistake_info[2],      # Mistake 2
                4: paysum.late,          # Absence late
                5: paysum.forget_checkout_count,  # Absence not check out
                6: paysum.days_permission,         # Permission
                7: paysum.late2           # Absence late layer 2
            }
            deduction_data = self._fn_insert_payroll_detail_deduction(paysum.id, emp_data, paysum.total_work_days, deduct_count)

            # Employee deduction check
            self._fn_insert_payroll_detail_deduction2(paysum.id, emp_data, paysum.total_work_days, deduct_count)

            # Not taken leave calculation
            self._fn_calc_leave_not_taken(paysum.id, emp_data, start_date, end_date)

            paysum.total_deduction = deduction_data
            # Calculate net salary (if needed)
            # paysum.net_salary = paysum.basic_salary - paysum.total_deduction + paysum.total_reward

            # Update paysum
            paysum.write({
                'net_salary': paysum.net_salary,
                'finished': finished,
            })

            # Gross salary PH calculation
            empsal_data_ph = self._fn_insert_payroll_gross_salary_ph(paysum.id, emp_data, total_days, start_date, end_date, absen_info[1], period)
            paysum.write({
                'net_salary': empsal_data_ph[0],
                'currency_id': empsal_data_ph[1],
                # 'currency_name': empsal_data_ph[2],
                # 'currency_symbol': empsal_data_ph[3],
            })

    def _fn_insert_payroll_gross_salary_ph(self, payroll_id, emp_data, total_days, start_date, end_date, absence_count, period):
        """
        Func in C# :
        fnInsertPayrolllDeductionPH DONE"""
        payrol_detail = self.env['payroll.payroll.summary.detail']
        payroll_summary = self.env['payroll.payroll.summaries'].search([
            ('id', '=', payroll_id)
        ], limit=1)
         
        if payroll_summary:
            empsal = self.env['payroll.employee.salary'].search([
               ('employee_id', '=', emp_data.id),
               ('condition', '=', False),
               ('is_basic_salary', '=', True)
           ])
            daily_rate = 0
            salary_amount = 0
            curr_id = False
            for empsalary in empsal:
                activate_date = emp_data.active_date + relativedelta(months=empsalary.minimum_working_duration)
                if end_date >= activate_date:
                    daily_rate = empsalary.amount / 26.08
                    attendance_log = self.env['payroll.attendance.log'].search([
                       ('employee_id', '=', emp_data.id),
                       ('date', '>=', start_date),
                       ('date', '<=', end_date)
                   ])
                    
                    nd_hours_amount = sum(log.is_night_diff for log in attendance_log) * 8 * daily_rate * 0.1
                    sh_hours_amount = sum(1 for log in attendance_log if log.holiday_type == '2' and log.weekday != 0) * 8 * daily_rate * 0.3
                    lh_hours_amount = sum(1 for log in attendance_log if log.holiday_type == '1' and log.weekday != 0) * 8 * daily_rate
                    sh_sunday_hours_amount = sum(1 for log in attendance_log if log.holiday_type == '2' and log.weekday == 0) * 8 * daily_rate * 1.69
                    lh_sunday_hours_amount = sum(1 for log in attendance_log if log.holiday_type == '1' and log.weekday == 0) * 8 * daily_rate * 1.5
                    total_amount = (payroll_summary.total_point * daily_rate) + \
                                  ((payroll_summary.days_leave + payroll_summary.days_permission) * daily_rate) + \
                                  (payroll_summary.sick_permission * daily_rate)
                    gross_amount = total_amount + nd_hours_amount + sh_hours_amount + lh_hours_amount + sh_sunday_hours_amount + lh_sunday_hours_amount
                    salary_amount += gross_amount
                   #  insert or update payroll detail for gross salary
                    paydet = payrol_detail.search([
                       ('payroll_summary_id', '=', payroll_id),
                       ('type_id', '=', empsalary.salary_component_id.id),
                       ('type', '=', '1')
                   ], limit=1)
                    
                    if paydet:
                        paydet.write({
                           'name': empsalary.salary_component_id.name,
                           'amount': empsalary.amount,
                           'net_amount': gross_amount,
                           'currency_id': empsalary.currency_id.id,
                           'days_count': total_days,
                       })
                    else:
                        payrol_detail.create({
                           'payroll_summary_id': payroll_id,
                           'type_id': empsalary.salary_component_id.id,
                           'type': 1,
                           'type_text': 'Salaries',
                           'name': empsalary.salary_component_id.name,
                           'amount': empsalary.amount,
                           'net_amount': gross_amount,
                           'currency_id': empsalary.currency_id.id,
                           'condition': False,
                           'days_count': total_days,
                       })
                    curr_id = empsalary.currency_id.id
            net_salary = self._fn_insert_payroll_deduction_ph(payroll_id, emp_data, daily_rate, curr_id, salary_amount, period)
            curencies = self.env['payroll.currencies'].search([('id', '=', curr_id)])
            return net_salary, curr_id, curencies.name, curencies.currency_symbol   
                 
    def _fn_insert_payroll_deduction_ph(self, payroll_id, emp_data, daily_rate, curr_id, salary_amount, period):
        payroll_detail = self.env['payroll.payroll.summary.detail']
        payroll_summary = self.env['payroll.payroll.summaries'].search([
            ('id', '=', payroll_id)
        ], limit=1)

        if payroll_summary:
            salamount = salary_amount
            salid = self.env['payroll.salary.components'].search([
                ('is_basic_salary', '=', True)
            ], limit=1)
            basicsal = payroll_detail.search([
                ('payroll_summary_id', '=', payroll_id),
                ('type_id', '=', salid.id),
            ], limit=1)

            deduction_ph_data = self.env['payroll.deductions'].search([
                ('ph_deduction_type', '!=', False),
            ])

            for d in deduction_ph_data:
                deductamount = 0
                day_count = 0
                sssamount = 0
                pgamount = 0
                phhealthamount = 0

                attlogdata = self.env['payroll.attendance.log'].search([
                    ('employee_id', '=', emp_data.id),
                    ('date', '>=', payroll_summary.from_date),
                    ('date', '<=', payroll_summary.to_date)
                ])

                if d.ph_deduction_type == '1': # Late
                    deductamount = sum(attlogdata.mapped('late_minutes'))
                    day_count = deductamount
                elif d.ph_deduction_type == '2': # Absence
                    deductamount = payroll_summary.days_absent * daily_rate
                    day_count = payroll_summary.days_absent
                # elif d.ph_deduction_type == 3:  # SSS kemarin tidak diperlukan.. tinggal sisa holiday saja
                #     if period == 2 and basicsal:
                #         deductamount = self.env['ph.sss'].search([
                #             ('start_amount', '<=', basicsal.amount)
                #         ], order='start_amount desc', limit=1).employee_share
                #         sssamount = deductamount
                elif d.ph_deduction_type == '4': # PH Health
                    if period == '2' and basicsal:
                        ph_health = self.env['payroll.ph.health'].search([
                            ('start_amount', '<=', basicsal.amount),
                        ], limit=1)
                        if ph_health:
                            deductamount = ((basicsal.amount + ph_health.compensation_range) * (ph_health.tax_rate_percent / 100) + ph_health.prescribed_wtx) / 2
                            phhealthamount = deductamount
                # elif d.ph_deduction_type == 5:  # PG kemarin tidak diperlukan.. tinggal sisa holiday saja
                #     if period == 2 and basicsal:
                #         pg = self.env['ph.pg'].search([
                #             ('start_amount', '<=', basicsal.amount)
                #         ], order='start_amount desc', limit=1)
                #         if pg:
                #             deductamount = pg.compensationrange * pg.pgrate_percent / 100
                #             pgamount = deductamount
                # elif d.ph_deduction_type == 6:  # Wtax kemarin tidak diperlukan.. tinggal sisa holiday saja
                #     datepayroll = payroll_summary.from_date
                #     paysumbefore = self.env['payroll.summary'].search([
                #         ('employee_id', '=', payroll_summary.employee_id.id),
                #         ('from_date', '=', datepayroll + timedelta(days=-1 * (30)))
                #     ], limit=1)

                #     paysumbeforeval = paysumbefore.net_salary if paysumbefore else 0
                #     amountbeforetax = salamount + sssamount + pgamount + phhealthamount + paysumbeforeval
                #     wtax = self.env['ph.wtax'].search([
                #         ('start_amount', '<=', amountbeforetax)
                #     ], order='start_amount desc', limit=1)
                #     if wtax:
                #         deductamount = (amountbeforetax - wtax.compensationrange) * (wtax.tax_rate_percent / 100)

            if deductamount != 0:
                salamount -= deductamount

                paydet = payroll_detail.search([
                    ('payroll_summary_id', '=', payroll_id),
                    ('type_id', '=', d.id),
                    ('type', '=', '2')
                ], limit=1)

                if paydet:
                    paydet.write({
                        'name': d.name,
                        'amount': deductamount,
                        'net_amount': deductamount,
                        'currency_id': curr_id,
                        'days_count': day_count,
                    })
                else:
                    payroll_detail.create({
                        'payroll_summary_id': payroll_id,
                        'type_id': d.id,
                        'type': 2,
                        'type_text': 'Deduction',
                        'name': d.name,
                        'amount': deductamount,
                        'net_amount': deductamount,
                        'currency_id': curr_id,
                        'days_count': day_count,
                    })

            return salamount

    # Shafilah - 2024-07-12
    def convert_attendance_device_to_att_log(self):
        """
        PostAttendanceDevice"""
        # When insert to attendance logs, it will be automatically create payroll attendance logs
        raise UserError('Not implemented yet!')
    
    def auto_create_user(self):
        """
        Create Employee"""
        # Automatic create user/employee in zk machine if not exist
        raise UserError('Not implemented yet!')
    
    def recalculate_late_salary(self):
        """
        Recalculate Late Salary"""
        attendance_log = self.env['payroll.attendance.log'].search([
            ('date', '>=', self.calculate_date),
            ('end_time', '!=', False)
        ])
        for att_log in attendance_log:
            duration = att_log.end_time - att_log.start_time
            if duration.total_seconds() > 0:
                hour = duration.days * 24 + (duration.seconds / 3600)
                # att_log.working_hours = hour
                att_log.write({
                    'working_hours': hour
                })
            else:
                att_log.write({
                    'working_hours': 0
                })

        attendance_log2 = self.env['payroll.attendance.log'].search([
            ('employee_id', '=', self.employee_ids.id),
            ('date', '>=', self.calculate_date),
            ('working_hours', '>', 20)
        ])
        for att_log2 in attendance_log2:
            start_time_log = att_log2.start_time
            dt2 = datetime(start_time_log.year, start_time_log.month, start_time_log.day)
            jam_masuk = datetime(start_time_log.year, start_time_log.month, start_time_log.day, 12, 0, 0)
            if start_time_log <= jam_masuk:
                attd = self.env['payroll.attendance.device'].search([
                    ('nik', '=', att_log2.nik),
                    ('device_department_id', '=', att_log2.device_department_id.id),
                    ('punch_type', 'in', ['1', '4']),
                    ('punching_time', '=', start_time_log)
                ])
                if attd:
                    att_log2.end_time = attd.punching_time

                    duration = att_log2.end_time - att_log2.start_time

                    if duration.total_seconds() > 0:
                        hour = duration.days * 24 + (duration.seconds / 3600)
                        att_log2.write({
                            'working_hours': hour
                        })
                    else:
                        att_log2.write({
                            'working_hours': 0,
                            'end_time': False
                        })
                else:
                    dt2 = dt2 + timedelta(days=1)
                    attd = self.env['payroll.attendance.device'].search([
                        ('nik', '=', att_log2.nik),
                        ('device_department_id', '=', att_log2.device_department_id.id),
                        ('punch_type', 'in', ['1', '4']),
                        ('punching_time', '=', dt2)
                    ])

                    if attd:
                        att_log2.end_time = attd.punching_time

                        duration = att_log2.end_time - att_log2.start_time

                        if duration.total_seconds() > 0:
                            hour = duration.days * 24 + (duration.seconds / 3600)
                            att_log2.write({
                                'working_hours': hour
                            })
                        else:
                            att_log2.write({
                                'working_hours': 0,
                                'end_time': False
                            })
                    else:
                        att_log2.write({
                            'working_hours': 0,
                            'end_time': False
                        })
  
    def fill_last_date_leave(self):
        """
        Get last date leave"""
        employee = self.env['payroll.employees'].search([])
        for emp in employee:
            attlog = self.env['payroll.attendance.log'].search([
                ('employee_id', '=', emp.id),
                ('time_off_type', 'in', ['1', '6']),
            ], order='date desc', limit=1)
            if attlog:
                emp.write({
                    'last_leave_date': attlog.date
                })
        # for emp in employee.with_progress(msg="Processing"):
        #     attlog = self.env['payroll.attendance.log'].search([
        #         ('employee_id', '=', emp.id),
        #         ('time_off_type', 'in', ['1', '6']),
        #     ], order='date desc', limit=1)
        #     if attlog:
        #         emp.write({
        #             'last_leave_date': attlog.date
        #         })
            # if attlog:
            #     attlog = attlog.sorted(key=lambda r: r.date, reverse=True)
            #     emp.write({
            #         'last_leave_date': attlog.date
            #     })

        # message = f'{len(employee)} employee(s) has been updated'
        # return{
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': 'Success',
        #         'message': message,
        #         'sticky': False
        #     }
        # }
        