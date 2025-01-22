from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollContracts(models.Model):
    _name = 'payroll.contracts'
    _description = 'Payroll Contracts'
    _rec_name = 'name'
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         'Contract name must be unique!'),
    ]

    name = fields.Char(string='Contract Name', required=True)
    period = fields.Integer(string='Period', required=True)
    active = fields.Boolean(string='Active', default=True)