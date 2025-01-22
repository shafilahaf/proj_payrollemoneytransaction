from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollAbsenceRegister(models.Model):
    _name = 'payroll.absence.register'
    _description = 'Absence Register'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, default='New', readonly=True)
    employee_id = fields.Many2one('payroll.employees', string='Employee', required=True)
    request_type = fields.Selection([
        ('2', 'Sick'),
        ('4', 'Day Off'),
        ('99', 'Absence'),
    ], string='Request Type')
    request_date = fields.Date(string='Request Date', default=fields.Date.today, readonly=True)
    absence_start_date = fields.Date(string='Start Date', required=True)
    absence_end_date = fields.Date(string='End date', required=True)
    duration = fields.Integer(string='Duration', readonly=True)
    remarks = fields.Text(string='Remarks')
    status = fields.Selection([
        ('1', 'Open'),
        ('5', 'Approved')
    ], string='Status', default='1', readonly=True)
    internal_notes = fields.Text(string='Internal Notes')

    @api.model
    def create(self, vals):
        """
        This method is called when creating a new record."""
        vals['name'] = self.env['ir.sequence'].next_by_code('payroll.absence.register') or 'New'
        vals['status'] = '5'
        return super(PayrollAbsenceRegister, self).create(vals)

    @api.onchange('absence_start_date', 'absence_end_date')
    def get_duration(self):
        """
        This method is called when the absence_start_date or absence_end_date field is changed."""
        for rec in self:
            if rec.absence_start_date and rec.absence_end_date:
                rec.duration = (rec.absence_end_date - rec.absence_start_date).days + 1

    def cancel_request(self):
        """
        This method is called when the cancel button is clicked."""
        self.status = '1'
        self.internal_notes = 'Request has been cancelled.'