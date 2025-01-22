from odoo import models, fields, api #type: ignore
from odoo.exceptions import UserError, ValidationError, AccessError #type: ignore
import base64
import xlrd #type: ignore
from io import BytesIO

class PayrollMistakeEntriesHeader(models.Model):
    _name = 'payroll.mistake.entries.header'
    _description = 'Payroll Mistake Entries Header'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True, default=lambda self: ('New'))
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today())
    status = fields.Selection([
        ('1', 'Open'),
        ('2', 'Released'),
    ], string='Status', default='1')
    department_id = fields.Many2one('payroll.device.department', string='Department')
    category_id = fields.Many2one('payroll.employee.categories', string='Category')
    website_id = fields.Many2one('payroll.websites', string='Website')
    details_ids = fields.One2many('payroll.mistake.entries.details', 'header_id', string='Details')
    file = fields.Binary(string='File')
    deduction_id = fields.Many2one('payroll.deductions', string='Deduction')
    currency_id = fields.Many2one('payroll.currencies', string='Currency')
    is_ph = fields.Boolean(string='Is PH')

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('payroll.mistake.entries.header') or ('New')
        return super(PayrollMistakeEntriesHeader, self).create(vals)
    
    @api.model
    def check_edit_permission(self):
        """Check if the user belongs to a group that can edit mistake entries."""
        user_groups = self.env.user.groups_id
        if not any(group.can_edit_mistake_entries for group in user_groups) and self.status == '2':
            raise AccessError("You do not have the permission to edit this entry.")

    def write(self, vals):
        """Override write method to enforce edit permissions."""
        self.check_edit_permission()
        return super(PayrollMistakeEntriesHeader, self).write(vals)

    def action_release(self):
        for rec in self:
            rec.status = '2'

    def insert_file_to_details(self):
        """
        Insert excel file to details
        """
        if not self.file:
            raise UserError('Please upload a file first.')
        
        file_content = base64.b64decode(self.file)
        workbook = xlrd.open_workbook(file_contents=BytesIO(file_content).read())
        sheet = workbook.sheet_by_index(0)

        deductions = {}
        # Header column 3 until end is name of deductions.. pls map it to deductions
        for i in range(3, sheet.ncols):
            name = sheet.cell_value(0, i)
            deduction = self.env['payroll.deductions'].search([('name', '=', name)], limit=1)
            if not deduction:
                raise UserError('Deduction %s not found' % name)
            deductions[i] = deduction.id

        for i in range(1, sheet.nrows):
            nik = sheet.cell_value(i, 0)
            if isinstance(nik, float):
                nik = str(int(nik))
            else:
                nik = str(nik)
            name = sheet.cell_value(i, 1)
            location = sheet.cell_value(i, 2)
            employee = self.env['payroll.employees'].search([('nik', '=', nik)], limit=1)
            if not employee:
                raise UserError('Employee with NIK %s not found' % nik)
            for j in range(3, sheet.ncols):
                deduction_id = deductions[j]
                amount = sheet.cell_value(i, j)
                if amount:
                    self.env['payroll.mistake.entries.details'].create({
                        'header_id': self.id,
                        'employee_id_2': employee.id,
                        'department_id': self.env['payroll.device.department'].search([('name', '=', location)], limit=1).id,
                        'deduction_id': deduction_id,
                        'amount': amount,
                    })

        self.is_ph = True


class PayrollMistakeEntriesDetails(models.Model):
    _name = 'payroll.mistake.entries.details'
    _description = 'Payroll Mistake Entries Details'
    _sql_constraints = [
        ('unique_employee_mistake_deduction', 'unique(employee_id, mistake, deduction_id)', 'Employee with same mistake and deduction already exists')
    ]

    header_id = fields.Many2one('payroll.mistake.entries.header', string='Header', ondelete='cascade')
    employee_id = fields.Many2one('payroll.employees', string='Employee') #, domain="[('department_id', '=', parent.department_id), ('category_id', '=', parent.category_id), ('current_website', '=', parent.website_id)]"
    mistake = fields.Selection([
        ('2', 'Mistake 1'),
        ('3', 'Mistake 2'),
    ], string='Mistake')
    mistake_value = fields.Char(string='Mistake Value', readonly=True, store=True)
    currency_id = fields.Many2one('payroll.currencies', string='Currency')
    member_user = fields.Char(string='Member User')
    amount = fields.Float(string='Amount')
    amount_lcy = fields.Float(string='Amount LCY')
    deduction_id = fields.Many2one('payroll.deductions', string='Deduction') #ph upload
    department_id = fields.Many2one('payroll.device.department', string='Department') #ph upload
    employee_id_2 = fields.Many2one('payroll.employees', string='Employee') #ph upload
    mistake_detail = fields.Many2one('payroll.mistake.detail', string='Mistake Detail')
    

    @api.onchange('mistake')
    def _onchange_mistake(self):
        if self.mistake == '2':
            self.mistake_value = 'Mistake 1'
        elif self.mistake == '3':
            self.mistake_value = 'Mistake 2'

        category_filter = [('deduction_name', '=', self.mistake_value)]
        
        if self.header_id.category_id:
            category_filter.append(('categories_id', '=', self.header_id.category_id.id))
        elif self.employee_id.category_id:
            category_filter.append(('categories_id', '=', self.employee_id.category_id.id))

        if self.mistake:
            return {
                'domain': {
                    'mistake_detail': category_filter
                }
            }
        
    @api.onchange('mistake_detail')
    def _onchange_mistake_detail(self):
        if self.mistake_detail:
            self.amount = self.mistake_detail.default_amount
            self.currency_id = self.mistake_detail.currency_id.id

