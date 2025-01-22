from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollCountries(models.Model):
    _name = 'payroll.countries'
    _description = 'Countries'
    _rec_name = 'name'
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         'Country name must be unique!'),
    ]

    name = fields.Char(string='Country Name', required=True)
    active = fields.Boolean(string='Active', default=True)
    
    city_ids = fields.One2many('payroll.cities', 'countries_id', string='Cities')
    
class PayrollCities(models.Model):
    _name = 'payroll.cities'
    _description = 'Cities'
    _rec_name = 'name'
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         'City name must be unique!'),
    ]

    name = fields.Char(string='City Name')
    countries_id = fields.Many2one('payroll.countries', string='Country', required=True, ondelete='cascade')