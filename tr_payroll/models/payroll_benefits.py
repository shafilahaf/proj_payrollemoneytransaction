from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollBenefits(models.Model):
    _name = 'payroll.benefits'
    _description = 'Benefits'
    _rec_name = 'name'

    type = fields.Selection([
        ('3', 'Medical'),
        ('4', 'Allowance'),
    ], string='Type', required=True)
    name = fields.Char(string='Benefit Name', required=True)
    active = fields.Boolean(string='Active', default=True)