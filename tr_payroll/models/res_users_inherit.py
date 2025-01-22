from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    department_ids = fields.Many2many(comodel_name='payroll.device.department', string='Departments')
    employee_category_ids = fields.Many2many(comodel_name='payroll.employee.categories', string='Employee Categories')
    payroll_employee_id = fields.Many2one('payroll.employees', string='Employee')
    payroll_positions_level = fields.Integer(related='payroll_employee_id.current_position.level', string='Position Level', store=True)
    
    
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

    @api.constrains('groups_id')
    def _check_active_groups(self):
        for user in self:
            all_groups = user.groups_id
            inactive_groups = user.groups_id.filtered(lambda g: not g.is_active)

            if inactive_groups:
                group_names = ', '.join(inactive_groups.mapped('name'))
                raise ValidationError(f"The following groups are inactive and cannot be assigned to : {group_names}")

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        
        if self.payroll_employee_id:
            employee = self.payroll_employee_id
            updates = {}

            if 'payroll_address' in vals:
                updates['address'] = self.payroll_address
            if 'payroll_address_2' in vals:
                updates['address_2'] = self.payroll_address_2
            if 'payroll_phone' in vals:
                updates['phone'] = self.payroll_phone
            if 'payroll_email' in vals:
                updates['email'] = self.payroll_email
            if 'payroll_emergency_contact' in vals:
                updates['emergency_contact'] = self.payroll_emergency_contact
            if 'payroll_emergency_phone' in vals:
                updates['emergency_phone'] = self.payroll_emergency_phone
            if 'payroll_gender' in vals:
                updates['gender'] = self.payroll_gender
            if 'payroll_date_of_birth' in vals:
                updates['date_of_birth'] = self.payroll_date_of_birth
            if 'payroll_country_id' in vals:
                updates['country_id'] = self.payroll_country_id.id
            if 'payroll_city_id' in vals:
                updates['city_id'] = self.payroll_city_id.id
            if 'payroll_visa_number' in vals:
                updates['visa_number'] = self.payroll_visa_number
            if 'payroll_visa_expire_date' in vals:
                updates['visa_expire_date'] = self.payroll_visa_expire_date
            if 'payroll_passport_number' in vals:
                updates['passport_number'] = self.payroll_passport_number
            if 'payroll_passport_expire_date' in vals:
                updates['passport_expire_date'] = self.payroll_passport_expire_date
            if 'payroll_bank_id' in vals:
                updates['bank_id'] = self.payroll_bank_id.id
            if 'payroll_bank_account_number' in vals:
                updates['bank_account_number'] = self.payroll_bank_account_number
            if 'payroll_username' in vals:
                updates['username'] = self.payroll_username

            if updates:
                employee.write(updates)

        return res

    
    @api.depends('payroll_employee_id')
    def _compute_payroll_employee_info(self):
        for rec in self:
            if rec.payroll_employee_id:
                rec.payroll_address = rec.payroll_employee_id.address
                rec.payroll_address_2 = rec.payroll_employee_id.address_2
                rec.payroll_phone = rec.payroll_employee_id.phone
                rec.payroll_email = rec.payroll_employee_id.email
                rec.payroll_emergency_contact = rec.payroll_employee_id.emergency_contact
                rec.payroll_emergency_phone = rec.payroll_employee_id.emergency_phone
                rec.payroll_gender = rec.payroll_employee_id.gender
                rec.payroll_date_of_birth = rec.payroll_employee_id.date_of_birth
                rec.payroll_country_id = rec.payroll_employee_id.country_id
                rec.payroll_city_id = rec.payroll_employee_id.city_id
                rec.payroll_visa_number = rec.payroll_employee_id.visa_number
                rec.payroll_visa_expire_date = rec.payroll_employee_id.visa_expire_date
                rec.payroll_passport_number = rec.payroll_employee_id.passport_number
                rec.payroll_passport_expire_date = rec.payroll_employee_id.passport_expire_date
                rec.payroll_bank_id = rec.payroll_employee_id.bank_id
                rec.payroll_bank_account_number = rec.payroll_employee_id.bank_account_number
            else:
                rec.payroll_address = False
                rec.payroll_address_2 = False
                rec.payroll_phone = False
                rec.payroll_email = False
                rec.payroll_emergency_contact = False
                rec.payroll_emergency_phone = False
                rec.payroll_gender = False
                rec.payroll_date_of_birth = False
                rec.payroll_country_id = False
                rec.payroll_city_id = False
                rec.payroll_visa_number = False
                rec.payroll_visa_expire_date = False
                rec.payroll_passport_number = False
                rec.payroll_passport_expire_date = False
                rec.payroll_bank_id = False
                rec.payroll_bank_account_number = False

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
