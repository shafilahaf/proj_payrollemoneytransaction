from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from collections import defaultdict
import io, os
import xlsxwriter
from odoo.http import request
from werkzeug.wrappers import Response
import xlrd
import base64

class bo_header(models.Model):
    _name = 'bo.header'
    _description = 'Backoffice Header'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    initial_balance = fields.Float(string="Saldo Awal", store=True)
    # initial_balance = fields.Float(string="Saldo Awal", track_visibility='always', related='bank_account.balance_per_bank_initial_balance', readonly=True, store=True)

    name = fields.Char(string='Name', track_visibility='always')
    photo = fields.Binary(string='Photo')
    state = fields.Selection([('draft', 'To Submit'), ('submitted', 'To Review'), ('approved', 'Approved'), ('refused', 'Refused'), ('cancel', 'Cancelled'), ('done', 'Done')], string='Status', default='draft', required=True)
    bank = fields.Many2one('res.bank', string='Bank', track_visibility='always', required=True, domain="[('websites', '=', website)]")
    bank_account = fields.Many2one('res.partner.bank', string='Bank Account', track_visibility='always', domain="[('bank_id', '=', bank)]", required=True)
    kategori_header = fields.Many2one('kategori.bo', string='Kategori')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, track_visibility='always')
    shift = fields.Selection([('1', 'Pagi'), ('2', 'Malam')], string='Shift', track_visibility='always', required=True, store=True)

    bank_account_max_limit = fields.Float(string='Bank Account Max Limit', readonly=True, related='bank_account.max_limit')
    bank_account_type = fields.Selection([('dana', 'Dana'), ('pulsa', 'Pulsa'), ('bankgojek', 'Bank GoJek'), ('linkaja', 'LinkAja'), ('ovo', 'OVO')], string='Bank Account Type', readonly=True, related='bank_account.type')
    bank_account_exp_date = fields.Date(string='Bank Account Exp Date', readonly=True, related='bank_account.expired_date')
    bank_account_acc_holder = fields.Char(string='Bank Account Acc Holder', readonly=True, related='bank_account.acc_holder_name')
    bank_user_id = fields.Char(string='Bank User ID', readonly=True, related='bank_account.user_id')
    bank_password = fields.Char(string='Bank Password', readonly=True, related='bank_account.password')
    bank_token = fields.Char(string='Bank Token', readonly=True, related='bank_account.token')
    bank_type = fields.Selection(string='Bank Type', readonly=True, related='bank_account.type')
    hide_field = fields.Boolean(string='Hide Field', compute='_compute_hide_field')
    active = fields.Boolean(default=True)

    total_deposit = fields.Float(string='Total Depo', store=True, compute='_compute_totals')
    total_withdraw = fields.Float(string='Total WD', store=True, compute='_compute_totals')
    total_admin_fee = fields.Float(string='Total Biaya ADM', store=True, compute='_compute_totals')
    total_pulsa_fee = fields.Float(string='Total Uang Pulsa', store=True, compute='_compute_totals')
    total_pulsa_rate = fields.Float(string='Total Rate Pulsa', store=True, compute='_compute_totals')
    total_purchase_pulsa_credit = fields.Float(string='Total Isi Pulsa', store=True, compute='_compute_totals')
    total_saving = fields.Float(string='Total Saving',readonly=True,store=True, compute='_compute_totals')
    total_belom_lapor = fields.Float(string='Total Belum Lapor (BL)', store=True, compute='_compute_totals')
    total_salah_lapor = fields.Float(string='Total Salah',readonly=True,store=True, compute='_compute_totals')
    total_all_balance = fields.Float(string='Total All Balance', store=True, compute='_compute_totals')
    total_all_minus_nominal = fields.Float(string='Total All Minus Nominal', store=True, compute='_compute_totals')

    # Need for the backoffice reporting

    total_belom_transfer = fields.Float(string='Total Belom Transfer', store=True,readonly=True, compute='_compute_totals') #mistaketype
    total_lp = fields.Float(string='Total LP', store=True,readonly=True, compute='_compute_totals') #kategori
    total_pd = fields.Float(string='Total PD', store=True,readonly=True, compute='_compute_totals') #kategori
    total_save = fields.Float(string='Total Save', store=True,readonly=True, compute='_compute_totals') #kategori
    total_pinj = fields.Float(string='Total Pinj', store=True,readonly=True, compute='_compute_totals') #kategori

    #Bonus 
    bonus_header_ids = fields.Many2many('bo.bonus.header', string='Bonus Header', compute='_compute_bonus_header_ids')
    bonus_line_ids = fields.Many2many('bo.bonus.line', string='Bonus Line', compute='_compute_bonus_line_ids')

    total_bonus = fields.Float(string='Total Bonus', store=True, compute='_compute_bonus') #sum of bonus_line_ids where bonustype kategori = 1
    total_rebate = fields.Float(string='Total Rebate', store=True, compuute='_compute_bonus') #sum of bonus_line_ids where bonustype kategori = 2
    # Need for the backoffice reporting

    
    date = fields.Date(string='Date', default=fields.Date.today, required=True, track_visibility='always')
    website = fields.Many2one('bo.website', string='Website', track_visibility='always', required=True)
    total_depo_minus_wd = fields.Float(string='Total Deposit - Withdraw', store=True)

    selisih = fields.Boolean(string='Selisih', default=False, track_visibility='always', store=True)
    selisih_nominal = fields.Float(string='Selisih Nominal', store=True)
    total_qris_before = fields.Float(string='Total QRIS Before', store=True)
    total_qris_pending = fields.Float(string='Total QRIS Pending', store=True)

    isHasbeenResetDraft = fields.Boolean(string='Has been Reset to Draft', default=False, track_visibility='always', store=True)
    

    bo_line_ids = fields.One2many('bo.line', 'bo_id', string='Backoffice Lines')

            
    #Report Field - Additional
    piclines = fields.Char(string='PIC', compute='_compute_piclines')
    piclinesLocal = fields.Char(string='PIC Local', compute='_compute_piclinesLocal')
    piclinesLocalPH = fields.Char(string='PIC Local PH', compute='_compute_piclinesLocalPH')
    @api.depends('bo_line_ids')
    def _compute_piclines(self):
        for rec in self:
            rec.piclines = ', '.join(rec.bo_line_ids.filtered(lambda x: x.pic.stafftype.name == 'CS - ID').mapped('pic.name'))

    def _compute_piclinesLocal(self):
        for rec in self:
            rec.piclinesLocal = ', '.join(rec.bo_line_ids.filtered(lambda x: x.pic.stafftype.name == 'CS - KH').mapped('pic.name'))

    def _compute_piclinesLocalPH(self):
        for rec in self:
            rec.piclinesLocalPH = ', '.join(rec.bo_line_ids.filtered(lambda x: x.pic.stafftype.name == 'CS - PH').mapped('pic.name'))

    total_deposit_date = fields.Float(string='Total Deposit Date', store=True)
    total_withdraw_date = fields.Float(string='Total Withdraw Date', store=True)
    #Report Field - Additional

    #Get balance from bank account
    # @api.onchange('bank_account')
    # def _onchange_initial_balance(self):
    #     for rec in self:
    #         rec.initial_balance = 0
    #         count_bo_header = self.env['bo.header'].search_count([('bank_account', '=', rec.bank_account.id)])
    #         if count_bo_header == 0:
    #             rec.initial_balance = rec.bank_account.initial_balance
    #         else:
    #             rec.initial_balance = rec.bank_account.balance_per_bank_initial_balance

    # Get the bonus header and bonus line by the website, date
    @api.depends('website', 'date')
    def _compute_bonus_header_ids(self):
        for rec in self:
            rec.bonus_header_ids = self.env['bo.bonus.header'].search([('website', '=', rec.website.id), ('date', '=', rec.date)])

    @api.depends('bonus_header_ids')
    def _compute_bonus_line_ids(self):
        for rec in self:
            rec.bonus_line_ids = rec.bonus_header_ids.mapped('bo_bonusLine')

    # Open the wizard
    def fnOpenWizard(self):
        userlogin_groups = self.env.user.groups_id.filtered(lambda group: group.category_id.name == 'Backoffice')
        if userlogin_groups and userlogin_groups[0].isImportLines:
            return {
                'name': _('Backoffice Wizard'),
                'type': 'ir.actions.act_window',
                'res_model': 'backoffice.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_backoffice_id': self.id}
            }
        else:
            raise ValidationError(_('You are not authorized to access this button'))

        # return {
        #     'name': _('Backoffice Wizard'),
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'backoffice.wizard',
        #     'view_mode': 'form',
        #     'target': 'new',
        #     'context': {'default_backoffice_id': self.id}
        # }

    @api.depends('bonus_line_ids')
    def _compute_bonus(self):
        for rec in self:
            rec.total_bonus = sum(rec.bonus_line_ids.filtered(lambda x: x.bonustype.kategori == '1').mapped('nominal'))
            rec.total_rebate = sum(rec.bonus_line_ids.filtered(lambda x: x.bonustype.kategori == '2').mapped('nominal'))
    # Get the bonus header and bonus line by the website, date  
    

    @api.onchange('bank_account')
    def _onchange_bank_account(self):
        """
        Configure bank account based on bank"""
        if self.bank_account:
            if self.bank_account.id in self.env['bo.header'].search([('state', '=', 'draft')]).mapped('bank_account.id'):
                bank_account_name = self.env['res.partner.bank'].search([('id', '=', self.bank_account.id)], limit=1).acc_number
                draft_bo_name = self.env['bo.header'].search([('state', '=', 'draft'), ('bank_account', '=', self.bank_account.id)], limit=1).name
                raise ValidationError('Bank Account %s already exist in Backoffice Journal Number %s' % (bank_account_name, draft_bo_name))
                #raise ValidationError('Bank Account already exist in draft state')
            
            if self.bank_account.reference_name != False:
                self.name = self.date.strftime('%m%d%Y') + '/' + self.user_id.name + '/' + self.website.name + '/' + self.bank_account.reference_name
            else:
                raise ValidationError('Reference Name is empty. Please fill the reference name first in the bank account')
            # self.name = self.date.strftime('%m%d%Y') + '/' + self.user_id.name + '/' + self.website.name + '/' + self.bank_account.reference_name

    @api.depends('bo_line_ids', 'initial_balance')
    def _compute_totals(self):
        for rec in self:
            rec.total_deposit = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'DP').mapped('nominal'))
            rec.total_withdraw = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'WD').mapped('nominal'))
            rec.total_admin_fee = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'ADM').mapped('nominal'))
            rec.total_pulsa_fee = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'UP').mapped('nominal'))
            rec.total_pulsa_rate = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'RP').mapped('nominal'))
            rec.total_purchase_pulsa_credit = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'PULSA').mapped('nominal'))
            rec.total_saving = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'SAVE').mapped('nominal'))
            rec.total_belom_lapor = sum(rec.bo_line_ids.filtered(lambda x: x.mistaketype.name == 'BL').mapped('nominal'))
            rec.total_salah_lapor = sum(rec.bo_line_ids.filtered(lambda x: x.mistaketype.name == 'SALAH').mapped('nominal'))
            # rec.total_all_balance = sum(rec.bo_line_ids.mapped('nominal'))
            rec.total_all_balance = sum(rec.bo_line_ids.mapped('nominal')) + rec.initial_balance
            # rec.total_all_minus_nominal = sum(rec.bo_line_ids.filtered(lambda x: x.nominal < 0).mapped('nominal'))
            rec.total_all_minus_nominal = sum(rec.bo_line_ids.filtered(lambda x: x.nominal < 0 and x.kategori.name != 'ADM').mapped('nominal'))
            rec.total_depo_minus_wd = rec.total_deposit + rec.total_withdraw

            # Need for dashboard report
            rec.total_belom_transfer = sum(rec.bo_line_ids.filtered(lambda x: x.mistaketype.name == 'BT').mapped('nominal'))
            rec.total_lp = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'LP').mapped('nominal'))
            rec.total_pd = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'PD').mapped('nominal'))
            rec.total_save = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'SAVE').mapped('nominal'))
            rec.total_pinj = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'PINJAM').mapped('nominal'))

            # Report Field - Additional
            rec.total_deposit_date = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'DP' and x.create_on.date() == rec.date).mapped('nominal'))
            rec.total_withdraw_date = sum(rec.bo_line_ids.filtered(lambda x: x.kategori.name == 'WD' and x.create_on.date() == rec.date).mapped('nominal'))
            # Report Field - Additional

    @api.onchange('bo_line_ids')
    def _onchange_bo_line_ids(self):
        """
        Get total balance from all lines"""
        for rec in self:
            if rec.bo_line_ids:
                for line in rec.bo_line_ids:
                    if line.transaction_id:
                        if len(rec.bo_line_ids.filtered(lambda x: x.transaction_id == line.transaction_id)) > 1:
                            raise ValidationError(_('Cannot add line with same transaction id'))
    
    def _creation_message(self):
        """
        Create Message in chatter"""
        return _('The %s created') % self.name

    def _write_message(self, vals):
        """
        Write Message in chatter"""
        return _('The %s updated') % self.name

    
    def action_draft(self):
        """
        Set state to draft"""
        for rec in self:
            userlogin_groups = self.env.user.groups_id.filtered(lambda group: group.category_id.name == 'Backoffice')
            if userlogin_groups and userlogin_groups[0].isResetToDraft:
                # rec.write({'state': 'draft'})
                rec.write({'state': 'draft', 'isHasbeenResetDraft': True})
            else:
                raise ValidationError(_('You are not authorized to access this button'))
        # for rec in self:
        #     rec.write({'state': 'draft'})

    
    def action_submitted(self):
        """
        Set state to submitted"""
        for rec in self:
            rec.write({'state': 'submitted'})

    
    def action_cancel(self):
        """
        Set state to cancel"""
        for rec in self:
            rec.write({'state': 'cancel'})

    def action_add_five_boline(self):
        """
        Add 5 Backoffice Lines """
        for rec in self:
            last_transaction_id = rec.bo_line_ids[-1].transaction_id if rec.bo_line_ids else ''
            transaction_id_parts = last_transaction_id.split('-') if last_transaction_id else []

            counter = int(transaction_id_parts[-1]) if transaction_id_parts else 0

            # Add 7 hours
            current_time = (datetime.now() + timedelta(hours=7)).strftime('%H%M%S')

            for i in range(1, 6):
                counter += 1
                transaction_id = '{}-{}-{}-{}'.format(
                    datetime.now().strftime('%Y%m%d'),
                    rec.website.initial_website,
                    current_time,
                    counter
                )

                rec.bo_line_ids.create({
                    'bo_id': rec.id,
                    'kategori': rec.kategori_header.id,
                    # 'rekening_name': "-",
                    'nominal': 0,
                    'transaction_id': transaction_id,
                })

    # @api.onchange('bank')
    # def _onchange_website_bank(self):
    #     """
    #     Set name based on date, user id, and bank"""
    #     if self.bank:
    #         # self.name = self.date.strftime('%m%d%Y') + '/' + self.user_id.name + '/' + self.bank.name
    #         self.name = self.date.strftime('%m%d%Y') + '/' + self.user_id.name + '/' + self.website.name + '/' + self.bank_account.reference_name

    
    @api.depends('bank_account')
    def _compute_hide_field(self):
        """
        If Bank Account is filled, Hide Field will be True"""
        for rec in self:
            if rec.bank_account:
                rec.hide_field = True
            else:
                rec.hide_field = False
            
    
    def action_done(self):
        """
        Set state to done"""
        for rec in self:
            rec.write({'state': 'done'})

    @api.constrains('bo_line_ids')
    def _check_bo_line_ids(self):
        """
        Cannot save if the nominal in the line is 0"""
        for rec in self:
            for line in rec.bo_line_ids:
                if line.nominal == 0:
                    raise ValidationError(_('Cannot save with nominal 0'))

    def unlink(self):
        # Delete bank ledger entries
        for rec in self:
            ledger_entries = self.env['bo.bank.ledger.entries'].search([('document_id_header', '=', rec.id)])
            ledger_entries.unlink()

        # Cannot delete if the state is not draft
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You cannot delete a request that is not in draft state.'))
        return super(bo_header, self).unlink()

    def generate_daily_reports_noon(self):
        daily_report_obj = self.env['bo.daily.reports']
        today = fields.Date.today()
        yesterday = today - timedelta(days=20)
        
        headers = self.search([('date', '>=', yesterday),('date', '<=', today), ('state', '=', 'done'), ('shift', '=', '1')])
        lines = self.env['bo.line'].search([('bo_id', 'in', headers.ids)])

        report_data = defaultdict(lambda: defaultdict(set))

        for line in lines:
            header = line.bo_id
            report_key = (header.date, header.shift, header.website.id, header.bank_account.id)

            if line.pic.stafftype.name.startswith('CS - '):
                staff_type = line.pic.stafftype.name
                report_data[report_key][staff_type].add(line.pic.name)

        
        for report_key, staff_data in report_data.items():
            date, shift, website_id, bank_account_id = report_key
            website = self.env['bo.website'].browse(website_id)
            bank_account = self.env['res.partner.bank'].browse(bank_account_id)

            selisih = headers.filtered(lambda x: x.date == date and x.shift == shift and x.website.id == website_id and x.bank_account.id == bank_account_id).mapped('selisih')
            selisih = any(selisih)
            if selisih:
                selisih = 'Selisih'
            else:
                selisih = 'Tidak Selisih'

            # Total DP
            total_dp = sum(headers.filtered(lambda x: x.date == date and x.shift == shift and x.website.id == website_id and x.bank_account.id == bank_account_id).mapped('total_deposit'))
            # Total WD
            total_wd = sum(headers.filtered(lambda x: x.date == date and x.shift == shift and x.website.id == website_id and x.bank_account.id == bank_account_id).mapped('total_withdraw'))
            # Total QRIS before
            total_qris_before = sum(headers.filtered(lambda x: x.date == date and x.shift == shift and x.website.id == website_id and x.bank_account.id == bank_account_id).mapped('total_qris_before'))
            # Total QRIS pending
            total_qris_pending = sum(headers.filtered(lambda x: x.date == date and x.shift == shift and x.website.id == website_id and x.bank_account.id == bank_account_id).mapped('total_qris_pending'))

            line = self.env['bo.line'].search([('kategori.name', '=', 'PINJAM')])
            total_hutang_tampung = sum(line.mapped('nominal'))

            shiftname = 'Pagi'
            
            report_vals = {
                'name': f'Daily Report {website.name} {date} {bank_account.acc_holder_name} {shiftname}',
                'website': website.id,
                'date': date,
                'shift': shift,
                'selisih': selisih,
                'bo_header_bank_account': bank_account.id, 
                'created_by_name_staff_id': ', '.join(staff_data.get('CS - ID', [])),
                'created_by_name_staff_kh': ', '.join(staff_data.get('CS - KH', [])),
                'created_by_name_staff_ph': ', '.join(staff_data.get('CS - PH', [])),
                'total_dp': total_dp,
                'total_wd': total_wd,
                'total_hutang_tampung': total_hutang_tampung,
                'total_qris_before': total_qris_before,
                'total_qris_pending': total_qris_pending,
            }

            existing_report = daily_report_obj.search([
                ('website', '=', website.id),
                ('date', '=', date),
                ('shift', '=', shift),
                ('bo_header_bank_account', '=', bank_account.id)
            ])

            if not existing_report:
                daily_report_obj.create(report_vals)
            else:
                existing_report.write(report_vals)

    def generate_daily_reports_night(self):
        daily_report_obj = self.env['bo.daily.reports']
        today = fields.Date.today()
        yesterday = today - timedelta(days=20)
        
        headers = self.search([('date', '>=', yesterday),('date', '<=', today), ('state', '=', 'done'), ('shift', '=', '2')])
        lines = self.env['bo.line'].search([('bo_id', 'in', headers.ids)])

        report_data = defaultdict(lambda: defaultdict(set))

        for line in lines:
            header = line.bo_id
            report_key = (header.date, header.shift, header.website.id, header.bank_account.id)

            if line.pic.stafftype.name.startswith('CS - '):
                staff_type = line.pic.stafftype.name
                report_data[report_key][staff_type].add(line.pic.name)

        
        for report_key, staff_data in report_data.items():
            date, shift, website_id, bank_account_id = report_key
            website = self.env['bo.website'].browse(website_id)
            bank_account = self.env['res.partner.bank'].browse(bank_account_id)

            selisih = headers.filtered(lambda x: x.date == date and x.shift == shift and x.website.id == website_id and x.bank_account.id == bank_account_id).mapped('selisih')
            selisih = any(selisih)
            if selisih:
                selisih = 'Selisih'
            else:
                selisih = 'Tidak Selisih'

            # Total DP
            total_dp = sum(headers.filtered(lambda x: x.date == date and x.shift == shift and x.website.id == website_id and x.bank_account.id == bank_account_id).mapped('total_deposit'))
            # Total WD
            total_wd = sum(headers.filtered(lambda x: x.date == date and x.shift == shift and x.website.id == website_id and x.bank_account.id == bank_account_id).mapped('total_withdraw'))
            # Total QRIS before
            total_qris_before = sum(headers.filtered(lambda x: x.date == date and x.shift == shift and x.website.id == website_id and x.bank_account.id == bank_account_id).mapped('total_qris_before'))
            # Total QRIS pending
            total_qris_pending = sum(headers.filtered(lambda x: x.date == date and x.shift == shift and x.website.id == website_id and x.bank_account.id == bank_account_id).mapped('total_qris_pending'))

            line = self.env['bo.line'].search([('kategori.name', '=', 'PINJAM')])
            total_hutang_tampung = sum(line.mapped('nominal'))

            shiftname = 'Malam'

            report_vals = {
                'name': f'Daily Report {website.name} {date} {bank_account.acc_holder_name} {shiftname}',
                'website': website.id,
                'date': date,
                'shift': shift,
                'selisih': selisih,
                'bo_header_bank_account': bank_account.id, 
                'created_by_name_staff_id': ', '.join(staff_data.get('CS - ID', [])),
                'created_by_name_staff_kh': ', '.join(staff_data.get('CS - KH', [])),
                'created_by_name_staff_ph': ', '.join(staff_data.get('CS - PH', [])),
                'total_dp': total_dp,
                'total_wd': total_wd,
                'total_hutang_tampung': total_hutang_tampung,
                'total_qris_before': total_qris_before,
                'total_qris_pending': total_qris_pending,
            }

            existing_report = daily_report_obj.search([
                ('website', '=', website.id),
                ('date', '=', date),
                ('shift', '=', shift),
                ('bo_header_bank_account', '=', bank_account.id)
            ])

            if not existing_report:
                daily_report_obj.create(report_vals)
            else:
                existing_report.write(report_vals)
    

    def delete_bulk_bo_line(self):
        """
        Delete all bo_line_ids"""
        for header in self:
            userlogin_groups = self.env.user.groups_id.filtered(lambda group: group.category_id.name == 'Backoffice')
            if userlogin_groups and userlogin_groups[0].isBulkDelete:
                header.bo_line_ids.unlink()
            else:
                raise ValidationError(_('You are not authorized to access this button'))

    def show_backoffice_line(self):
        """
        Show backoffice line"""
        # self.ensure_one()
        # action = self.env.ref('backoffice.backoffice_lines_action').read()[0]
        # action['domain'] = [('bo_id', '=', self.id)]
        # return action
        userlogin_groups = self.env.user.groups_id.filtered(lambda group: group.category_id.name == 'Backoffice')
        if userlogin_groups and userlogin_groups[0].isShowBackofficeLine:
            self.ensure_one()
            action = self.env.ref('backoffice.backoffice_lines_action').read()[0]
            action['domain'] = [('bo_id', '=', self.id)]
            return action
        else:
            raise ValidationError(_('You are not authorized to access this button'))

