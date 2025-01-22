from odoo import models, fields, api
from odoo.exceptions import UserError

class PayrollKeyPerformanceIndex(models.Model):
    _name = 'payroll.key.performance.index'
    _description = 'Payroll Key Performance Index'

    year = fields.Char(string='Year', required=True)
    semester = fields.Selection([
        ('1', 'Semester 1'),
        ('2', 'Semester 2')
    ], string='Semester', required=True)
    employee_id = fields.Many2one('payroll.employees', string='Employee', required=True)
    total_att_log_point = fields.Float(string='Total Attendance Log Point')
    total_performance_point = fields.Float(string='Total Performance Point')
    kpi_point = fields.Float(string='KPI Point')
    date = fields.Date(string="Date")

    kpi_details_ids = fields.One2many('payroll.key.performance.index.detail', 'kpi_header', string='Kpi Details', ondelete='cascade')

    # dashboard_id = fields.Many2one('tr.payroll.dashboard.staff', string="Dashboard")
    

    # def action_generate_kpi_report(self):
    #     return self.env.ref('your_module.report_kpi_template').report_action(self)
    
    # @api.multi
    def button_details(self):
        report = self.env.ref('tr_payroll.report_kpi_template')
        return report.report_action(self)
    
class PayrollKeyPerformanceIndexDetail(models.Model):
    _name = 'payroll.key.performance.index.detail'
    _description = 'Payroll Key Performance Index Detail'

    kpi_header = fields.Many2one('payroll.key.performance.index', string="KPI Header")
    type = fields.Integer(string='Type')
    type_text = fields.Char(string='Type Text')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    total_point = fields.Float('Total Point')
    percentage = fields.Integer('Percentage')
    kpi_point = fields.Float('Kpi Point')
    
    
    
    
    
    
    