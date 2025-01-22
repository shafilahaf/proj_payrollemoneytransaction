from odoo import models, fields, api # type: ignore
from odoo.exceptions import UserError, ValidationError # type: ignore

class PayrollConvertAttTOR(models.TransientModel):
    _name = 'payroll.convert.att.tor'
    _description = 'Payroll Convert Attendance To TOR'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    employee_id = fields.Many2one('payroll.employees', string='Employee')

    def convert_attlog_tor(self):
        domain = []

        if self.employee_id:
            domain.append(('employee_id', '=', self.employee_id.id))
        if self.start_date:
            domain.append(('date', '>=', self.start_date))
        if self.end_date:
            domain.append(('date', '<=', self.end_date))

        domain

        att_logs = self.env['payroll.attendance.log'].search(domain)