class bo_line(models.Model):
    _name = 'bo.line'
    _description = 'Backoffice Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'line_number asc'

    bo_id = fields.Many2one('bo.header', string='Backoffice', ondelete='cascade', readonly=True)

    line_number = fields.Integer(string='Line Number', readonly=True, store=True, compute='_compute_line_number')
    create_on = fields.Datetime(string='Input Date', default=fields.Datetime.now)
    last_update = fields.Datetime(string='Last Update', default=fields.Datetime.now, readonly=True)
    last_update_by = fields.Many2one('res.users', string='Last Update By', default=lambda self: self.env.user, readonly=True)
    pic = fields.Many2one('res.users', string='User ID', default=lambda self: self.env.user, readonly=True)
    mistaketype = fields.Many2one('mistaketype.bo', string='Mistake Type')
    kategori = fields.Many2one('kategori.bo', string='Kategori')
    kategori_name = fields.Char(related='kategori.name', string='Kategori Name', readonly=True, store=True)
    description = fields.Char(string='Deskripsi')
    rekening_name = fields.Char(string='Nama Rekening')
    user_id = fields.Char(string="Member ID")
    bank_account = fields.Many2one(related='bo_id.bank_account')
    nominal = fields.Float(string='Nominal', required=True)
    state = fields.Selection(related='bo_id.state', string='Status', readonly=True, store=True)
    bo_header_name = fields.Char(related='bo_id.name', string='Backoffice Name', readonly=True, store=True)
    transfer_bank_account = fields.Many2one('res.partner.bank', string='Transfer Bank Account', store=True)
    read_only_field = fields.Boolean(string='Read Only', compute='_compute_read_only_field')
    required_field = fields.Boolean(string='Required', compute='_compute_required_field')
    stateline = fields.Selection([('draft', 'Open'), ('toapprove', 'To Approve'), ('approved', 'Approved'), ('refused', 'Refused')], string='Status', default='draft', required=True)
    bo_header_website = fields.Many2one(related='bo_id.website', string='Website', readonly=True, store=True)
    isExecuted = fields.Boolean(string='Is Executed')
    is_from_request_tampung = fields.Boolean(string='Is From Request Tampung', default=False)
    request_category_name = fields.Char(string='Request Category Name', readonly=True, store=True)

    transaction_id = fields.Char(string='Transaction ID')

    nominal_wd = fields.Float(string='Nominal WD', compute='_compute_nominal_wd', store=True)
    is_nominal_wd = fields.Boolean(string='Is Nominal WD', store=True, compute='_compute_is_nominal_wd')


    @api.depends('nominal', 'nominal_wd')
    def _compute_is_nominal_wd(self):
        for rec in self:
            if rec.nominal >= rec.nominal_wd:
                rec.is_nominal_wd = True
            else:
                rec.is_nominal_wd = False
    
    @api.depends('bo_id')
    def _compute_nominal_wd(self):
        for rec in self:
            if rec.bo_id:
                setup = self.env['bo.setups'].search([('is_active', '=', True)])
                rec.nominal_wd = setup.nominal_wd

    @api.onchange('last_update_by')
    def _onchange_last_update_by(self):
        """
        Set last update by based on user login"""
        self.create_on = fields.Datetime.now()

    @api.onchange('bo_id', 'bo_id.website', 'bo_id.website.is_automatic_transactionid')
    def _onchange_transaction_id(self):
        """
        Set transaction id based on website header configuration"""
        if self.bo_id.website:
            if self.bo_id.website.is_automatic_transactionid:
                # time + 7 hours
                current_time = (datetime.now() + timedelta(hours=7)).strftime('%H%M%S')
                self.transaction_id = self.create_on.strftime('%Y%m%d') + '-' + self.bo_id.website.initial_website + '-' + current_time
            

    @api.depends('bo_id')
    def _compute_line_number(self):
        """
        Get line number from backoffice"""
        for rec in self:
            if rec.bo_id:
                rec.line_number = len(rec.bo_id.bo_line_ids)
            else:
                rec.line_number = 0
            

    @api.onchange('bo_id', 'mistaketype', 'kategori', 'rekening_name', 'user_id', 'bank_account', 'nominal', 'description', 'last_update_by', 'create_on')
    def _onchange_last_update(self):
        """
        Update last update field"""
        self.last_update = fields.Datetime.now()
        self.last_update_by = self.env.user

    @api.onchange('mistaketype')
    def _onchange_mistaketype(self):
        """
        If Mistake Type is filled, Kategori will be empty"""
        if self.mistaketype:
            self.kategori = False

    @api.onchange('kategori')
    def _onchange_kategori(self):
        """
        If Kategori is filled, Mistake Type will be empty"""
        if self.kategori:
            self.mistaketype = False

    @api.onchange('nominal')
    def _onchange_nominal(self):
        if self.transfer_bank_account and self.nominal != 0:
            bo_header = self.env['bo.header'].search([('bank_account', '=', self.transfer_bank_account.id), ('state', '=', 'draft')], limit=1)
            if bo_header:
                # Create new line
                bo_line = self.env['bo.line'].create({
                    'bo_id': bo_header.id,
                    'kategori': self.kategori.id,
                    'description': self.description,
                    'rekening_name': self.rekening_name,
                    'user_id': self.user_id,
                    'bank_account': self.bank_account.id,
                    # 'nominal': self.nominal * -1 if self.kategori.name == 'PD' else self.nominal,
                    'nominal': self.nominal * -1,
                    'transfer_bank_account': self.transfer_bank_account.id,
                    'transaction_id': self.transaction_id,
                })
            else:
                raise ValidationError(_('No Backoffice Transaction with the same bank account found. Please create a new Backoffice Header with the same bank account first.'))
    
    @api.onchange('transfer_bank_account')
    def _onchange_transfer_bank_account(self):
        """
        If Kategori is 'PD', create a new line in backoffice with the same bank account as in the header.
        """
        if self.transfer_bank_account and self.nominal != 0:
            bo_header = self.env['bo.header'].search([('bank_account', '=', self.transfer_bank_account.id), ('state', '=', 'draft')], limit=1)
            if bo_header:
                # Create new line
                bo_line = self.env['bo.line'].create({
                    'bo_id': bo_header.id,
                    'kategori': self.kategori.id,
                    'description': self.description,
                    'rekening_name': self.rekening_name,
                    'user_id': self.user_id,
                    'bank_account': self.bank_account.id,
                    # 'nominal': self.nominal * -1 if self.kategori.name == 'PD' else self.nominal,
                    'nominal' : self.nominal * -1,
                    'transfer_bank_account': self.transfer_bank_account.id,
                    'transaction_id': self.transaction_id,
                })
            else:
                raise ValidationError(_('No Backoffice Transaction with the same bank account found. Please create a new Backoffice Header with the same bank account first.'))

    @api.onchange('bo_id')
    def _onchange_bo_id(self):
        """
        Get Kategori from Header"""
        if self.bo_id:
            self.kategori = self.bo_id.kategori_header
    
    @api.depends('kategori')
    def _compute_required_field(self):
        """
        If Kategori is PD or SAVE, Required Field will be True"""
        for rec in self:
            if rec.kategori.name == 'PD' or rec.kategori.name == 'SAVE':
                rec.required_field = True
            else:
                rec.required_field = False

    @api.depends('kategori')
    def _compute_read_only_field(self):
        """
        If Kategori is PD or SAVE, Read Only Field will be True"""
        for rec in self:
            if rec.kategori.name == 'PD' or rec.kategori.name == 'SAVE':
                rec.read_only_field = True
            else:
                rec.read_only_field = False

    @api.model
    def create(self, vals):
        # Create the bo.line record
        line = super(bo_line, self).create(vals)

        # Create BankLedgerEntries record
        # If isExecuted is True not create BankLedgerEntries record
        if line.isExecuted:
            return line
        else:
            ledger_entry_from_vals = {
                'entry_no': self.env['bo.bank.ledger.entries'].search([], order='entry_no desc', limit=1).entry_no + 1,
                'posting_date': line.bo_id.date,
                'document_type': '1',
                'document_id_header': line.bo_id.id,
                'document_id_line': line.id,
                'kategori': line.kategori.id,
                'mistaketype': line.mistaketype.id,
                'bank_account_id': line.bank_account.id,
                'bank_account_no': line.bank_account.acc_number,
                'bank_account_name': line.bank_account.acc_holder_name,
                'is_from_request_tampung': line.is_from_request_tampung if line.is_from_request_tampung else False,
                'request_category_name': line.request_category_name if line.request_category_name else False,
                # 'amount': line.nominal if not line.transfer_bank_account else -line.nominal,
                'amount': line.nominal,

            }
            self.env['bo.bank.ledger.entries'].create(ledger_entry_from_vals) 

        # ledger_entry_from_vals = {
        #     'entry_no': self.env['bo.bank.ledger.entries'].search([], order='entry_no desc', limit=1).entry_no + 1,
        #     'posting_date': line.bo_id.date,
        #     'document_type': '1',
        #     'document_id_header': line.bo_id.id,
        #     'document_id_line': line.id,
        #     'kategori': line.kategori.id,
        #     'mistaketype': line.mistaketype.id,
        #     'bank_account_id': line.bank_account.id,
        #     'bank_account_no': line.bank_account.acc_number,
        #     'bank_account_name': line.bank_account.acc_holder_name,
        #     'amount': line.nominal if not line.transfer_bank_account else -line.nominal,
        # }
        # self.env['bo.bank.ledger.entries'].create(ledger_entry_from_vals)

        # if line.transfer_bank_account:
        #     # Create BankLedgerEntries record for the transfer_to bank account
        #     ledger_entry_to_vals = {
        #         'entry_no': self.env['bo.bank.ledger.entries'].search([], order='entry_no desc', limit=1).entry_no + 1,
        #         'posting_date': line.bo_id.date,
        #         'document_type': '1',
        #         'document_id_header': line.bo_id.id,
        #         'document_id_line': line.id,
        #         'kategori': line.kategori.id,
        #         'mistaketype': line.mistaketype.id,
        #         'bank_account_id': line.transfer_bank_account.id,
        #         'bank_account_no': line.transfer_bank_account.acc_number,
        #         'bank_account_name': line.transfer_bank_account.acc_holder_name,
        #         'amount': -line.nominal if not line.transfer_bank_account else line.nominal,
        #     }
        #     self.env['bo.bank.ledger.entries'].create(ledger_entry_to_vals)

        # Post a message in the chatter
        message = _("A Member ID: %s, Mistake Type: %s, Category: %s, Rekening Name: %s, Bank Account: %s with Nominal: %s has been added to the back office system. Line Number: %s.") % (line.user_id, line.mistaketype.name, line.kategori.name, line.rekening_name, line.bank_account.acc_number, line.nominal, line.line_number)
        line.bo_id.message_post(body=message)

        return line
    

    def unlink(self):
        # Delete BankLedgerEntries
        for rec in self:
            ledger_entries = self.env['bo.bank.ledger.entries'].search([('document_id_line', '=', rec.id)])
            ledger_entries.unlink()

        # Post a message in the chatter
        message = _("A Member ID: %s, Mistake Type: %s, Category: %s, Rekening Name: %s, Bank Account: %s with Nominal: %s has been deleted from the back office system. Line Number: %s.") % (rec.user_id, rec.mistaketype.name, rec.kategori.name, rec.rekening_name, rec.bank_account.acc_number, rec.nominal, rec.line_number)
        rec.bo_id.message_post(body=message)

        return super(bo_line, self).unlink()

    def write(self, vals):
        # Write BankLedgerEntries
        for rec in self:
            if 'nominal' in vals:
                ledger_entries = self.env['bo.bank.ledger.entries'].search([('document_id_line', '=', rec.id)])
                for ledger_entry in ledger_entries:
                    ledger_entry.amount = vals['nominal'] if not rec.transfer_bank_account else -vals['nominal']
                    if rec.transfer_bank_account:
                        ledger_entry.amount = -vals['nominal'] if not rec.transfer_bank_account else vals['nominal']

        # Post a message in the chatter
        message = _("A Member ID: %s, Mistake Type: %s, Category: %s, Rekening Name: %s, Bank Account: %s with Nominal: %s has been updated to the back office system. Line Number: %s.") % (rec.user_id, rec.mistaketype.name, rec.kategori.name, rec.rekening_name, rec.bank_account.acc_number, rec.nominal, rec.line_number)
        rec.bo_id.message_post(body=message)

        return super(bo_line, self).write(vals)

    @api.onchange('kategori', 'nominal')
    def _onchange_kategori_nominal(self):
        for rec in self:
            if rec.kategori.name == 'WD' and rec.nominal >= rec.nominal_wd:
                rec.stateline = 'toapprove'
            else:
                rec.stateline = 'draft'

    
    def action_approve_wd(self):
        """
        Set state to approved"""
        for rec in self:
            self.ensure_one()
            rec.write({'stateline': 'approved'})
    

    def action_approval(self):
        """
        Set state to toapproved"""
        for rec in self:
            self.ensure_one()
            leader_group = self.env.ref('backoffice.bo_admin_group')
            leader_user = leader_group.users

            for leader in leader_user:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'res_id': self.id,
                    'res_model_id': self.env.ref('backoffice.model_bo_line').id,
                    'summary': 'Backoffice Line %s' % self.id,
                    'user_id': leader.id,
                    'date_deadline': datetime.today(),
                    'note': 'Backoffice Line %s' % self.id,
                })

            rec.write({'stateline': 'toapprove'})

    def action_approve(self):
        """
        Set state to approved"""
        for rec in self:
            userlogin_groups = self.env.user.groups_id.filtered(lambda group: group.category_id.name == 'Backoffice')
            if userlogin_groups and userlogin_groups[0].isApproveBlBtl:
                if rec.stateline == 'toapprove':
                    activity = self.env['mail.activity'].search([('res_id', '=', rec.id), ('res_model_id', '=', self.env.ref('backoffice.model_bo_line').id)])
                    activity.unlink()
                    rec.write({'stateline': 'approved'})

                if rec.stateline == 'approved':
                    bo_draft = self.env['bo.header'].search([('state', '=', 'draft'), ('website', '=', rec.bo_header_website.id), ('bank_account', '=', rec.bank_account.id)], limit=1)
                    if bo_draft:
                        if rec.mistaketype.name == 'BL':
                            # Get the bo.setups based on the mistaketype
                            # bo_setup = self.env['bo.setups'].search([('mistake_type', '=', rec.mistaketype.id)], limit=1)

                            bo_setup = self.env['bo.setups'].search([('mistake_type', '=', rec.mistaketype.id), ('is_active', '=', True)], limit=1)
                            
                            if not bo_setup.category_for_claim:
                                raise ValidationError(_('Category for Claim is not set in Backoffice Setup'))

                            if not bo_setup.mistake_type_for_claim:
                                raise ValidationError(_('Mistake Type for Claim is not set in Backoffice Setup'))
                            
                            bo_draft_bank_adjust = self.env['bo.header'].search([('state', '=', 'draft'), ('website', '=', rec.bo_header_website.id), ('bank_account.reference_name', 'ilike', 'adjust')], limit=1)
                            if not bo_draft_bank_adjust:
                                raise ValidationError(_('Backoffice with Bank Account Adjust is not exist in draft state'))
                            else:
                                bo_draft_bank_adjust.bo_line_ids.create({
                                    'bo_id': bo_draft_bank_adjust.id,
                                    'kategori': bo_setup.category_for_claim.id,
                                    'mistaketype': bo_setup.mistake_type_for_claim.id,
                                    'description': rec.description,
                                    'rekening_name': rec.rekening_name,
                                    'user_id': rec.user_id,
                                    'bank_account': rec.bank_account.id,
                                    'nominal': rec.nominal,
                                })

                            # bo_draft.bo_line_ids.create({
                            #     'bo_id': bo_draft.id,
                            #     'kategori': bo_setup.category_for_claim.id,
                            #     'mistaketype': bo_setup.mistake_type_for_claim.id,
                            #     'description': rec.description,
                            #     'rekening_name': rec.rekening_name,
                            #     'user_id': rec.user_id,
                            #     'bank_account': rec.bank_account.id,
                            #     'nominal': rec.nominal,
                            # })
                            
                        elif rec.mistaketype.name == 'BT':
                            bo_draft.bo_line_ids.create({
                                'bo_id': bo_draft.id,
                                'kategori': self.env['kategori.bo'].search([('name', '=', 'WD')], limit=1).id,
                                'description': rec.description, # +Claimed
                                'rekening_name': rec.rekening_name,
                                'user_id': rec.user_id,
                                'bank_account': rec.bank_account.id,
                                'nominal': rec.nominal,
                            })
                    else:
                        raise ValidationError('Backoffice with Bank Account %s is not exist in draft state' % rec.bank_account.acc_number)
            else:
                raise ValidationError(_('You are not authorized to access this button'))
                
    def action_approved_wd(self):
        """
        Set state to approved"""
        for rec in self:
            userlogin_groups = self.env.user.groups_id.filtered(lambda group: group.category_id.name == 'Backoffice')
            if userlogin_groups and userlogin_groups[0].isApproveWD:
                if rec.stateline == 'toapprove':
                    activity = self.env['mail.activity'].search([('res_id', '=', rec.id), ('res_model_id', '=', self.env.ref('backoffice.model_bo_line').id)])
                    activity.unlink()
                    rec.write({'stateline': 'approved'})
            else:
                raise ValidationError(_('You are not authorized to access this button'))             

    def action_refuse(self):
        for rec in self:
            if rec.stateline == 'toapprove':
                activity = self.env['mail.activity'].search([('res_id', '=', rec.id), ('res_model_id', '=', self.env.ref('backoffice.model_bo_line').id)])
                activity.unlink()
                rec.write({'stateline': 'refused'})

