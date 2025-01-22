from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollWebsites(models.Model):
    _name = 'payroll.websites'
    _description = 'Payroll Websites'
    _rec_name = 'name'

    name = fields.Char(string='Website Name')
    companies_id = fields.Many2one('payroll.companies', string='Company', required=True, ondelete='cascade')