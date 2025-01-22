from odoo import models, fields, api # type: ignore
from odoo.exceptions import UserError, ValidationError # type: ignore

class PayrollPhHealth(models.Model):
    _name = 'payroll.ph.health'
    _description = 'PH Health'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, default='New', copy=False, readonly=True)
    start_amount = fields.Float(string='Start Amount')
    end_amount = fields.Float(string='End Amount')
    compensation_range = fields.Float(string='Compensation Range')
    tax_rate_percent = fields.Float(string='Tax Rate Percent')
    prescribed_wtx = fields.Float(string='Prescribed WTX')

    @api.model
    def create(self, vals):
        """
        This method is called when creating a new record."""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('payroll.ph.health') or 'New'
        return super(PayrollPhHealth, self).create(vals)