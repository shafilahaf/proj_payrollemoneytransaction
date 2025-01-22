from odoo import models, fields, api #type: ignore
from odoo.exceptions import UserError, ValidationError #type: ignore

class PayrollSalaryComponents(models.Model):
    _name = 'payroll.salary.components'
    _description = 'Payroll Salary Components'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    is_basic_salary = fields.Boolean(string='Is Basic Salary')
    ph_salary_type = fields.Selection([
        ('1', 'Over Time'),
        ('2', 'Allowance'),
    ], string='PH Salary Type')
    active = fields.Boolean(string='Active', default=True)