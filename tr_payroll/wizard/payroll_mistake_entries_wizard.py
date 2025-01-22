from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from openpyxl import Workbook
import io
import base64
import urllib.parse

class PayrollMistakeEntriesWizard(models.TransientModel):
    _name = 'payroll.mistake.entries.wizard'
    _description = 'Payroll Mistake Entries Wizard'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    department_ids = fields.Many2many('payroll.device.department', string='Department')
    category_ids = fields.Many2many('payroll.employee.categories', string='Category')

    def export_excel(self):
        """
        Export payroll mistake entries to Excel files
        """
        # Create Excel file
        wb = Workbook()
        ws = wb.active
        ws.title = "Payroll Mistake Entries"
        header = ['Name', 'NIK', 'Department', 'Date', 'Type',
                'Description', 'Mistake Detail', 'Amount', 'AmountLCY', 'Currency',
                'Member User', 'Website', 'Status']
        ws.append(header)
        
        # Set column widths
        column_widths = [25] + [18] * (len(header) - 1)
        for i, width in enumerate(column_widths, start=1):
            ws.column_dimensions[chr(64 + i)].width = width

        # Get payroll mistake entries based on selected departments and categories
        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('is_ph', '=', False)
        ]

        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        
        if self.category_ids:
            domain.append(('category_id', 'in', self.category_ids.ids))

        mistake_entries_1 = self.env['payroll.mistake.entries.header'].search(domain)

        domain_mistake_detail = [
            ('header_id', 'in', mistake_entries_1.ids)
        ]

        if self.department_ids:
            domain_mistake_detail.append(('employee_id.department_id', 'in', self.department_ids.ids))
        
        if self.category_ids:
            domain_mistake_detail.append(('employee_id.category_id', 'in', self.category_ids.ids))

        mistake_entries_detail_1 = self.env['payroll.mistake.entries.details'].search(domain_mistake_detail)

        for med in mistake_entries_detail_1:
            
            mistake_description = ''
            if med.mistake == '2':
                mistake_description = 'Mistake 1'
            elif med.mistake == '3':
                mistake_description = 'Mistake 2'

            mistake_status = ''
            if med.header_id.status == '1':
                mistake_status = 'Open'
            elif med.header_id.status == '2':
                mistake_status = 'Released'

            mistake_detail_name = med.mistake_detail.name if med.mistake_detail else ''

            ws.append([
                med.employee_id.name,
                med.employee_id.nik,
                med.employee_id.department_id.name,
                med.header_id.date,
                med.mistake,
                mistake_description,
                mistake_detail_name,
                med.amount,
                med.amount_lcy,
                med.currency_id.name,
                med.member_user,
                med.header_id.website_id.name if med.header_id.website_id else '',
                mistake_status,
            ])

        # Save Excel file to binary field
        fp = io.BytesIO()
        wb.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        # Encode data to base64
        data_base64 = base64.b64encode(data)

        # Save Excel file to attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'payroll_mistake_entries.xlsx',
            'type': 'binary',
            'datas': data_base64,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Return attachment
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s' % (attachment.id, urllib.parse.quote(attachment.name)),
            'target': 'self'
        }
