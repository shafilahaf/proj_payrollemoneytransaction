from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollEmployeeAppraisalsSetupHeader(models.Model):
    _name = 'payroll.emp.appraisals.setup.header'
    _description = 'Payroll Employee Appraisals Setup Header'
    _rec_name = 'title'

    title = fields.Char(string="Title", required=True)
    category_id = fields.Many2one('payroll.employee.categories', string='Category', required=True)
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    active_appraisal = fields.Boolean(string="Active")

    appraisal_line_ids = fields.One2many('payroll.emp.appraisals.setup.line', 'appraisal_header_id', string='Appraisal Lines')

    @api.constrains('active_appraisal')
    def _check_active_appraisal(self):
        """
        This method will check if there is more than one active appraisal per category."""
        for record in self:
            if record.active_appraisal:
                active_appraisals = self.search([('category_id', '=', record.category_id.id), ('active_appraisal', '=', True)])
                if len(active_appraisals) > 1:
                    raise ValidationError("Only one active appraisal per category is allowed")

class PayrollPayrollEmployeeAppraisalsSetupLines(models.Model):
    _name = 'payroll.emp.appraisals.setup.line'
    _description = 'Payroll Employee Appraisals Setup Line'
    _rec_name = 'performance'

    appraisal_header_id = fields.Many2one('payroll.emp.appraisals.setup.header', string='Appraisal Header', ondelete='cascade')
    performance = fields.Char(string="Performance", required=True)
    scale_min = fields.Integer(string="Scale Min", required=True, default=1)
    scale_max = fields.Integer(string="Scale Max", required=True)

class PayrollEmployeeAppraisals(models.Model):
    _name = 'payroll.employee.appraisals'
    _description = 'Employee Appraisals'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, default='New', readonly=True)
    assessed_by = fields.Many2one('res.users', string='Assessed By', default=lambda self: self.env.user, readonly=True)
    assessed_date = fields.Date(string='Assessed Date', default=fields.Date.today)
    assessed_position = fields.Many2one('payroll.positions', string='Current Position', required=True, readonly=True)
    employee_assessed = fields.Many2one('payroll.employees', string='Employee', required=True)
    appraisal_lines = fields.One2many('payroll.employee.appraisal.line', 'appraisal_id', string='Appraisal Lines')
    total_score = fields.Integer(string='Total Score', store=True, readonly=True) #, compute='_compute_total_score'

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

        # domain = [] 
        
        # if allowed_departments and allowed_categories:
        #     for dept in allowed_departments:
        #         for cat in allowed_categories:
        #             domain += ['|',('employee_assessed.department_id', '=', dept), ('employee_assessed.category_id', '=', cat)]
        # elif allowed_departments:
        #     for dept in allowed_departments:
        #         domain += [('employee_assessed.department_id', '=', dept)]
        # elif allowed_categories:
        #     for cat in allowed_categories:
        #         domain += [('employee_assessed.category_id', '=', cat)]

        domain = []
        if allowed_departments and allowed_categories:
            domain = ['|', ('employee_assessed.department_id', 'in', allowed_departments), ('employee_assessed.category_id', 'in', allowed_categories)]
        elif allowed_departments:
            domain = [('employee_assessed.department_id', 'in', allowed_departments)]
        elif allowed_categories:
            domain = [('employee_assessed.category_id', 'in', allowed_categories)]

        if domain:
            args += domain

        return super(PayrollEmployeeAppraisals, self).search(args, offset, limit, order, count)

    @api.onchange('assessed_by')
    def _onchange_assessed_by(self):
        """
        This method is called when the assessed_by field is changed."""
        if self.assessed_by:
            self.assessed_position = self.env['payroll.employees'].search([('user_id', '=', self.assessed_by.id)], limit=1).current_position

    @api.depends('appraisal_lines.score')
    def _compute_total_score(self):
        """
        This method will compute the total score."""
        for record in self:
            record.total_score = sum(line.score for line in record.appraisal_lines)

    @api.onchange('employee_assessed')
    def _onchange_employee_assessed(self):
        """
        This method is called when the employee_assessed field is changed."""
        if self.employee_assessed:
            # Clear existing appraisal lines
            self.appraisal_lines = [(5, 0, 0)]
            
            appraisal_header = self.env['payroll.emp.appraisals.setup.header'].search([('category_id', '=', self.employee_assessed.category_id.id), ('active_appraisal', '=', True)], limit=1)
            
            if appraisal_header:
                appraisal_lines = []
                for line in appraisal_header.appraisal_line_ids:
                    appraisal_lines.append((0, 0, {
                        'question_id': line.id,
                        'score': 0
                    }))
                self.appraisal_lines = appraisal_lines

    @api.model
    def create(self, vals):
        """
        This method is called when creating a new record."""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('payroll.employee.appraisals') or 'New'
        return super(PayrollEmployeeAppraisals, self).create(vals)

class PayrollEmployeeAppraisalLine(models.Model):
    _name = 'payroll.employee.appraisal.line'
    _description = 'Employee Appraisal Line'

    appraisal_id = fields.Many2one('payroll.employee.appraisals', string='Appraisal', ondelete='cascade')
    question_id = fields.Many2one('payroll.emp.appraisals.setup.line', string='Question', required=True, store=True)
    score = fields.Integer(string='Score')

    @api.onchange('score')
    def _onchange_score(self):
        """
        This method is called when the score field is changed."""
        if self.score < self.question_id.scale_min or self.score > self.question_id.scale_max:
            raise ValidationError("Score must be between %s and %s" % (self.question_id.scale_min, self.question_id.scale_max))