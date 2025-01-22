from odoo import models, fields, api # type: ignore
from odoo.exceptions import UserError, ValidationError # type: ignore

class PayrollDeductions(models.Model):
    _name = 'payroll.deductions'
    _description = 'Payroll Deductions'
    _rec = 'name'

    name = fields.Char(string='Name', required=True)
    source = fields.Selection([
        ('1', 'Absen'),
        ('2', 'Mistake 1'),
        ('3', 'Mistake 2'),
        ('4', 'Absen Late'),
        ('5', 'Absen Not Check Out'),
        ('6', 'Permission'),
        ('7', 'Absen Late Layer 2'),
        ('8', 'Absen Late Layer 3'),
        ('9', 'Absen Late Layer 4'),
    ], string='Source')
    pro_rate = fields.Boolean(string='Pro Rate')
    ph_deduction_type = fields.Selection([
        ('1', 'Additional Adjustment'),
        ('2', 'Deduction Adjustment'),
        ('3', 'SSS'),
        ('4', 'PH Health'),
        ('5', 'PG'),
        ('6', 'SSS Loans'),
        ('7', 'Calamity Loans'),
        ('8', 'HDMF Loans'),
        ('9', 'Over Break Deduction'),
        ('10', 'Error')
    ], string='PH Deduction Type')
    active = fields.Boolean(string='Active', default=True)
    
    mistake_detail_ids = fields.One2many('payroll.mistake.detail', 'deduction_id', string='Mistake Details')
    