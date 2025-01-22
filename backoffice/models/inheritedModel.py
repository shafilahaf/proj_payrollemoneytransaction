from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

#inherit group (res.groups)
class inheritedGroup(models.Model):
    _inherit = "res.groups"

    isImportLines = fields.Boolean(string='Access Import Lines Backoffice', default=False)
    isBulkDelete = fields.Boolean(string='Access Bulk Delete Backoffice', default=False)
    isResetToDraft = fields.Boolean(string='Access Reset to Draft Backoffice', default=False)
    isApproveBlBtl = fields.Boolean(string='Access Approve BL/BL Backoffice', default=False)
    isApproveWD = fields.Boolean(string='Access Approve WD Backoffice', default=False)
    isShowBackofficeLine = fields.Boolean(string='Access Search Line Backoffice', default=False)

#inherit bank account(res.partner.bank)
class inheritedBankAccount(models.Model):
    _inherit = "res.partner.bank"

    # balance_per_bank = fields.Float(string="Balance", compute='_compute_balance_per_bank', store=True) #sum up by the initial balance and the nominal
    balance_per_bank2 = fields.Float(string="Balance", compute='_compute_balance_per_bank2', store=True) #sum up by the initial balance and the nominal
    # bo_line_ids = fields.One2many('bo.line', 'bank_account', string='Backoffice Lines')
    bo_ledger_entries_ids = fields.One2many('bo.bank.ledger.entries', 'bank_account_id', string='Bank Ledger Entries')
    max_limit = fields.Float(string="Max Limit")
    type = fields.Selection([('dana', 'Dana'), ('pulsa', 'Pulsa'), ('bankgojek', 'Bank GoJek'), ('linkaja', 'LinkAja'), ('ovo', 'OVO')], string='Type')
    expired_date = fields.Date(string="Expired Date")
    user_id = fields.Char(string="User ID")
    password = fields.Char(string="Password")
    token = fields.Char(string="Token")
    location = fields.Char(string="Location")
    location_detail = fields.Char(string="Location Detail")
    reference_name = fields.Char(string="Ref. Name")
    initial_balance = fields.Float(string="Saldo Awal")
    balance_per_bank_initial_balance = fields.Float(string="Balance", compute='_compute_balance_per_bank_initial_balance', store=True) #sum up by the initial balance and the nominal

    # 8/27/2023 - Storing borrow - return balance
    # borrow_amount = fields.Float(string="Borrow Amount", default=0)
    # return_amount = fields.Float(string="Return Amount", default=0)
    # borrow_return_balance = fields.Float(string="Borrow Return Balance", compute='_compute_borrow_return_balance', store=True)

    # @api.depends('borrow_amount', 'return_amount')
    # def _compute_borrow_return_balance(self):
    #     """
    #     Compute the balance of the bank account."""
    #     for rec in self:
    #         rec.borrow_return_balance = rec.borrow_amount - rec.return_amount

    def name_get(self):
        result = []
        for bank in self:
            # display_name = f"{bank.acc_holder_name} - {bank.acc_number}"
            display_name = f"{bank.reference_name} - {bank.acc_number}"
            result.append((bank.id, display_name))
        return result
    
    @api.depends('bo_ledger_entries_ids.amount')
    def _compute_balance_per_bank2(self):
        """
        Compute the balance of the bank account."""
        for rec in self:
            rec.balance_per_bank2 = sum(rec.bo_ledger_entries_ids.mapped('amount'))

    @api.depends('initial_balance', 'bo_ledger_entries_ids.amount')
    def _compute_balance_per_bank_initial_balance(self):
        """
        Compute the balance of the bank account."""
        for rec in self:
            rec.balance_per_bank_initial_balance = rec.initial_balance + sum(rec.bo_ledger_entries_ids.mapped('amount'))

    # @api.depends('bo_line_ids.nominal')
    # def _compute_balance_per_bank(self):
    #     """
    #     Compute the balance of the bank account."""
    #     for rec in self:
    #         bo_header_records = rec.bo_line_ids.mapped('bo_id')
    #         initial_balances = bo_header_records.mapped('initial_balance')
    #         rec.balance_per_bank = sum(initial_balances) + sum(rec.bo_line_ids.mapped('nominal'))



    # def action_view_bo_lines(self):
    #     """
    #     This function returns an action that display existing BO Lines of given Bank Account."""
    #     return {
    #         'name': _('BO Lines'),
    #         'view_type': 'form',
    #         'view_mode': 'tree',
    #         'res_model': 'bo.line',
    #         'view_id': False,
    #         'type': 'ir.actions.act_window',
    #         'domain': [('bank_account', '=', self.id)],
    #         'context': {'search_default_bank_account': self.id},
    #     }

    def action_view_bo_lines(self):
        """
        This function returns an action that display existing Bank Ledger Entries of given Bank Account."""
        return {
            'name': _('Bank Ledger Entries'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'bo.bank.ledger.entries',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('bank_account_id', '=', self.id)],
            # 'context': {'search_default_bank_account_id': self.id},
            'context': {'create': False, 'edit': False, 'delete': False},
        }

