from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PayrollShifts(models.Model):
    _name = 'payroll.shifts'
    _description = 'Payroll Shifts'
    _rec_name = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Shift name must be unique!')
    ]

    name = fields.Char(string='Name', required=True)
    start_time = fields.Float(string='Start Time', required=True)
    duration = fields.Integer(string='Duration', required=True)
    timezone = fields.Char(string='Timezone', required=True)
    is_night_diff = fields.Boolean(string='Is Night Differential')
    color = fields.Integer(string='Color')
    color2 = fields.Char(string='Hex Color')
    active = fields.Boolean(string='Active', default=True)

    def get_shift_by_date(self, date):
        shift = self.search([('start_time', '<=', date.hour), ('duration', '>=', date.hour)], limit=1)
        if not shift:
            raise UserError('Shift not found')
        return shift.id