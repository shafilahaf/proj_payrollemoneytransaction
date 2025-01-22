from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollEmployeeStatus(models.Model):
    _name = 'payroll.employee.status'
    _description = 'Employee Status'
    _rec = 'name'
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         'Employee status name must be unique!'),
    ]

    name = fields.Char(string='Name', required=True)
    duration = fields.Integer(string='Duration', required=True)
    active = fields.Boolean(string='Active', default=True)