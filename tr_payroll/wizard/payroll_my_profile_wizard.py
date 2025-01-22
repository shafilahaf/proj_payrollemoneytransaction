from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PayrollMyProfileWizard(models.TransientModel):
    _name = "payroll.my.profile.wizard"
    _description = "User Profile"
    _transient = True

    department_ids = fields.Many2many(comodel_name='payroll.device.department', string='Departments')
    employee_category_ids = fields.Many2many(comodel_name='payroll.employee.categories', string='Employee Categories')
    
    payroll_employee_id = fields.Many2one('payroll.employees', string='Employee')
    payroll_positions_level = fields.Integer(related='payroll_employee_id.current_position.level', string='Position Level', store=True)
    # user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    user_id = fields.Many2one('res.users', string='User')
    
    payroll_employee_name = fields.Char(string='Employee Name', related='payroll_employee_id.name')
    payroll_nik = fields.Char(string='NIK', related='payroll_employee_id.nik')
    payroll_manager_id = fields.Many2one('payroll.employees', string='Manager', related='payroll_employee_id.manager_id')
    payroll_active_date = fields.Date(string='Active Date', related='payroll_employee_id.active_date')
    payroll_inactive_date = fields.Date(string='Inactive Date',related='payroll_employee_id.inactive_date')
    payroll_working_status = fields.Selection([
                                ('1', 'Active'),
                                ('2', 'Inactive'),
                                ('3', 'Terminated'),
                            ], string='Working Status',related='payroll_employee_id.working_status')
    payroll_employee_status_id =  fields.Many2one('payroll.employee.status', string='Employee Status',related='payroll_employee_id.employee_status_id')
    payroll_company_id = fields.Many2one('payroll.companies', string='Company', related='payroll_employee_id.company_id')
    payroll_category_id = fields.Many2one('payroll.employee.categories', string='Category', related='payroll_employee_id.category_id')
    payroll_current_position = fields.Many2one('payroll.positions', string='Current Position', related='payroll_employee_id.current_position')
    payroll_last_leave_date = fields.Date(string='Last Leave Date', related='payroll_employee_id.last_leave_date')
    payroll_contract_id = fields.Many2one('payroll.contracts', string='Contract', related='payroll_employee_id.contract_id')
    payroll_contract_start_date = fields.Date(string='Contract Start Date', related='payroll_employee_id.contract_start_date')
    payoll_contract_end_date = fields.Date(string='Contract End Date', related='payroll_employee_id.contract_end_date')
    payroll_current_website = fields.Many2one('payroll.websites', string='Current Website',related='payroll_employee_id.current_website')
    payroll_department_id = fields.Many2one('payroll.device.department', string='Department', related='payroll_employee_id.department_id')
    payroll_case_of_inactivity = fields.Char(string='Case of Inactivity', related='payroll_employee_id.case_of_inactivity')

    payroll_address = fields.Text(string='Address', store=True)
    payroll_address_2 = fields.Text(string='Address 2', store=True)
    payroll_phone = fields.Char(string='Phone', store=True)
    payroll_email = fields.Char(string='Email', store=True)
    payroll_emergency_contact = fields.Char(string='Emergency Contact', store=True)
    payroll_emergency_phone = fields.Char(string='Emergency Phone', store=True)
    payroll_gender = fields.Selection([
        ('1', 'Male'),
        ('2', 'Female')
    ], string='Gender', store=True)
    payroll_date_of_birth = fields.Date(string='Date of Birth', store=True)
    payroll_country_id = fields.Many2one('payroll.countries', string='Country of Birth', store=True)
    payroll_city_id = fields.Many2one('payroll.cities', string='City of Birth', domain="[('countries_id', '=', payroll_country_id)]", store=True)
    payroll_visa_number = fields.Char(string='Visa Number', store=True)
    payroll_visa_expire_date = fields.Date(string='Visa Expire Date', store=True)
    payroll_passport_number = fields.Char(string='Passport Number', store=True)
    payroll_passport_expire_date = fields.Date(string='Passport Expire Date', store=True)
    payroll_bank_id = fields.Many2one('payroll.banks', string='Bank', store=True)
    payroll_bank_account_number = fields.Char(string='Bank Account Number', store=True)
    payroll_username = fields.Char(string="Username")

    ir_action_wizard_id = fields.Integer(string="IR ACTION WIZARD", compute="_compute_ir_action_wizard_id")
    value_ir_action_wizard = fields.Integer(string="Value IR ACTION", compute="_compute_value_ir_action_wizard")

    @api.depends('ir_action_wizard_id')
    def _compute_value_ir_action_wizard(self):
        for record in self:
            record.value_ir_action_wizard = record.ir_action_wizard_id


    @api.depends('payroll_employee_name')
    def _compute_ir_action_wizard_id(self):
        action = self.env['ir.actions.act_window'].sudo().search([('name', '=', 'My Profile Wizard')], limit=1)
        if action:
            self.ir_action_wizard_id = action.id
        else:
            self.ir_action_wizard_id = False

    @api.model
    def default_get(self, fields_list):
        """Auto-fill fields based on the logged-in user's employee record."""
        defaults = super(PayrollMyProfileWizard, self).default_get(fields_list)
        user = self.env.user

        # Try to get the employee linked to the logged-in user
        employee = self.env['payroll.employees'].search([('user_id', '=', user.id)], limit=1)

        # If employee exists, fill the fields
        if employee:
            related_fields = {
                'payroll_employee_id': employee.id,
                'payroll_employee_name': employee.name,
                'payroll_nik': employee.nik,
                'payroll_manager_id': employee.manager_id.id,
                'payroll_active_date': employee.active_date,
                'payroll_inactive_date': employee.inactive_date,
                'payroll_working_status': employee.working_status,
                'payroll_employee_status_id': employee.employee_status_id.id,
                'payroll_company_id': employee.company_id.id,
                'payroll_category_id': employee.category_id.id,
                'payroll_current_position': employee.current_position.id,
                'payroll_last_leave_date': employee.last_leave_date,
                'payroll_contract_id': employee.contract_id.id,
                'payroll_contract_start_date': employee.contract_start_date,
                'payoll_contract_end_date': employee.contract_end_date,
                'payroll_current_website': employee.current_website.id,
                'payroll_department_id': employee.department_id.id,
                'payroll_case_of_inactivity': employee.case_of_inactivity,
                'payroll_address': employee.address,
                'payroll_address_2': employee.address_2,
                'payroll_phone': employee.phone,
                'payroll_email': employee.email,
                'payroll_emergency_contact': employee.emergency_contact,
                'payroll_emergency_phone': employee.emergency_phone,
                'payroll_gender': employee.gender,
                'payroll_date_of_birth': employee.date_of_birth,
                'payroll_country_id': employee.country_id.id,
                'payroll_city_id': employee.city_id.id,
                'payroll_visa_number': employee.visa_number,
                'payroll_visa_expire_date': employee.visa_expire_date,
                'payroll_passport_number': employee.passport_number,
                'payroll_passport_expire_date': employee.passport_expire_date,
                'payroll_bank_id': employee.bank_id.id,
                'payroll_bank_account_number': employee.bank_account_number,
                'payroll_username': user.login,  # Assuming login should be auto-filled from user
            }
            defaults.update(related_fields)
        return defaults

    def action_save(self):
        if self.payroll_username:
            self.payroll_employee_id.username = self.payroll_username
        else:
            raise UserError('Please provide a valid username')
        
        return {
            'type': 'ir.actions.act_window_close',
        }

    def action_open_password_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Password',
            'res_model': 'res.users.password.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_user_id': self.id,
            },
        }