#inherit bank (res.bank)
class inheritedBank(models.Model):
    _inherit = "res.bank"

    websites = fields.Many2one('bo.website', string='Website', store=True)
    isBankTampung = fields.Boolean(string='Is Bank Tampung?', default=False)

#inherit user (res.users)
class inheritedUser(models.Model):
    _inherit = "res.users"
    stafftype = fields.Many2one('bo.staff.type', string='Staff Type')
    website = fields.Many2many('bo.website', string='Website')    
            
##inherit approval.category (approval.category)
class inheritedApprovalCategory(models.Model):
    _inherit = "approval.category"

    approver_group_ids = fields.Many2one('res.groups', string='Approver Group', track_visibility='always')
    kategori = fields.Many2one('kategori.bo', string='Kategori', help="Kategori yang digunakan untuk approval, menentukan kategori pada saat insert ke Backoffice Line")
    isInsertBackofficeLine = fields.Boolean(string='Insert Backoffice Line', default=False)
    bank_account_tampung = fields.Many2one('res.partner.bank', string='Bank Account Tampung')

    banks = fields.Many2one('res.bank', string='Bank', track_visibility='always', help="Bank yang digunakan untuk filter From Bank Account pada saat insert ke Backoffice Line", required=True)

    has_website = fields.Selection([('required', 'Required'), ('optional', 'Optional'), ('no', 'None')], string='Has Website', default='required')
    has_bank_account_holder = fields.Selection([('required', 'Required'), ('optional', 'Optional'), ('no', 'None')], string='Has Bank Account Holder', default='no')
    has_from_bank_account = fields.Selection([('required', 'Required'), ('optional', 'Optional'), ('no', 'None')], string='Has From Bank Account', default='no')
    has_member_id = fields.Selection([('required', 'Required'), ('optional', 'Optional'), ('no', 'None')], string='Has Member ID', default='no')
    has_bank = fields.Selection([('required', 'Required'), ('optional', 'Optional'), ('no', 'None')], string='Has Bank', default='no')
    has_nama_rekening = fields.Selection([('required', 'Required'), ('optional', 'Optional'), ('no', 'None')], string='Has Nama Rekening', default='no')
    has_nomor_rekening = fields.Selection([('required', 'Required'), ('optional', 'Optional'), ('no', 'None')], string='Has Nomor Rekening', default='no')

