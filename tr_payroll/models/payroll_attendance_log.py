from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollAttendanceLog(models.Model):
    _name = 'payroll.attendance.log'
    _description = 'Attendance Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    employee_id = fields.Many2one('payroll.employees', string='Employee', required=True ,track_visibility='onchange')
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today,track_visibility='onchange')
    start_time = fields.Datetime(string='Start Time',track_visibility='onchange')
    end_time = fields.Datetime(string='End Time',track_visibility='onchange')
    shift_id = fields.Many2one('payroll.shifts', string='Shift',track_visibility='onchange')
    working_hours = fields.Float(string='Working Hours', store=True, compute='_compute_working_hours',track_visibility='onchange')
    is_latelog = fields.Boolean(string='Late',track_visibility='onchange')
    source = fields.Char(string='Source',track_visibility='onchange')
    source_id = fields.Char(string='Source ID',track_visibility='onchange')
    is_manual = fields.Boolean(string='Manual',track_visibility='onchange')
    is_late_2 = fields.Boolean(string='Late 2',track_visibility='onchange')
    weekday = fields.Integer(string='Weekday',track_visibility='onchange')
    holiday = fields.Many2one('payroll.holiday', string='Holiday',track_visibility='onchange')
    late_minutes = fields.Float(string='Late Minutes',track_visibility='onchange')
    is_night_diff = fields.Boolean(string='Night Differential',track_visibility='onchange')
    ph_points = fields.Float(string='PH Points',track_visibility='onchange')
    ot_hours = fields.Float(string='OT Hours',track_visibility='onchange')
    ot_points = fields.Float(string='OT Points',track_visibility='onchange')
    is_late_3 = fields.Boolean(string='Late 3',track_visibility='onchange')
    is_late_4 = fields.Boolean(string='Late 4',track_visibility='onchange')
    nik = fields.Char(string='NIK',track_visibility='onchange')
    department_id = fields.Many2one('payroll.device.department', string='Department',track_visibility='onchange', required=True)
    # dashboard_id = fields.Many2one('tr.payroll.dashboard.staff', string='Payroll Dashboard', ondelete='cascade')
    status = fields.Char(string='Status',track_visibility='onchange')
    holiday_type = fields.Selection([
        ('1', 'LH'),
        ('2', 'SH')
    ], string='Holiday Type', store=True,track_visibility='onchange')
    time_off_type = fields.Selection([
        ('1', 'Leave'),
        ('2', 'Sick'),
        ('3', 'Permission'),
        ('4', 'Day Off'),
        ('5', 'Device Error'),
        ('6', 'Not Taken Leave'),
        ('7', 'Medical Reimburment W/O Off'),
        ('99', 'Absence'),
    ], string='Time Off Type',track_visibility='onchange')
    PH_point = fields.Float(string='PH Point',track_visibility='onchange')
    ot_points = fields.Float(string='OT Point',track_visibility='onchange')
    ot_hours = fields.Float(string='OT Hours',track_visibility='onchange')
    text = fields.Char(string="Text/Description",track_visibility='onchange', readonly=True, store=True)

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

        # domain = []
        # if allowed_departments and allowed_categories:
        #     for dept in allowed_departments:
        #         for cat in allowed_categories:
        #             domain += ['|',('department_id', '=', dept), ('employee_id.category_id', '=', cat)]
        # elif allowed_departments:
        #     for dept in allowed_departments:
        #         domain += [('department_id', '=', dept)]
        # elif allowed_categories:
        #     for cat in allowed_categories:
        #         domain += [('employee_id.category_id', '=', cat)]

        # Domain hardcode 
        # domain = [('department_id', 'in', [9, 12])]
        domain = []
        if allowed_departments and allowed_categories:
            domain = ['|', ('department_id', 'in', allowed_departments), ('employee_id.category_id', 'in', allowed_categories)]
        elif allowed_departments:
            domain = [('department_id', 'in', allowed_departments)]
        elif allowed_categories:
            domain = [('employee_id.category_id', 'in', allowed_categories)]

        if domain:
            args += domain

        return super(PayrollAttendanceLog, self).search(args, offset=offset, limit=limit, order=order, count=count)



    @api.depends('start_time', 'end_time')
    def _compute_working_hours(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                rec.working_hours = (rec.end_time - rec.start_time).total_seconds() / 3600.0
            else:
                rec.working_hours = 0.0

    @api.onchange('holiday')
    def _onchange_holiday(self):
        if self.holiday:
            self.holiday_type = self.holiday.type

    def _get_time_off_type_label(self):
        return dict(self._fields['time_off_type'].selection).get(self.time_off_type, '')
    
    @api.onchange('employee_id')
    def _onchange_employee(self):
        if self.employee_id:
            # Check if employee exists
            if not self.employee_id.exists():
                raise UserError("The selected employee does not exist.")
            
    @api.model
    def create(self, vals):
        existing_record = self.search([
            ('employee_id', '=', vals.get('employee_id')),
            ('date', '=', vals.get('date')),
            ('start_time', '=', vals.get('start_time')),
            ('end_time', '=', vals.get('end_time')),
            ('nik', '=', vals.get('nik')),
            ('department_id', '=', vals.get('department_id'))
        ], limit=1)
        
        if existing_record:
            return existing_record
        
        return super(PayrollAttendanceLog, self).create(vals)

