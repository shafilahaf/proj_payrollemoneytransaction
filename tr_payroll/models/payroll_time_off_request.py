from odoo import _, api, fields, models # type: ignore
from odoo.exceptions import ValidationError, UserError # type: ignore
from dateutil.relativedelta import relativedelta # type: ignore
from datetime import datetime, timedelta
from pytz import timezone, utc

class PayrollTimeOffRequest(models.Model):
    _name = 'payroll.time.off.request'
    _description = 'Time Off Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, default='New')
    request_date = fields.Date(string='Request Date', default=fields.Date.today)
    request_type = fields.Selection([
        ('1', 'Leave'),
        ('2', 'Sick'),
        ('3', 'Permission'),
        ('4', 'Day Off'),
        ('5', 'Device Error'),
        ('6', 'Not Taken Leave'),
        ('7', 'Medical Reimburment W/O Off'),
        ('99', 'Absence'),
    ], string='Request Type')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    duration = fields.Integer(string='Duration', store=True, readonly=True)
    remaining_leave = fields.Integer(string='Remaining Leave', readonly=True)
    file = fields.Binary(string='File')
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    status = fields.Selection([
        ('1', 'Open'),
        ('2', 'Pending Approval'),
        ('3', 'Rejected'),
        ('5', 'Approved'),
        ('6', 'Cancelled')
    ], string='Status', default='1')
    # remaining leave days belum
    time_off_request_approval_ids = fields.One2many('payroll.time.off.request.approval', 'request_id', string='Time Off Request Approval')
    reimburse_amount = fields.Float(string='Reimburse Amount')
    remaining_amount = fields.Float(string='Remaining Amount', readonly=True)
    ticket_amount = fields.Float(string='Ticket Amount')
    remaining_off_day = fields.Float(string='Remaining Off Day', readonly=True)
     # remarks and currency(related to payroll currency table)
    remarks = fields.Text(string='Remarks')
    currency_id = fields.Many2one('payroll.currencies', string='Currency')
    employee_id = fields.Many2one('payroll.employees', string='Employee', store=True, readonly=True)
    created_manual_system = fields.Boolean(string='Created Manual System', default=False)
    internal_note = fields.Char(string="Internal Note", readonly=True)

    def open_tor(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Time Off Request',
            'res_model': 'payroll.time.off.request',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        user_groups = user.groups_id

        allowed_departments = []
        allowed_categories = []

        for group in user_groups:
            if group.is_active:
                allowed_departments += group.department_ids.ids
                allowed_categories += group.categories_ids.ids

        domain = []

        # if allowed_departments and allowed_categories:
        #     for dept in allowed_departments:
        #         for cat in allowed_categories:
        #             domain += ['|', ('employee_id.department_id', '=', dept), ('employee_id.category_id', '=', cat)]
        # elif allowed_departments:
        #     for dept in allowed_departments:
        #         domain += [('employee_id.department_id', '=', dept)]
        # elif allowed_categories:
        #     for cat in allowed_categories:
        #         domain += [('employee_id.category_id', '=', cat)]

        domain = []
        if allowed_departments and allowed_categories:
            domain = ['|', ('employee_id.department_id', 'in', allowed_departments), ('employee_id.category_id', 'in', allowed_categories)]
        elif allowed_departments:
            domain = [('employee_id.department_id', 'in', allowed_departments)]
        elif allowed_categories:
            domain = [('employee_id.category_id', 'in', allowed_categories)]


        if user.payroll_positions_level:
            domain += ['|', 
                       ('employee_id.current_position.level', '>', user.payroll_positions_level), 
                       ('employee_id', '=', user.payroll_employee_id.id)]

        if domain:
            args += domain

        return super(PayrollTimeOffRequest, self).search(args, offset=offset, limit=limit, order=order, count=count)
    
    
    @api.onchange('created_by')
    def _onchange_created_by(self):
        for record in self:
            if record.created_by:
                employee = self.env['payroll.employees'].search([('user_id', '=', record.created_by.id)], limit=1)
                record.employee_id = employee

    @api.onchange('start_date', 'end_date', 'request_type')
    def _onchange_request_type(self):
        for rec in self:

            if rec.start_date and not rec.end_date:
                rec.end_date = rec.start_date

            #employee = self.env['payroll.employees'].search([('user_id', '=', self.env.user.id)], limit=1)
            employee = self.env['payroll.employees'].search([('id', '=', self.employee_id.id)], limit=1)
            if rec.request_type in ['1', '6']: # Leave
                rec.remaining_leave = 0
                empdtl = self.env['payroll.employee.details'].search([('employee_id', '=', employee.id), ('type', '=', '1'), ('isActive', '=', True), ('active_date', '<=', rec.start_date),('expired_date', '>=', rec.end_date)], order='active_date desc')
                if empdtl:
                    
                    timeoffreq = self.env['payroll.time.off.request'].search([('created_by', '=', self.env.user.id), ('request_type', '=', self.request_type), ('status', 'in', ['1']), 
                                                                              ('start_date', '>=', empdtl.active_date), ('end_date', '<=', empdtl.expired_date)])
                    rec.remaining_leave = sum(empdtl.mapped('quantity'))
                    if timeoffreq:
                        # rec.remaining_off_day = rec.remaining_leave - sum(timeoffreq.mapped('duration'))
                        rec.remaining_leave -= sum(timeoffreq.mapped('duration'))
                        rec.remaining_leave = max(0, rec.remaining_leave) # Ensure remaining leave is not negative
                    
                    attlog = self.env['payroll.attendance.log'].search([('employee_id', '=', employee.id), ('time_off_type', '=', self.request_type), ('date', '>=', empdtl.active_date), ('date', '<=', empdtl.expired_date)])
                    if attlog:
                        # rec.remaining_off_day -= len(attlog)
                        rec.remaining_leave -= len(attlog)
                        rec.remaining_leave = max(0, rec.remaining_leave) # Ensure remaining leave is not negative
            elif rec.request_type in ['2', '7']:  # Sick or Medical Reimbursement
                empdtl = self.env['payroll.employee.details'].search([
                    ('employee_id', '=', employee.id), 
                    ('type', '=', '3'), 
                    ('isActive', '=', True),
                    ('active_date', '<=', rec.start_date),
                    ('expired_date', '>=', rec.end_date)
                ], order='active_date desc', limit=1)

                if empdtl:
                    rec.remaining_leave = sum(empdtl.mapped('quantity'))
                    rec.remaining_amount = sum(empdtl.mapped('amount'))
                else:
                    rec.remaining_leave = 0
                    rec.remaining_amount = 0
                
                if empdtl:
                    timeoffreq = self.env['payroll.time.off.request'].search([
                        ('created_by', '=', self.env.user.id),
                        ('request_type', 'in', ['2']),
                        ('status', 'in', ['5']), 
                        ('start_date', '>=', empdtl.active_date), 
                        ('end_date', '<=', empdtl.expired_date),
                    ])
                    if timeoffreq:
                        rec.remaining_leave = rec.remaining_leave - sum(timeoffreq.mapped('duration'))
                        rec.remaining_leave = max(0, rec.remaining_leave) # Ensure remaining leave is not negative
                        rec.remaining_amount -= sum(timeoffreq.mapped('reimburse_amount'))
                    
                    timeoffreq2 = self.env['payroll.time.off.request'].search([
                        ('created_by', '=', self.env.user.id),
                        ('request_type', 'in', ['7']),
                        ('status', 'in', ['2']), 
                        ('start_date', '>=', empdtl.active_date), 
                        ('end_date', '<=', empdtl.expired_date),
                    ])
                    if timeoffreq2:
                        rec.remaining_amount -= sum(timeoffreq2.mapped('reimburse_amount'))

            elif rec.request_type == '4':  # Day Off
                empdtl = self.env['payroll.employee.details'].search([
                    ('employee_id', '=', employee.id), 
                    ('type', '=', '2'), 
                    ('isActive', '=', True),
                    ('active_date', '<=', rec.start_date),
                    ('expired_date', '>=', rec.end_date)
                ], order='active_date desc', limit=1)

                if empdtl:
                    rec.remaining_leave = sum(empdtl.mapped('quantity'))
                else:
                    rec.remaining_leave = 0
                
                if empdtl:
                    timeoffreq = self.env['payroll.time.off.request'].search([
                        ('created_by', '=', self.env.user.id),
                        ('request_type', '=', self.request_type),
                        ('status', 'in', ['1']),
                        ('start_date', '>=', empdtl.active_date), 
                        ('end_date', '<=', empdtl.expired_date),
                    ])
                    if timeoffreq:
                        rec.remaining_off_day = rec.remaining_leave - sum(timeoffreq.mapped('duration'))
                    attlog = self.env['payroll.attendance.log'].search([
                        ('employee_id', '=', employee.id),
                        ('time_off_type', '=', self.request_type),
                        ('date', '>=', empdtl.active_date),
                        ('date', '<=', empdtl.expired_date)
                    ])
                    if attlog:
                        rec.remaining_off_day -= len(attlog)
            elif rec.request_type in ['3', '5', '99']:
                rec.remaining_leave = 0
                rec.remaining_amount = 0
                rec.remaining_off_day = 0

    @api.model
    def create(self, vals):
        """
        This method is called when creating a new record."""
        vals['name'] = self.env['ir.sequence'].next_by_code('payroll.time.off.request') or 'New'
        record = super(PayrollTimeOffRequest, self).create(vals)
        if record.status == '5':
            record._create_attendance_log()
        return record
    
    def _create_attendance_log(self):
        for request in self:
            if request.request_type and request.request_type not in ['6', '7']:
                start_date = request.start_date
                end_date = request.end_date
                remaining_days = request.remaining_leave
                employee = self.env['payroll.employees'].search([('user_id', '=', self.env.user.id)], limit=1)
                # requester = self.env['payroll.employees'].search([('user_id', '=', self.employee_id.id)], limit=1)
                if self.employee_id:
                    requester = self.env['payroll.employees'].search([('id', '=', self.employee_id.id)], limit=1)
                else:
                    requester = self.env['payroll.employees'].search([('user_id', '=', self.created_by.id)], limit=1)

                days_diff = (end_date - start_date).days + 1  # Calculate the number of days

                for day in range(days_diff):
                    current_date = start_date + timedelta(days=day)

                    if request.request_type == '2' and remaining_days > 0:
                        attendance_log = self.env['payroll.attendance.log'].search([
                            ('employee_id', '=', requester.id),
                            ('date', '=', current_date)
                        ], limit=1)

                        if attendance_log:
                            attendance_log.write({
                                'start_time': current_date,
                                'end_time': current_date,
                                'time_off_type': request.request_type,
                                'source': 'Time Off Request',
                                'source_id': request.id
                            })
                        else:
                            self.env['payroll.attendance.log'].create({
                                'nik': requester.nik,
                                'employee_id': requester.id,
                                'date': current_date,
                                'start_time': current_date,
                                'end_time': current_date,
                                'time_off_type': request.request_type,
                                'source': 'Time Off Request',
                                'source_id': request.id,
                                'department_id': requester.department_id.id
                            })
                        remaining_days -= 1  # Decrement remaining days

                    elif request.request_type == '2' and remaining_days <= 0:
                        requester_category = self.env['payroll.employee.categories'].search([
                            ('id', '=', requester.category_id.id)
                        ], limit=1)

                        if requester_category:
                            attendance_log = self.env['payroll.attendance.log'].search([
                                ('employee_id', '=', requester.id),
                                ('date', '=', current_date)
                            ], limit=1)

                            if attendance_log:
                                if not requester_category.over_sick_deduction_to or requester_category.over_sick_deduction_to == '1':
                                    attendance_log.unlink()
                                elif requester_category.over_sick_deduction_to == '2':
                                    attendance_log.write({
                                        'time_off_type': '3',
                                        'text': 'Permission Over Sick'
                                    })
                            else:
                                if requester_category.over_sick_deduction_to == '2':
                                    self.env['payroll.attendance.log'].create({
                                        'nik': requester.nik,
                                        'employee_id': requester.id,
                                        'date': current_date,
                                        'start_time': current_date,
                                        'end_time': current_date,
                                        'time_off_type': '3',
                                        'source': 'Time Off Request',
                                        'source_id': request.id,
                                        'text': 'Permission Over Sick',
                                        'department_id': requester.department_id.id
                                    })

                    else:
                        if request.duration > 0:
                            current_dates = start_date + timedelta(days=day)
                            user_tz = self.env.user.tz or 'UTC' 
                            local_tz = timezone(user_tz)
                            current_date = datetime.combine(
                                start_date + timedelta(days=day),
                                datetime.min.time() 
                            )
                            current_date_localized = local_tz.localize(current_date)  
                            current_date_utc = current_date_localized.astimezone(utc)

                            current_date_naive = current_date_utc.replace(tzinfo=None)
                            self.env['payroll.attendance.log'].create({
                                'nik': requester.nik,
                                'employee_id': requester.id,
                                'date': current_dates,
                                'time_off_type': request.request_type,
                                'source': 'Time Off Request',
                                'source_id': request.id,
                                'department_id': requester.department_id.id,
                                'start_time': current_date_naive,
                                'end_time': current_date_naive,
                            })                     

    # @api.model
    def unlink(self):
        for record in self:
            if record.status != '1':
                raise UserError(_('You can only delete requests that are in Open status.'))
        return super(PayrollTimeOffRequest, self).unlink()

    @api.onchange('start_date', 'end_date')
    def get_duration(self):
        """                                                                                                   
        This method is called when the start_date or end_date field is changed."""
        for rec in self:
            if rec.start_date and rec.end_date:
                rec.duration = (rec.end_date - rec.start_date).days + 1

    def action_submit_for_approval(self):
        """
        This method will submit the time off request for approval. It will create approval entries for each approver in the sequence."""
        for rec in self:
            self.ensure_one()

            if self.request_type in ['1', '4', '6']:
                employee = self.env['payroll.employees'].search([('user_id', '=', self.created_by.id)], limit=1)
                emp_details = self.env['payroll.employee.details'].search([('employee_id', '=', employee.id)], limit=1)

                if not emp_details:
                    raise UserError(_('Employee details not found!'))

                if self.duration > self.remaining_off_day and self.duration > self.remaining_leave:
                    raise UserError(_('Remaining days must be greater than or equal to the duration of the time off request.'))
                if self.start_date <= emp_details.active_date:
                    raise UserError(_('Start date must be greater than the active date. Your active date is %s.') % emp_details.active_date)
                
                if self.request_type == '1' or self.request_type == '6':
                    last_leave_date_emp = self.env['payroll.employees'].search([('user_id', '=', self.created_by.id)], limit=1)
                    if last_leave_date_emp and last_leave_date_emp.last_leave_date:
                        lastLeave = last_leave_date_emp.last_leave_date
                        six_months_after_last_leave = last_leave_date_emp.last_leave_date + relativedelta(months=+6)
                        if six_months_after_last_leave >= self.start_date:
                            raise UserError(_('You can submit the start date request earlier on %s') % six_months_after_last_leave.strftime('%Y-%m-%d'))
            elif self.request_type in ['2', '7']:
                if self.reimburse_amount > self.remaining_amount:
                    raise UserError(_('Remaining Reimbursement Amount must be greater than Request Amount'))

            employee = self.env['payroll.employees'].search([('user_id', '=', self.env.user.id)])
            if not employee:
                raise UserError(_('Employee not found!'))
            if len(employee) > 1:
                raise UserError(_('Multiple employees found! Please ensure there is only one employee associated with this user.'))
            
            employee = employee[0]
            current_position = employee.current_position
            if not current_position:
                raise UserError(_('Current Position not found!'))
            
            sequences = current_position.position_approver_ids.sorted(key=lambda r: r.sequence)
            if not sequences:
                raise UserError(_('Sequence Approver not found!'))
            
            for sequence in sequences:
                approvers = self.env['payroll.employees'].search([
                    ('current_position', '=', sequence.approver_position_id.id),
                    # ('category_id','=', employee.category_id.id)
                ])
                # emp_category = self.employee_id.category_id.sudo().name
                # if not approvers:
                #     raise UserError(_('No approvers found for position %s %s!') % (emp_category, sequence.approver_position_id.name))
                for approver in approvers:
                    approval = self.env['payroll.time.off.request.approval'].create({
                        'request_id': self.id,
                        'approver': approver.id,
                        'approver_current_position': sequence.approver_position_id.id,
                        'sequence': sequence.sequence,
                        'has_approved': False
                    })
                    self.env['payroll.approval.entries'].create({
                        'name': self.env['ir.sequence'].next_by_code('payroll.approval.entries') or 'New',
                        'document_type': '1',
                        'document_id': self.id,
                        'request_date': fields.Date.today(),
                        'request_by': self.env.user.id,
                        'request_by_employee': employee.id,
                        'status': '2',
                        'sequence': sequence.sequence,
                        'approval_id': approval.id,
                        'approver': approver.id
                    })

            # Notify the first approver
            first_approvers = self.time_off_request_approval_ids.filtered(lambda r: r.sequence == 1)
            if not first_approvers:
                raise UserError(_('First Approver not found!'))
            for first_approver in first_approvers:
                rec.activity_schedule('mail.mail_activity_data_todo', note=_('You have a new time off request from %s.') % employee.name, user_id=first_approver.approver.user_id.id)

            rec.write({
                'status': '2'
            })

class PayrollTimeOffRequestApproval(models.Model):
    _name = 'payroll.time.off.request.approval'
    _description = 'Time Off Request Approval'

    request_id = fields.Many2one('payroll.time.off.request', string='Request', required=True, ondelete='cascade')
    approver = fields.Many2one('payroll.employees', string='Approver', required=True)
    approver_current_position = fields.Many2one('payroll.positions', string='Approver Current Position', required=True)
    sequence = fields.Integer(string='Sequence', required=True)
    approver_date = fields.Date(string='Approver Date')
    has_approved = fields.Boolean(string='Has Approved')
    reason = fields.Text(string='Reason')

    def action_approve(self):
        """
        This method will approve the time off request. If the current approver is the last approver, the request will be fully approved. Otherwise, it will notify the next approver."""
        self.ensure_one()
        request = self.request_id
        employee = self.env['payroll.employees'].search([('user_id', '=', self.request_id.created_by.id)], limit=1)

        self.write({'has_approved': True, 'approver_date': fields.Date.today()})
        request.activity_feedback(['mail.mail_activity_data_todo'])

        next_sequence = self.sequence + 1
        next_approvals = request.time_off_request_approval_ids.filtered(lambda a: a.sequence == next_sequence)

        if not next_approvals:
            request.write({'status': '5'})
            request.message_post(body=_("Time Off Request has been approved by %s and is now fully approved.") % (self.env.user.name,))
            message = f'Time Off Request has been approved by {self.env.user.name} and is now fully approved.'
            request.write({'internal_note': message})
            request.activity_feedback(['mail.mail_activity_data_todo'])
        else:
            for next_approver in next_approvals:
                request.activity_schedule('mail.mail_activity_data_todo', note=_('You have a new time off request to approve from %s.') % request.created_by.name, user_id=next_approver.approver.user_id.id)

        if request.status == '5':
            self._create_attendance_log()
            if request.request_type in ['1']:
                employee.write({
                    'last_leave_date': request.end_date
                })
            # # Delete the approval entries where the status is pending
            # approval_entries = self.env['payroll.approval.entries'].search([
            #     ('document_type', '=', '1'),
            #     ('document_id', '=', request.id),
            #     ('status', '=', '2')
            # ])
            # if approval_entries:
            #     approval_entries.sudo().unlink()

        

    def _create_attendance_log(self):
        for request in self:
            if request.request_id.request_type and request.request_id.request_type not in ['6', '7']:
                start_date = request.request_id.start_date
                end_date = request.request_id.end_date
                remaining_days = request.request_id.remaining_leave
                employee = self.env['payroll.employees'].search([('user_id', '=', self.env.user.id)], limit=1)
                requester = self.env['payroll.employees'].search([('user_id', '=', request.request_id.created_by.id)], limit=1)

                days_diff = (end_date - start_date).days + 1  # Calculate the number of days

                for day in range(days_diff):
                    current_date = start_date + timedelta(days=day)

                    if request.request_id.request_type == '2' and remaining_days > 0:
                        attendance_log = self.env['payroll.attendance.log'].search([
                            ('employee_id', '=', requester.id),
                            ('date', '=', current_date)
                        ], limit=1)

                        if attendance_log:
                            attendance_log.write({
                                'start_time': current_date,
                                'end_time': current_date,
                                'time_off_type': request.request_id.request_type,
                                'source': 'Time Off Request',
                                'source_id': request.request_id.id
                            })
                        else:
                            self.env['payroll.attendance.log'].create({
                                'nik': requester.nik,
                                'employee_id': requester.id,
                                'date': current_date,
                                'start_time': current_date,
                                'end_time': current_date,
                                'time_off_type': request.request_id.request_type,
                                'source': 'Time Off Request',
                                'source_id': request.request_id.id,
                                'department_id': requester.department_id.id
                            })
                        remaining_days -= 1  # Decrement remaining days

                    elif request.request_id.request_type == '2' and remaining_days <= 0:
                        requester_category = self.env['payroll.employee.categories'].search([
                            ('id', '=', requester.category_id.id)
                        ], limit=1)

                        if requester_category:
                            attendance_log = self.env['payroll.attendance.log'].search([
                                ('employee_id', '=', requester.id),
                                ('date', '=', current_date)
                            ], limit=1)

                            if attendance_log:
                                if not requester_category.over_sick_deduction_to or requester_category.over_sick_deduction_to == '1':
                                    attendance_log.unlink()
                                elif requester_category.over_sick_deduction_to == '2':
                                    attendance_log.write({
                                        'time_off_type': '3',
                                        'text': 'Permission Over Sick'
                                    })
                            else:
                                if requester_category.over_sick_deduction_to == '2':
                                    self.env['payroll.attendance.log'].create({
                                        'nik': requester.nik,
                                        'employee_id': requester.id,
                                        'date': current_date,
                                        'start_time': current_date,
                                        'end_time': current_date,
                                        'time_off_type': '3',
                                        'source': 'Time Off Request',
                                        'source_id': request.request_id.id,
                                        'text': 'Permission Over Sick',
                                        'department_id': requester.department_id.id
                                    })

                    else:
                        if request.request_id.duration > 0:
                            current_dates = start_date + timedelta(days=day)
                            user_tz = self.env.user.tz or 'UTC' 
                            local_tz = timezone(user_tz)
                            current_date = datetime.combine(
                                start_date + timedelta(days=day),
                                datetime.min.time() 
                            )
                            current_date_localized = local_tz.localize(current_date)  
                            current_date_utc = current_date_localized.astimezone(utc)

                            current_date_naive = current_date_utc.replace(tzinfo=None)
                            self.env['payroll.attendance.log'].create({
                                'nik': requester.nik,
                                'employee_id': requester.id,
                                'date': current_dates,
                                'time_off_type': request.request_id.request_type,
                                'source': 'Time Off Request',
                                'source_id': request.request_id.id,
                                'department_id': requester.department_id.id,
                                'start_time': current_date_naive,
                                'end_time': current_date_naive,
                            })                           

    def action_reject(self, reason):
        """
        This method will reject the time off request. It will notify the requestor and update the status of the request."""
        self.ensure_one()
        request = self.request_id
        employee = self.env['payroll.employees'].search([('user_id', '=', self.env.user.id)], limit=1)

        self.write({'has_approved': True, 'approver_date': fields.Date.today(), 'reason': reason})
        request.write({'status': '3'})
        request.activity_feedback(['mail.mail_activity_data_todo'])
        request.message_post(body=_("Time Off Request has been rejected by %s. Reason: %s") % (self.env.user.name, reason))
        reasons = reason if reason else "No Reason"
        message = f'Time Off Request has been rejected by {self.env.user.name}. Reason : {reasons}'
        request.write({'internal_note':message})

        # If status is rejected, delete attendance log
        attlog = self.env['payroll.attendance.log'].search([('employee_id', '=', employee.id), ('date', '>=', request.start_date), ('date', '<=', request.end_date), ('time_off_type', '=', request.request_type)])
        if attlog:
            attlog.unlink()

class PayrollTimeOffRejectWizard(models.TransientModel):
    _name = 'payroll.time.off.reject.wizard'
    _description = 'Time Off Reject Wizard'

    reason = fields.Text(string='Reason', required=True)
    request_id = fields.Many2one('payroll.time.off.request', string='Time Off Request')

    def action_reject(self):
        """
        This method will reject the time off request. It will notify the requestor and update the status of the request."""
        self.ensure_one()
        request = self.request_id
        request.ensure_one()
        
        current_user = self.env.user
        employee = self.env['payroll.employees'].search([('user_id', '=', current_user.id)], limit=1)

        if not employee:
            raise UserError(_('Employee not found!'))

        approval = request.time_off_request_approval_ids.filtered(lambda a: a.approver == employee and not a.has_approved)
        if not approval:
            raise UserError(_('No approval found for the current user or already approved.'))

        approval.write({'has_approved': True, 'approver_date': fields.Date.today(), 'reason': self.reason})
        request.write({'status': '3'})
        request.activity_feedback(['mail.mail_activity_data_todo'])
        request.message_post(body=_("Time Off Request has been rejected by %s. Reason: %s") % (self.env.user.name, self.reason))

        # If status is rejected, delete attendance log
        attlog = self.env['payroll.attendance.log'].search([('employee_id', '=', employee.id), ('date', '>=', request.start_date), ('date', '<=', request.end_date), ('time_off_type', '=', request.request_type)])
        if attlog:
            attlog.unlink()