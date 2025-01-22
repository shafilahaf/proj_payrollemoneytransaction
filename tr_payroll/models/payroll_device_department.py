from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PayrollDeviceDepartment(models.Model):
    _name = 'payroll.device.department'
    _description = 'Payroll Device Department'
    _rec_name = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Department name must be unique!')
    ]

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=True)