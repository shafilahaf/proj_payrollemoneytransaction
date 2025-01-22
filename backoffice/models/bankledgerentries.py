from odoo import models, fields, api, _

class BankLedgerEntries(models.Model):
    _name = 'bo.bank.ledger.entries'
    _description = 'Bank Ledger Entries'

    entry_no = fields.Integer(string='Entry No.')
    posting_date = fields.Date(string='Posting Date')
    document_type = fields.Selection([('1', 'BackOffice')], string='Document Type')
    document_id_header = fields.Many2one('bo.header', string='Document No.')
    document_id_line = fields.Integer(string='Document Line No.')
    kategori = fields.Many2one('kategori.bo', string='Kategori')
    mistaketype = fields.Many2one('mistaketype.bo', string='Mistake Type')
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account')
    bank_account_no = fields.Char(string='Bank Account No.', related='bank_account_id.bank_id.name')
    bank_account_name = fields.Char(string='Bank Account Name', related='bank_account_id.acc_holder_name')
    amount = fields.Float(string='Amount')
    is_from_request_tampung = fields.Boolean(string='From Request Tampung', default=False)
    request_category_name = fields.Char(string='Request Name')

    @api.model
    def create_approval_log(self, entry_no, posting_date, document_type, document_id_header, kategori, bank_account_id, amount, document_id_line, is_from_request_tampung, request_category_name):
        log = self.create({
            'entry_no': entry_no,
            'posting_date': posting_date,
            'document_type': document_type,
            'document_id_line': document_id_line,
            'document_id_header': document_id_header,
            'kategori': kategori,
            'bank_account_id': bank_account_id,
            'amount': amount,
            'is_from_request_tampung': is_from_request_tampung,
            'request_category_name': request_category_name,
        })

        return log

class BankLedgerEntries(models.TransientModel):
    _name = 'bo.bank.ledger.entries.wizard'
    _description = 'Bank Ledger Entries Wizard'

    note = fields.Text(string='Note', default='This wizard will insert bank ledger entries for all backoffice transactions that have not been inserted into bank ledger entries.', readonly=True)

    def insert_bank_ledger_entries(self):
        bo_line = self.env['bo.line'].search([
            ('id', 'not in', self.env['bo.bank.ledger.entries'].search([]).mapped('document_id_line'))
        ])
        
        if not bo_line:
            return  
        
        existing_entries = self.env['bo.bank.ledger.entries'].search([], order='entry_no desc', limit=1)
        entry_no = existing_entries.entry_no if existing_entries else 0

        ledger_entries_to_create = []
        
        for line in bo_line:
            entry_no += 1
            entry_vals = {
                'entry_no': entry_no,
                'posting_date': line.bo_id.date,
                'document_type': "1",
                'document_id_header': line.bo_id.id,
                'document_id_line': line.id,
                'kategori': line.kategori.id,
                'mistaketype': line.mistaketype.id,
                'bank_account_id': line.bank_account.id,
                'amount': line.nominal,
            }
            ledger_entries_to_create.append(entry_vals)
        
        if ledger_entries_to_create:
            self.env['bo.bank.ledger.entries'].create(ledger_entries_to_create)


