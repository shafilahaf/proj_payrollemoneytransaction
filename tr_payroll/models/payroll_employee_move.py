from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollEmployeeMove(models.Model):
    _name = 'payroll.employee.move'
    _description = 'Payroll Employee Move'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True, default=lambda self: 'New')
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    employee_id = fields.Many2one('payroll.employees', string='Employee', required=True)
    location_from_id = fields.Many2one('payroll.device.department', string='Location From', readonly=True, required=True, store=True)
    location_to_id = fields.Many2one('payroll.device.department', string='Location To', required=True, domain="[('id', '!=', location_from_id)]")
    nik_from = fields.Char(string='NIK From', readonly=True, store=True)
    nik_to = fields.Char(string='NIK To')
    category_from_id = fields.Many2one('payroll.employee.categories', string='Category From', readonly=True, required=True, store=True)
    category_to_id = fields.Many2one('payroll.employee.categories', string='Category To', required=True)

    # Validation 

    @api.model
    def create(self, vals):
        """
        This method is called when creating a new record."""
        vals['name'] = self.env['ir.sequence'].next_by_code('payroll.employee.move') or 'New'
        employee = self.env['payroll.employees'].browse(vals['employee_id'])
        employee.write({
            'department_id': vals['location_to_id'],
            'nik': vals['nik_to'],
            'category_id': vals['category_to_id']
        })
        return super(PayrollEmployeeMove, self).create(vals)
    
    @api.onchange('employee_id')
    def get_nik_from(self):
        """
        This method is called when the employee_id field is changed."""
        for rec in self:
            if rec.employee_id:
                rec.nik_from = rec.employee_id.nik
                rec.location_from_id = rec.employee_id.department_id.id
                rec.category_from_id = rec.employee_id.category_id.id