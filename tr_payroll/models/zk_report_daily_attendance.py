from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollZKReportDailyAttInherit(models.Model):
    _inherit = 'zk.report.daily.attendance'

    device_department_id = fields.Many2one('payroll.device.department', string='Department')