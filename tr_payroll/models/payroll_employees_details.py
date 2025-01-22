from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

class PayrollEmpDetails(models.Model):
    _name = "payroll.employee.details"
    _description = "Employee Details"

    type = fields.Char(string="Type")
    calculation_date = fields.Date(
        string="Calculation Date", readonly=True
    )
    active_date = fields.Date(string="Active Date")
    expired_date = fields.Date(string="Expired Date")
    quantity = fields.Integer(string="Quantity")
    currency = fields.Many2one("payroll.currencies", string="Currency")
    amount = fields.Float(string="Amount")
    isActive = fields.Boolean(string="Status")
    employee_id = fields.Many2one("payroll.employees", string="Employee")
    date = fields.Date(string="Date")
    type_text = fields.Char(string="Type Text")
    type_id = fields.Integer(string="Type ID")
    user_id_employee = fields.Many2one("res.users", string="User", related='employee_id.user_id', store=True)
    last_leave_date = fields.Date(string='Last Leave Date', related='employee_id.last_leave_date', store=True)