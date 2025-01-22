from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollBanks(models.Model):
    _name = 'payroll.banks'
    _description = 'Banks'
    _rec_name = 'name'
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         'Bank name must be unique!'),
    ]

    name = fields.Char(string='Bank Name', required=True)
    active = fields.Boolean(string='Active', default=True)