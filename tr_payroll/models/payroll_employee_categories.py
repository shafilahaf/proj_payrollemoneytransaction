from odoo import models, fields, api # type: ignore
from odoo.exceptions import UserError, ValidationError # type: ignore

class PayrollEmployeeCategories(models.Model):
    _name = 'payroll.employee.categories'
    _description = 'Employee Categories'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    leave_currency_code = fields.Many2one('payroll.currencies', string='Leave Currency Code')
    without_attendance_logs = fields.Boolean(string='Without Attendance Logs')
    salary_cut_off = fields.Integer(string='Salary Cut Off', required=True)
    salary_cut_off_2 = fields.Integer(string='Salary Cut Off 2', required=True)
    salary_adjustment = fields.Float(string='Salary Adjustment')
    over_sick_deduction_to = fields.Selection([
        ('1', 'Absence'),
        ('2', 'Permission')
    ], string='Over Sick Deduction To')
    attendance_log_percent = fields.Float(string='Attendance Log %')
    performance_percent = fields.Float(string='Performance %')
    blocked = fields.Boolean(string='Blocked')
    active = fields.Boolean(string='Active', default=True)
    
    salary_components_ids = fields.One2many('payroll.emp.cat.salary.component', 'categories_id', string='Salary Components')
    deductions_ids = fields.One2many('payroll.emp.cat.deduction', 'categories_id', string='Deductions')
    benefits_ids = fields.One2many('payroll.emp.cat.benefit', 'categories_id', string='Benefits')
    timeoff_setup_ids = fields.One2many('payroll.emp.cat.timeoff.setup', 'categories_id', string='Time Off Setup')
    mistake_entries_detail_ids = fields.One2many('payroll.emp.cat.mistake.etnries.detail','categories_id', string='Mistake Entries Detail')

    @api.model
    def create(self, vals):
        res = super(PayrollEmployeeCategories, self).create(vals)
        if res.mistake_entries_detail_ids:
            for mistake_entries_detail in res.mistake_entries_detail_ids:
                mistake_detail = self.env['payroll.mistake.detail'].create({
                    'name': mistake_entries_detail.mistake_detail_name,
                    'deduction_id': mistake_entries_detail.deduction_id.id,
                    'categories_id': res.id,
                    'default_amount': mistake_entries_detail.default_amount,
                    'currency_id': mistake_entries_detail.currency_id.id
                })
                mistake_entries_detail.mistake_detail_name = mistake_detail.name
        return res
    
class PayrollEmpCatSalaryComponent(models.Model):
    _name = 'payroll.emp.cat.salary.component'
    _description = 'Employee Category Salary Component'

    salary_component_id = fields.Many2one('payroll.salary.components', string='Salary Component', required=True)
    currency_id = fields.Many2one('payroll.currencies', string='Currency', required=True)
    amount = fields.Float(string='Amount', required=True)
    condition = fields.Selection([
        ('1', 'No Mistake'),
        ('2', 'Not Taken Leaves')
    ], string='Condition')
    recurring = fields.Integer(string='Recurring')
    minimum_working_duration = fields.Integer(string='Minimum Working Duration')
    meal_type = fields.Selection([
        ('1', 'Give After'),
        ('2', 'Upfront'),
        ('3', 'Day Rate')
    ], string='Meal Type')
    pro_rate = fields.Boolean(string='Pro Rate')
    is_basic_salary = fields.Boolean(string='Is Basic Salary', store=True)

    categories_id = fields.Many2one('payroll.employee.categories', string='Employee Category', ondelete='cascade')

    @api.onchange('salary_component_id')
    def _onchange_salary_component_id(self):
        """
        This method is called when the salary_component_id field is changed."""
        self.is_basic_salary = self.salary_component_id.is_basic_salary

class PayrollEmpCatDeduction(models.Model):
    _name = 'payroll.emp.cat.deduction'
    _description = 'Employee Category Deduction'

    deduction_id = fields.Many2one('payroll.deductions', string='Deduction', required=True)
    currency_id = fields.Many2one('payroll.currencies', string='Currency', required=True)
    amount = fields.Float(string='Amount', required=True)
    amount_from_basic_salary = fields.Boolean(string='Amount From Basic Salary')
    deduction_source = fields.Selection([
        ('1', 'Absen'),
        ('2', 'Mistake 1'),
        ('3', 'Mistake 2'),
        ('4', 'Absen Late'),
        ('5', 'Absen Not Check Out'),
        ('6', 'Permission'),
        ('7', 'Absen Late Layer 2'),
        ('8', 'Absen Late Layer 3'),
        ('9', 'Absen Late Layer 4'),
    ], string='Source', related='deduction_id.source', store=True)
    categories_id = fields.Many2one('payroll.employee.categories', string='Employee Category', ondelete='cascade')

class PayrollEmpCatBenefit(models.Model):
    _name = 'payroll.emp.cat.benefit'
    _description = 'Employee Category Benefit'

    benefit_id = fields.Many2one('payroll.benefits', string='Benefit', required=True)
    currency_id = fields.Many2one('payroll.currencies', string='Currency', required=True)
    amount = fields.Float(string='Amount', required=True)
    limit_days = fields.Integer(string='Limit Days')
    minimum_working_duration = fields.Integer(string='Minimum Working Duration')
    recurring_month = fields.Integer(string='Recurring Month')
    cut_off_year = fields.Boolean(string='Cut Off Year')

    categories_id = fields.Many2one('payroll.employee.categories', string='Employee Category', ondelete='cascade')

class PayrollEmpCatTimeOffSetup(models.Model):
    _name = 'payroll.emp.cat.timeoff.setup'
    _description = 'Employee Category Time Off Setup'

    type = fields.Selection([
        ('1', 'Leave'),
        ('2', 'Day Off')
    ], string='Type', required=True)
    days_off = fields.Integer(string='Days Off')
    minimum_working_duration = fields.Integer(string='Minimum Working Duration')
    reccuring_month = fields.Integer(string='Recurring Month')
    ticket_currency_id = fields.Many2one('payroll.currencies', string='Ticket Currency')
    ticket_amount = fields.Float(string='Ticket Amount')

    categories_id = fields.Many2one('payroll.employee.categories', string='Employee Category', ondelete='cascade')

class PayrollEmpCatMistakeEntriesDetail(models.Model):
    _name = 'payroll.emp.cat.mistake.etnries.detail'
    _description = 'Employee Mistake Entries Detail'
    _rec_name = 'mistake_detail_name'

    deduction_id = fields.Many2one('payroll.deductions', string='Deduction') 
    mistake_detail_name = fields.Char(string='Mistake Detail Name', store=True)
    currency_id = fields.Many2one('payroll.currencies', string='Currency', required=True)
    default_amount = fields.Float(string='Default Amount')
    categories_id = fields.Many2one('payroll.employee.categories', string='Employee Category', ondelete='cascade')
    
    