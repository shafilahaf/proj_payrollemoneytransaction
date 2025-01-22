from odoo import models, fields, api #type:ignore
from odoo.exceptions import UserError, ValidationError #type:ignore
from datetime import date

class PayrollPayrollSummaries(models.Model):
    _name = 'payroll.payroll.summaries'
    _description = 'Payroll Summaries'

    employee_id = fields.Many2one('payroll.employees', string='Employee')
    employee_id_department = fields.Many2one('payroll.device.department', string='Employee Department', related='employee_id.department_id')
    employee_id_category = fields.Many2one('payroll.employee.categories', string='Employee Category', related='employee_id.category_id')
    employee_company_id = fields.Many2one('payroll.companies', string='Company', related='employee_id.company_id')
    employee_position_id = fields.Many2one('payroll.positions', string='Position', related='employee_id.current_position')
    month = fields.Integer(string='Month')
    year = fields.Char(string='Year')
    total_work_days = fields.Integer(string='Total Work Days')
    days_in = fields.Integer(string='Days In')
    days_absent = fields.Integer(string='Days Absent')
    days_permission = fields.Integer(string='Days Permission')
    days_leave = fields.Integer(string='Days Leave')
    sick_permission = fields.Integer(string='Sick Permission')
    days_off = fields.Integer(string='Days Off')
    late = fields.Integer(string='Late')
    forget_checkout_count = fields.Integer(string='Forget Checkout Count')
    mistake_1_count = fields.Integer(string='Mistake 1 Count')
    mistake_2_count = fields.Integer(string='Mistake 2 Count')
    basic_salary = fields.Float(string='Basic Salary')
    total_reward = fields.Float(string='Total Reward')
    total_deduction = fields.Float(string='Total Deduction')
    total_reimbursment = fields.Float(string='Total Reimbursment')
    net_salary = fields.Float(string='Net Salary')
    finished = fields.Boolean(string='Finished')
    currency_id = fields.Many2one('payroll.currencies', string='Currency')
    late2 = fields.Integer(string='Late 2')
    # periode = fields.Integer(string='Periode')
    periode = fields.Selection([
        ('1', 'Periode 1'),
        ('2', 'Periode 2'),
    ], string='Periode')
    late3 = fields.Integer(string='Late 3')
    late4 = fields.Integer(string='Late 4')
    total_point = fields.Float(string='Total Point')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    month_text = fields.Char(string='Month Text', compute='_compute_month_text', store=True)

    payroll_summary_detail_ids = fields.One2many('payroll.payroll.summary.detail', 'payroll_summary_id', string='Payroll Summary Detail')
    summary_grouped_by_currency = fields.One2many('payroll.currency.summary', string='Summary Grouped By Currency', compute='_compute_summary_grouped_by_currency')
    attendance_log_ids = fields.One2many('payroll.attendance.log', string='Attendance Logs', compute='_compute_attendance_logs')
    # dashboard_id = fields.Many2one('tr.payroll.dashboard.staff', string="Dashboard")

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
        #             domain += ['|',('employee_id_department', '=', dept), ('employee_id_category', '=', cat)]
        # elif allowed_departments:
        #     for dept in allowed_departments:
        #         domain += [('employee_id_department', '=', dept)]
        # elif allowed_categories:
        #     for cat in allowed_categories:
        #         domain += [('employee_id_category', '=', cat)]

        domain = []
        if allowed_departments and allowed_categories:
            domain = ['|', ('employee_id_department', 'in', allowed_departments), ('employee_id_category', 'in', allowed_categories)]
        elif allowed_departments:
            domain = [('employee_id_department', 'in', allowed_departments)]
        elif allowed_categories:
            domain = [('employee_id_category', 'in', allowed_categories)]

        if domain:
            args += domain

        return super(PayrollPayrollSummaries, self).search(args, offset=offset, limit=limit, order=order, count=count)

    def button_details(self):
        report = self.env.ref('tr_payroll.report_payroll_sumarries_template')
        return report.report_action(self)
    
    def action_preview_pdf(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/report/payroll_summary/{self.id}',
            'target': 'new',  # new tab browser
        }

    
    @api.depends('month')
    def _compute_month_text(self):
        for record in self:
            if record.month:
                record.month_text = date(1900, record.month, 1).strftime('%B')
            else:
                record.month_text = ''

    # V2
    @api.depends('payroll_summary_detail_ids.net_amount', 'payroll_summary_detail_ids.currency_id')
    def _compute_summary_grouped_by_currency(self):
        for record in self:
            # Remove existing currency summary entries
            record.summary_grouped_by_currency.unlink()

            # Calculate new summary grouped by currency
            currency_summary = {}
            for detail in record.payroll_summary_detail_ids:
                currency = detail.currency_id
                if currency not in currency_summary:
                    currency_summary[currency] = 0
                currency_summary[currency] += detail.net_amount

            # Create new currency summary records
            summary_data = []
            for currency, amount in currency_summary.items():
                summary_data.append((0, 0, {
                    'currency_id': currency.id,
                    'net_amount': amount,
                    'payroll_summary_id': record.id
                }))
            record.write({'summary_grouped_by_currency': summary_data})

    @api.depends('employee_id', 'from_date', 'to_date')
    def _compute_attendance_logs(self):
        for record in self:
            if record.employee_id and record.from_date and record.to_date:
                record.attendance_log_ids = self.env['payroll.attendance.log'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('date', '>=', record.from_date),
                    ('date', '<=', record.to_date)
                ])
            else:
                record.attendance_log_ids = False

class PayrollPayrollSummaryDetail(models.Model):
    _name = 'payroll.payroll.summary.detail'
    _description = 'Payroll Summary Detail'

    payroll_summary_id = fields.Many2one('payroll.payroll.summaries', string='Payroll Summary', ondelete='cascade')
    type_id = fields.Char(string='Type ID')
    type = fields.Integer(string='Type')
    type_text = fields.Char(string='Type Text')
    name = fields.Char(string='Name')
    amount = fields.Float(string='Amount')
    currency_id = fields.Many2one('payroll.currencies', string='Currency')
    condition = fields.Integer(string='Condition')
    condition_text = fields.Char(string='Condition Text')
    days_count = fields.Integer(string='Days Count')
    net_amount = fields.Float(string='Net Amount')

class PayrollCurrencySummary(models.Model):
    _name = 'payroll.currency.summary'
    _description = 'Payroll Currency Summary'

    currency_id = fields.Many2one('payroll.currencies', string='Currency')
    net_amount = fields.Float(string='Net Amount')
    payroll_summary_id = fields.Many2one('payroll.payroll.summaries', string='Payroll Summary', ondelete='cascade')