class ReportBackoffice(models.AbstractModel):
    _name = 'report.backoffice.report_backoffice'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Get data for report"""
        bo_header = self.env['bo.header'].browse(docids)
        bo_line  = self.env['bo.line'].search([('bo_id', '=', bo_header.id)])
        bo_bonusheader = self.env['bo.bonus.header'].search([('website', '=', bo_header.website.id), ('date', '=', bo_header.date), ('shift', '=', bo_header.shift)])
        bo_bonusline = self.env['bo.bonus.line'].search([('bo_bonusheader_id', '=', bo_bonusheader.id)])

        nominal_sum_by_type = defaultdict(float)
        for line in bo_bonusline:
            nominal_sum_by_type[line.bonustype.name] += line.nominal

        nominal_sum_by_kategori_pd = defaultdict(float)
        for line in bo_line:
            if line.kategori.name == 'PD':
                nominal_sum_by_kategori_pd[line.transfer_bank_account.acc_number] += line.nominal
        
        return {
            'doc_ids': docids,
            'doc_model': 'bo.header',
            'docs': bo_header,
            'bo_bonusheader': bo_bonusheader,
            'bo_bonusline': bo_bonusline,
            'nominal_sum_by_type': nominal_sum_by_type,
            'nominal_sum_by_kategori_pd': nominal_sum_by_kategori_pd,
        }

class backoffcie_wizard(models.TransientModel):
    _name = 'backoffice.wizard'
    _description = 'Backoffice Wizard'

    uploadfile = fields.Binary(string='Upload Excel File')
    backoffice_id = fields.Many2one('bo.header', string='Bonus Header', ondelete='cascade', readonly=True)

    def generate_transaction_id(self, rec):
        last_transaction_id = rec.bo_line_ids[-1].transaction_id if rec.bo_line_ids else ''
        transaction_id_parts = last_transaction_id.split('-') if last_transaction_id else []

        counter = int(transaction_id_parts[-1]) if transaction_id_parts else 0

        current_time = (datetime.now() + timedelta(hours=7)).strftime('%H%M%S')
        counter += 1
        transaction_id = '{}-{}-{}-{}'.format(
            datetime.now().strftime('%Y%m%d'),
            rec.website.initial_website,
            current_time,
            counter
        )
        return transaction_id
    
    def fnimportBackofficeLines(self):
        try:
            book = xlrd.open_workbook(file_contents=base64.decodestring(self.uploadfile))
        except xlrd.biffh.XLRDError:
            raise UserError('Only excel files are supported.')

        for sheet in book.sheets():
            if sheet.name == 'Sheet1':
                for row in range(sheet.nrows):
                    try:
                        if row >= 1:
                            row_values = sheet.row_values(row)
                            vals = self.fnCreateBonusLineRec(row_values)

                            transaction_id = self.generate_transaction_id(self.backoffice_id)

                            new_line = self.env['bo.line'].create({
                                'bo_id': self.backoffice_id.id,
                                'nominal': vals['nominal'],
                                'rekening_name': vals['rekening_name'],
                                'user_id': vals['user_id'],
                                'transfer_bank_account': vals['transfer_bank_account'],
                                'description': vals['description'],
                                'kategori': vals['kategori'],
                                'mistaketype': vals['mistaketype'],
                                'transaction_id': transaction_id,
                                'create_on': vals['create_on'],
                            })

                            if new_line.transfer_bank_account:
                                bo_header_same_bank_account = self.env['bo.header'].search([
                                    ('bank_account', '=', new_line.transfer_bank_account.id),
                                    ('state', '=', 'draft')
                                ], limit=1)
                                if bo_header_same_bank_account:
                                    bo_line_same_vals = {
                                        'bo_id': bo_header_same_bank_account.id,
                                        'kategori': new_line.kategori.id,
                                        'description': new_line.description,
                                        'rekening_name': new_line.rekening_name,
                                        'user_id': new_line.user_id,
                                        'bank_account': new_line.transfer_bank_account.id,
                                        # 'nominal': -new_line.nominal if new_line.kategori.name == 'PD' else new_line.nominal,
                                        'nominal': new_line.nominal * -1,
                                        'transfer_bank_account': new_line.bank_account.id,
                                        'transaction_id': new_line.transaction_id,
                                        'create_on': new_line.create_on,
                                    }
                                    self.env['bo.line'].create(bo_line_same_vals)

                    except IndexError:
                        pass

        if not self.uploadfile:
            raise UserError('Please upload excel file first.')
        
    def fnCreateBonusLineRec(self, record):
 
        kategori = str(record[5])
        kategoriid = self.env['kategori.bo'].search([('name', '=', kategori)], limit=1)
        if kategori:
            if not kategoriid:
                raise UserError(_("There is no kategori with name %s.") % kategori)
        else:
            kategoriid = False
        
        mistake = str(record[6])
        mistakeid = self.env['mistaketype.bo'].search([('name', '=', mistake)], limit=1)
        if mistake:
            if not mistakeid:
                raise UserError(_("There is no mistake with name %s.") % mistake)
        else:
            mistakeid = False

        bank_account = str(record[3])
        bank_account_id = self.env['res.partner.bank'].search([('acc_number', '=', bank_account)], limit=1)
        if bank_account:
            if not bank_account_id:
                raise UserError(_("There is no bank account with number %s.") % bank_account)
        else:
            bank_account_id = False

        
        
        
        line_ids = {
            'nominal': record[0],
            'rekening_name': record[1],
            'user_id': record[2],
            'transfer_bank_account': bank_account_id.id if bank_account_id else False,
            'description': record[4],
            'kategori': kategoriid.id if kategoriid else False,
            'mistaketype': mistakeid.id if mistakeid else False,
            'create_on': record[7],
        }
        return line_ids

# class backoffice_search_wizard(models.TransientModel):
#     _name = 'backoffice.search.wizard'
#     _description = 'Backoffice Search Wizard'