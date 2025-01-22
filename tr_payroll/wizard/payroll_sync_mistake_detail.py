from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class PayrollSyncMistakeDetailWizard(models.TransientModel):
    _name = 'payroll.sync.mistake.detail'
    _description = 'Sync Mistake Detail'

    desc = fields.Char(string="Description", default='This is for sync mistake detail from employee categories', readonly=True)

    def sync_mistake_detail(self):
        # Fetch all payroll employee categories
        categories = self.env['payroll.employee.categories'].search([])

        for category in categories:
            # Filter mistake entries where mistake_detail_name is not empty
            valid_mistake_entries = category.mistake_entries_detail_ids.filtered(lambda x: x.mistake_detail_name)

            for mistake_entry in valid_mistake_entries:
                # Check if a record with the same mistake detail already exists
                existing_detail = self.env['payroll.mistake.detail'].search([
                    ('name', '=', mistake_entry.mistake_detail_name),
                    ('categories_id', '=', category.id)
                ])

                if not existing_detail:
                    self.env['payroll.mistake.detail'].create({
                        'name': mistake_entry.mistake_detail_name,
                        'deduction_id': mistake_entry.deduction_id.id,
                        'default_amount': mistake_entry.default_amount,
                        'categories_id': category.id,
                        'currency_id': mistake_entry.currency_id.id,
                    })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }