from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollRestrict(models.Model):
    _name = 'payroll.restrict'
    _description = 'Payroll Restrict'
    _rec_name = 'users'

    users = fields.Many2one('res.users', string='Users', readonly=True)
    employee_id = fields.Many2one('payroll.employees', string='Employee', readonly=True)
    position = fields.Many2one('payroll.positions', string='Employee Position', readonly=True, related='employee_id.current_position')
    department_id = fields.Many2one(
        "payroll.device.department", string="Department", related='employee_id.department_id'
    )
    category_id = fields.Many2one(
        "payroll.employee.categories", string="Category", related='employee_id.category_id'
    )
    department_ids = fields.Many2many('payroll.device.department', string='Permitted Departments')
    category_ids = fields.Many2many('payroll.employee.categories', string='Permitted Categories')

    def _upgrade_module(self):
        module = self.env['ir.module.module'].search([('name', '=', 'tr_payroll')], limit=1)
        if module:
            if module.state == 'installed':
                module.button_immediate_upgrade()

    def get_all_users(self):
        all_users = self.env['res.users'].search([])
        for user in all_users:
            if not self.env['payroll.restrict'].search([('users', '=', user.id)]):
                self.env['payroll.restrict'].create({
                    'users': user.id, 
                    'department_ids': user.department_ids.ids, 
                    'category_ids': user.employee_category_ids.ids,
                    'employee_id': user.payroll_employee_id.id,
                })
            else:
                restrict = self.env['payroll.restrict'].search([('users', '=', user.id)], limit=1)
                restrict.department_ids = user.department_ids
                restrict.category_ids = user.employee_category_ids
                restrict.employee_id = user.payroll_employee_id.id

    def change_user(self):
        for user in self:
            user.users.department_ids = user.department_ids
            user.users.employee_category_ids = user.category_ids

    @api.model
    def create(self, vals):
        res = super(PayrollRestrict, self).create(vals)
        res.change_user()
        # res._upgrade_module()
        return res
    
    def write(self, vals):
        res = super(PayrollRestrict, self).write(vals)
        self.change_user()
        # self._upgrade_module()
        return res
        