# inherit approval.request
class inheritedApprovalRequest(models.Model):
    _inherit = "approval.request"

    website = fields.Many2one('bo.website', string='Website', track_visibility='always')
    name2 = fields.Char(string='Name', track_visibility='always', store=True)
    bank_account_holder = fields.Many2one('res.partner.bank', string='To Bank Account')
    banks_category = fields.Many2one('res.bank', string='Bank')
    # from_bank_account = fields.Many2one('res.partner.bank', string='From Bank Account', track_visibility='always')
    from_bank_account = fields.Many2one('res.partner.bank', string='From Bank Account', track_visibility='always', domain="[('bank_id', '=', banks_category)]")
    member_id = fields.Char(string='Member ID', track_visibility='always')
    name_bank = fields.Char(string='Bank', track_visibility='always')
    nama_rekening = fields.Char(string='Nama Rekening', track_visibility='always')
    nomor_rekening = fields.Char(string='Nomor Rekening', track_visibility='always')
    isExecuted2 = fields.Boolean(string='Execute')

    category_approval_name = fields.Char(related="category_id.name", string='Category Name', store=True)

    has_website = fields.Selection(related="category_id.has_website")
    has_bank_account_holder = fields.Selection(related="category_id.has_bank_account_holder")
    has_from_bank_account = fields.Selection(related="category_id.has_from_bank_account")
    has_member_id = fields.Selection(related="category_id.has_member_id")
    has_bank = fields.Selection(related="category_id.has_bank")
    has_nama_rekening = fields.Selection(related="category_id.has_nama_rekening")
    has_nomor_rekening = fields.Selection(related="category_id.has_nomor_rekening")

    active = fields.Boolean(default=True)

    # Approval Request Name -> Category Name / request_owner_id.name / website / date
    @api.onchange('category_id', 'request_owner_id', 'website', 'date')
    def _onchange_category_request_owner_id_website_date(self):
        if self.category_id.name and self.request_owner_id.name and self.website and self.date:
            self.name2 = self.category_id.name + '/' + self.request_owner_id.name + '/' + self.website.name + '/' + self.date.strftime("%d-%m-%Y")

    @api.onchange('category_id')
    def _onchange_category(self):
        if self.category_id.banks:
            self.banks_category = self.category_id.banks.id

    # @api.onchange('category_id', 'website')
    # def _onchange_category_website(self):
    #     if self.category_id.name.find('WD') != -1 and self.website:
    #         self.bank_account_holder = False
    #         domain = [('bank_id.websites', '=', self.website.id), ('bank_id.id', '=', self.category_id.banks.id)]
    #         return {'domain': {'bank_account_holder': domain}}
    #     else:
    #         domain = [('bank_id.websites', '=', self.website.id)]
    #         return {'domain': {'bank_account_holder': domain}}
    
    def send_group_approval(self):
        self.ensure_one()
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('Nominal cannot be 0 or less than 0!'))
            else:
                approvalGroup = self.env['approval.category'].search([('id', '=', rec.category_id.id)]).approver_group_ids
                if approvalGroup:
                    for user in approvalGroup.users:
                        #Create activity schedule for each user
                        rec.activity_schedule(
                            'approvals.mail_activity_data_approval',
                            user_id=user.id,
                            summary=_('Approval %s') % rec.name,
                            note=_('Please Approve this Request')
                        )
                        rec.approver_ids = [(0, 0, {'user_id': user.id, 'status': 'pending'})]
                    rec.write({'request_status': 'pending'})
                else:
                    raise ValidationError(_('Cannot find any approver group for this category!'))

    def action_approve(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'approved'})
        
        # Check if any other approver is pending
        pending_approvers = self.mapped('approver_ids').filtered(
            lambda approver: approver.status == 'pending'
        )
        
        # Delete activity schedule for other pending approvers
        for pending_approver in pending_approvers:
            self.activity_unlink(['approvals.mail_activity_data_approval'], user_id=pending_approver.user_id.id)
            pending_approver.write({'status': 'approved'})
        
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

    def action_refuse(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'refused'})
        
        # Check if any other approver is pending
        pending_approvers = self.mapped('approver_ids').filtered(
            lambda approver: approver.status == 'pending'
        )
        
        # Delete activity schedule for other pending approvers
        for pending_approver in pending_approvers:
            self.activity_unlink(['approvals.mail_activity_data_approval'], user_id=pending_approver.user_id.id)
            pending_approver.write({'status': 'refused'})
        
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

    def action_insert_bo_line(self):
        for rec in self:
            if rec.category_id.isInsertBackofficeLine:
                bo_header_bank_acc_holder = self.env['bo.header'].search([('state', '=', 'draft'), ('bank_account', '=', rec.bank_account_holder.id), ('isHasbeenResetDraft', '=', False), ('date', '=', rec.date)], limit=1)
                bo_header_from_bank_acc = self.env['bo.header'].search([('state', '=', 'draft'), ('bank_account', '=', rec.from_bank_account.id), ('isHasbeenResetDraft', '=', False), ('date', '=', rec.date)], limit=1) # , ('website', '=', rec.website.id)

                if bo_header_bank_acc_holder and bo_header_from_bank_acc:
                    # BackofficeLine
                    bo_line_bank_acc_holder = self.env['bo.line'].create({
                        'bo_id': bo_header_bank_acc_holder.id,
                        'kategori': rec.category_id.kategori.id,
                        'description': 'Approval Request : ' + rec.name2 + ' From Bank ' + rec.from_bank_account.acc_number,
                        'bank_account': rec.bank_account_holder.id,
                        'nominal': rec.amount,
                        'isExecuted': False,
                        'rekening_name': rec.nama_rekening if rec.nama_rekening else False,
                        'user_id': rec.member_id if rec.member_id else False,
                        'is_from_request_tampung': True,
                        'request_category_name': rec.category_id.name,
                        'transfer_bank_account': rec.from_bank_account.id,
                        'rekening_name': rec.nama_rekening if rec.nama_rekening else False,
                        'user_id': rec.member_id if rec.member_id else False,
                    })

                    bo_line_from_bank_acc = self.env['bo.line'].create({
                        'bo_id': bo_header_from_bank_acc.id,
                        'kategori': rec.category_id.kategori.id,
                        'description': 'Approval Request : ' + rec.name2 + ' To Bank ' + rec.bank_account_holder.acc_number,
                        'bank_account': rec.from_bank_account.id,
                        'nominal': -rec.amount,
                        'isExecuted': False,
                        'rekening_name': rec.nama_rekening if rec.nama_rekening else False,
                        'user_id': rec.member_id if rec.member_id else False,
                        'is_from_request_tampung': True,
                        'request_category_name': rec.category_id.name,
                        'rekening_name': rec.nama_rekening if rec.nama_rekening else False,
                        'user_id': rec.member_id if rec.member_id else False,
                    })
                    # BackofficeLine

                    # Bank Ledger Entries if request is Bayar WD
                    if 'BAYAR WD' in rec.category_id.name.upper():
                      bo_header_bank_adjust = self.env['bo.header'].search([('state', '=', 'draft'), ('bank_account.reference_name', 'ilike', 'adjust'), ('isHasbeenResetDraft', '=', False), ('date', '=', rec.date)], limit=1) #, ('website', '=', rec.website.id)
                      self.env['bo.bank.ledger.entries'].create_approval_log(
                                entry_no = self.env['bo.bank.ledger.entries'].search([], order='entry_no desc', limit=1).entry_no + 1 if self.env['bo.bank.ledger.entries'].search([], order='entry_no desc', limit=1) else 1,
                                posting_date = fields.Date.today(),
                                document_type = '1',
                                document_id_line = bo_line_bank_acc_holder.line_number,
                                document_id_header = bo_header_bank_acc_holder.id,
                                kategori = self.env['kategori.bo'].search([('name', '=', 'PINJAM WD')]).id,
                                # bank_account_id = self.env['res.partner.bank'].search([('reference_name', 'ilike', 'adjust')]).id,
                                bank_account_id = bo_header_bank_adjust.bank_account.id,
                                amount = -rec.amount,
                                is_from_request_tampung = True,
                                request_category_name = rec.category_id.name,
                        )
                    # Bank Ledger Entries if request is Bayar WD  
                    message = "Request has been inserted to Backoffice Line successfully!"
                    rec.message_post(body=message)
                elif not rec.bank_account_holder and rec.from_bank_account:
                    # REQUEST WD

                    ## Adjustment
                    bo_header_bank_adjust = self.env['bo.header'].search([('state', '=', 'draft'), ('bank_account.reference_name', 'ilike', 'adjust'), ('isHasbeenResetDraft', '=', False), ('date', '=', rec.date)], limit=1) #, ('website', '=', rec.website.id)
                    if bo_header_bank_adjust:
                        bo_line_bank_adjust = self.env['bo.line'].create({
                            'bo_id': bo_header_bank_adjust.id,
                            'kategori': self.env['kategori.bo'].search([('name', '=', 'PINJAM WD')]).id,
                            'description': 'Approval Request : ' + rec.name2 + ' From Bank ' + rec.from_bank_account.acc_number,
                            'bank_account': rec.from_bank_account.id,
                            'nominal': rec.amount,
                            'isExecuted': False,
                            'is_from_request_tampung': True,
                            'request_category_name': rec.category_id.name,
                            'transfer_bank_account': rec.from_bank_account.id,
                            'rekening_name': rec.nama_rekening if rec.nama_rekening else False,
                            'user_id': rec.member_id if rec.member_id else False,
                        })
                    else:
                        raise ValidationError(_('Cannot find any Backoffice Header for bank adjust %s!') % rec.from_bank_account.acc_number)
                    ## Adjustment

                    ## Backoffice Bank Tampung (From)
                    bo_header_from_bank_acc_tamp = self.env['bo.header'].search([('state', '=', 'draft'), ('bank_account', '=', rec.from_bank_account.id), ('isHasbeenResetDraft', '=', False), ('date', '=', rec.date)], limit=1) # , ('website', '=', rec.website.id)
                    if bo_header_from_bank_acc_tamp:
                        bo_line_from_bank_acc_tamp = self.env['bo.line'].create({
                            'bo_id': bo_header_from_bank_acc_tamp.id,
                            'kategori': rec.category_id.kategori.id,
                            'description': 'Approval Request : ' + rec.name2 + ' From Bank ' + rec.from_bank_account.acc_number,
                            'bank_account': rec.from_bank_account.id,
                            'nominal': -rec.amount,
                            'isExecuted': False,
                            'is_from_request_tampung': True,
                            'request_category_name': rec.category_id.name,
                            'rekening_name': rec.nama_rekening if rec.nama_rekening else False,
                            'user_id': rec.member_id if rec.member_id else False,
                        })
                    else:
                        raise ValidationError(_('Cannot find any Backoffice Header for bank account %s!') % rec.from_bank_account.acc_number)
                    ## Backoffice Bank Tampung (From)

                    # REQUEST WD
                    
                else:
                    raise ValidationError(_('Cannot find any Backoffice Header for this request!'))
                
                rec.isExecuted2 = True

#inherit journal item for journal entries, general ledger
# class inheritedJournalItem(models.Model):
#     _inherit = "account.move.line"

#     bankNumber = fields.Char(string="Bank")