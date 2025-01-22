from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollMistakeDetail(models.Model):
    _name = 'payroll.mistake.detail'
    _description = 'Payroll Mistake Detail'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    deduction_id = fields.Many2one('payroll.deductions', string='Deduction')
    deduction_name = fields.Char(string='Deduction Name', related='deduction_id.name', store=True)
    default_amount = fields.Float(string='Default Amount')
    categories_id = fields.Many2one('payroll.employee.categories', string='Employee Category')
    currency_id = fields.Many2one('payroll.currencies', string='Currency')
    deduction_source = fields.Selection([
        ('1', 'Absen'),
        ('2', 'Mistake 1'),
        ('3', 'Mistake 2'),
        ('4', 'Absen Late'),
        ('5', 'Absen Not Check Out'),
        ('6', 'Permission'),
        ('7', 'Absen Late Layer 2'),
        ('8', 'Absen Late Layer 3'),
        ('9', 'Absen Late Layer 4'),
    ], string='Source', related='deduction_id.source', store=True)
