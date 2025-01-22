from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

class PayrollSalaryAdjustmentHeader(models.Model):
    _name = 'payroll.salary.adjustment.header'
    _description = 'Salary Adjustment'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, default='New', readonly=True)
    adjustment_date = fields.Date(string='Adjustment Date', default=fields.Date.today)
    department_id = fields.Many2one('payroll.device.department', string='Department', required=True)
    category_id = fields.Many2one('payroll.employee.categories', string='Category', required=True)
    salary_adjustment_detail_ids = fields.One2many('payroll.salary.adjustment.detail', 'header_id', string='Salary Adjustment Detail')

    status = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], string='Status', default='draft')

    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        user_groups = user.groups_id

        allowed_departments = []
        allowed_categories = []

        for group in user_groups:
            if group.is_active:
                allowed_departments += group.department_ids.ids
                allowed_categories += group.categories_ids.ids

        domain = [] 
        
        # if allowed_departments and allowed_categories:
        #     for dept in allowed_departments:
        #         for cat in allowed_categories:
        #             domain += ['|',('department_id', '=', dept), ('category_id', '=', cat)]
        # elif allowed_departments:
        #     for dept in allowed_departments:
        #         domain += [('department_id', '=', dept)]
        # elif allowed_categories:
        #     for cat in allowed_categories:
        #         domain += [('category_id', '=', cat)]

        domain = []
        if allowed_departments and allowed_categories:
            domain = ['|', ('department_id', 'in', allowed_departments), ('category_id', 'in', allowed_categories)]
        elif allowed_departments:
            domain = [('department_id', 'in', allowed_departments)]
        elif allowed_categories:
            domain = [('category_id', 'in', allowed_categories)]

        if domain:
            args += domain

        return super(PayrollSalaryAdjustmentHeader, self).search(args, offset, limit, order, count)
    
    @api.model
    def create(self, vals):
        """
        This method is called when creating a new record."""
        vals['name'] = self.env['ir.sequence'].next_by_code('payroll.salary.adjustment.header') or 'New'
        return super(PayrollSalaryAdjustmentHeader, self).create(vals)
    
    def action_done(self):
        """
        This method will update the basic salary of the employees based on the salary adjustment detail."""
        for record in self:
            if not record.salary_adjustment_detail_ids:
                raise UserError(_('Please add at least one employee to proceed.'))
            
            for detail in record.salary_adjustment_detail_ids:
                # Change basic salary of employee amount to the new amount
                basic_salary = self.env['payroll.employee.salary'].search([
                    ('employee_id', '=', detail.employee_id.id),
                    ('is_basic_salary', '=', True),
                ], limit=1)
                basic_salary.amount = detail.total_salary
                basic_salary.last_increment_salary_date = record.adjustment_date
                basic_salary.last_increment_salary_amount = detail.adjustment_amount
                
            record.status = 'done'

    def add_eligible_employees(self):
        """
        Add employees to the salary adjustment detail if they have been active for more than six months and haven't been adjusted in the last six months.
        """
        six_months_ago = fields.Date.today() - relativedelta(months=6)
        basic_salary_component_id = self.env['payroll.salary.components'].search([('is_basic_salary', '=', True)], limit=1).id

        employees = self.env['payroll.employees'].search([
            ('department_id', '=', self.department_id.id),
            ('category_id', '=', self.category_id.id),
            ('active_date', '<=', six_months_ago),
            ('working_status', '=', '1'),
        ])
        
        for employee in employees:
            # Find the latest salary adjustment date
            latest_adjustment = self.env['payroll.salary.adjustment.detail'].search([
                ('employee_id', '=', employee.id)
            ], order='create_date desc', limit=1)
            
            if latest_adjustment:
                last_adjustment_date = latest_adjustment.header_id.adjustment_date
                last_adjustment_date = fields.Date.from_string(last_adjustment_date) + relativedelta(months=6)
            else:
                last_adjustment_date = employee.active_date + relativedelta(months=6)

            # Check if the employee is eligible for adjustment
            if fields.Date.today() >= last_adjustment_date:
                current_basic_salary = self.env['payroll.employee.salary'].search([
                    ('employee_id', '=', employee.id),
                    ('salary_component_id', '=', basic_salary_component_id)
                ], limit=1).amount

                self.salary_adjustment_detail_ids.create({
                    'header_id': self.id,
                    'employee_id': employee.id,
                    'employee_basic_salary': current_basic_salary,
                    'adjustment_type': '1',  # Assuming '1' is for increment
                    'adjustment_amount': 0,  # You can set the default adjustment amount here
                    'adjustment_reason': '',
                })

class PayrollSalaryAdjustmentDetail(models.Model):
    _name = 'payroll.salary.adjustment.detail'
    _description = 'Salary Adjustment Detail'

    header_id = fields.Many2one('payroll.salary.adjustment.header', string='Header', ondelete='cascade')
    employee_id = fields.Many2one('payroll.employees', string='Employee', required=True, domain=lambda self: self._get_employee_domain())
    employee_basic_salary = fields.Float(string='Employee Basic Salary', required=True, store=True)
    adjustment_type = fields.Selection([
        ('1', 'Salary Increment'),
        ('2', 'Salary Decrement'),
    ], string='Adjustment Type', required=True)
    adjustment_amount = fields.Float(string='Adjustment Amount', required=True)
    adjustment_reason = fields.Text(string='Adjustment Reason')
    total_salary = fields.Float(string='Total Salary', compute='_compute_total_salary', store=True)

    

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        This method is called when the employee_id field is changed."""
        basic_salary = self.env['payroll.employee.salary'].search([
            ('employee_id', '=', self.employee_id.id),
            ('is_basic_salary', '=', True),
        ], limit=1).amount
        self.employee_basic_salary = basic_salary

    @api.depends('employee_basic_salary', 'adjustment_amount')
    def _compute_total_salary(self):
        """
        This method will compute the total salary based on the adjustment type."""
        for record in self:
            if record.adjustment_type == '1':
                record.total_salary = record.employee_basic_salary + record.adjustment_amount
            elif record.adjustment_type == '2':
                record.total_salary = record.employee_basic_salary - record.adjustment_amount

    @api.depends('header_id')
    def _get_employee_domain(self):
        """
        This method will return the domain for the employee_id field based on the header_id field."""
        for record in self:
            domain = []
            if record.header_id:
                domain = [
                    ('department_id', '=', record.header_id.department_id.id),
                    ('category_id', '=', record.header_id.category_id.id)
                ]
            return domain

    @api.model
    def default_get(self, fields):
        """
        This method will set the default values for the fields."""
        res = super(PayrollSalaryAdjustmentDetail, self).default_get(fields)
        header_id = self._context.get('default_header_id')
        if header_id:
            header = self.env['payroll.salary.adjustment.header'].browse(header_id)
            res.update({
                'employee_id': self.env['payroll.employee'].search([
                    ('department_id', '=', header.department_id.id),
                    ('category_id', '=', header.category_id.id)
                ], limit=1).id
            })
        return res
    
    @api.depends('employee_basic_salary', 'adjustment_amount')
    def _compute_total_salary(self):
        """
        This method will compute the total salary based on the adjustment type."""
        for record in self:
            record.total_salary = record.employee_basic_salary + record.adjustment_amount
