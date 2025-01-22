from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollCurrencies(models.Model):
    _name = 'payroll.currencies'
    _description = 'Currencies'
    _rec_name = 'name'
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         'Currency name must be unique!'),
    ]

    name = fields.Char(string='Currency Name', required=True)
    currency_symbol = fields.Char(string='Currency Symbol', required=True)
    active = fields.Boolean(string='Active', default=True)
    
    rate_ids = fields.One2many('payroll.currencies.rate', 'currency_id', string='Rates')

class PayrollCurrenciesRate(models.Model):
    _name = 'payroll.currencies.rate'
    _description = 'Currencies Rate'

    start_date = fields.Date(string='Start Date', required=True)
    rate = fields.Float(string='Rate', required=True)

    currency_id = fields.Many2one('payroll.currencies', string='Currency', required=True, ondelete='cascade')