from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from collections import defaultdict
from datetime import timedelta


class bo_daily_reports(models.Model):
    _name = 'bo.daily.reports'
    _description = 'Daily Reports Schedule Every 12 AM'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    website = fields.Many2one('bo.website', string='Website', track_visibility='always')
    date = fields.Date(string='Date', required=True)
    shift = fields.Selection([('1', 'Pagi'), ('2', 'Malam')], string='Shift', track_visibility='always', store=True)
    bo_header_bank_account = fields.Many2one('res.partner.bank', string='Bank Account', track_visibility='always', store=True)
    active = fields.Boolean(default=True)
    created_by_name_staff_id = fields.Char(string='Created By Name Staff ID', track_visibility='always', store=True)
    created_by_name_staff_kh = fields.Char(string='Created By Name Staff KH', track_visibility='always', store=True)
    created_by_name_staff_ph = fields.Char(string='Created By Name Staff PH', track_visibility='always', store=True)
    selisih = fields.Char(string='Selisih', track_visibility='always', store=True)
    total_dp = fields.Float(string='Total DP', track_visibility='always', store=True)
    total_wd = fields.Float(string='Total WD', track_visibility='always', store=True)
    total_hutang_tampung = fields.Float(string='Total Hutang Tampung', track_visibility='always', store=True)
    total_qris_pending = fields.Float(string='Total QRIS Pending', track_visibility='always', store=True)
    total_qris_before = fields.Float(string='Total QRIS Before', track_visibility='always', store=True)


class ReportBackofficeDaily(models.AbstractModel):
    _name = 'report.backoffice.report_backoffice_report_daily'

    @api.model
    def _get_report_values(self, docids, data=None):
        bo_daily_reports = self.env['bo.daily.reports'].browse(docids)
        # bo_header = bo_daily_reports.bo_header
        # bo_line = self.env['bo.line'].search([('bo_id', '=', bo_header.id)])
        bo_bonusheader = self.env['bo.bonus.header'].search([('website', '=', bo_daily_reports.website.id), ('date', '=', bo_daily_reports.date), ('shift', '=', bo_daily_reports.shift)])
        bo_bonusline = self.env['bo.bonus.line'].search([('bo_bonusheader_id', '=', bo_bonusheader.id)])
        bo_header = self.env['bo.header'].search([('website', '=', bo_daily_reports.website.id), ('date', '=', bo_daily_reports.date), ('shift', '=', bo_daily_reports.shift), ('bank_account', '=', bo_daily_reports.bo_header_bank_account.id)])
        bo_line = self.env['bo.line'].search([('bo_id', 'in', bo_header.ids)])

        nominal_sum_by_type = defaultdict(float)
        for line in bo_bonusline:
            if line.bonustype.name:
                nominal_sum_by_type[line.bonustype.name] += line.nominal

        sub_type = sum(nominal_sum_by_type.values())

        nominal_sum_by_kategori_save = defaultdict(float)
        for line in bo_line:
            if line.kategori.name == 'SAVE':
                nominal_sum_by_kategori_save[line.transfer_bank_account.acc_number] += line.nominal

        sub_kategori_save = sum(nominal_sum_by_kategori_save.values())

        # # Get previous date
        # previous_date = bo_daily_reports.date - timedelta(days=1)
        # bo_line_pinj = self.env['bo.line'].search([('kategori.name', '=', 'PINJ'), ('bo_id.date', 'in', [previous_date, bo_daily_reports.date])])

        

        # nominal_sum_by_kategori_pinj = defaultdict(float)
        # for line in bo_line_pinj:
        #     nominal_sum_by_kategori_pinj[line.kategori.name] += line.nominal

        return {
            'doc_ids': docids,
            'doc_model': 'bo.daily.reports',
            'docs': bo_daily_reports,
            # 'bo_header': bo_header,
            # 'bo_line': bo_line,
            'bo_bonusheader': bo_bonusheader,
            'bo_bonusline': bo_bonusline,
            'nominal_sum_by_type': nominal_sum_by_type,
            'nominal_sum_by_kategori_save': nominal_sum_by_kategori_save,
            'sub_type': sub_type,
            'sub_kategori_save': sub_kategori_save,
            # 'nominal_sum_by_kategori_pinj': nominal_sum_by_kategori_pinj,
        }