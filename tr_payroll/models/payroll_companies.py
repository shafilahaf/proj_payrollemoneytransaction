from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PayrollCompanies(models.Model):
    _name = 'payroll.companies'
    _description = 'Payroll Companies'
    _rec_name = 'name'
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         'Company name must be unique!'),
    ]

    name = fields.Char(string='Company Name', required=True)
    address = fields.Text(string='Address', required=True)
    address2 = fields.Text(string='Address 2')
    picture = fields.Binary(string='Logo')
    blocked = fields.Boolean(string='Blocked')
    active = fields.Boolean(string='Active', default=True)
    
    website_ids = fields.One2many('payroll.websites', 'companies_id', string='Websites')