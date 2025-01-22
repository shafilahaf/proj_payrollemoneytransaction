from odoo import models, fields, api

class ResGroupsInherit(models.Model):
    _inherit = 'res.groups'

    is_active = fields.Boolean(string="Active", default=True)
    can_edit_mistake_entries = fields.Boolean(string="Can Edit Release Mistake Entry", default=False)
    permitted_edit_nik_dept = fields.Boolean(string="Can Edit NIK and Department", default=False)

    department_ids = fields.Many2many("payroll.device.department", string="Departments")
    categories_ids = fields.Many2many('payroll.employee.categories', string="Categories")

    def action_unlink_group_users(self):
        for group in self:
            if group.is_active: 
                users_to_unlink = group.users 
                if users_to_unlink:
                    for user in users_to_unlink:
                        user.groups_id = [(3, group.id)]

    def toggle_permission(self):
        """Enable or disable edit permission for NIK and Department."""
        for group in self:
            group.permitted_edit_nik_dept = not group.permitted_edit_nik_dept
