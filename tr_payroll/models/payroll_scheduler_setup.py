from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollSchedulerSetup(models.Model):
    _name = 'payroll.scheduler.setup'
    _description = 'Scheduler Setup'

    attendance_interval = fields.Integer(string='Attendance Interval', required=True, default=1)
    last_run = fields.Datetime(string='Last Run', readonly=True)
    default_category_employee = fields.Many2one('payroll.employee.categories', string='Default Category Employee', required=True)
    default_position_employee = fields.Many2one('payroll.positions', string='Default Position Employee', required=True)
    default_contract_employee = fields.Many2one('payroll.contracts', string='Default Contract Employee', required=True)
    default_website_employee = fields.Many2one('payroll.websites', string='Default Website Employee', required=True)
    default_company_employee = fields.Many2one('payroll.companies', string='Default Company Employee', required=True)