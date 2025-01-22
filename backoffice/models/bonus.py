from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import xlrd
import base64

class bo_bonusHeader(models.Model):
    _name = 'bo.bonus.header'
    _description = 'Bonus Header Backoffice'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Bonus Name', readonly=True, track_visibility='always')
    date = fields.Date(string='Date', default=fields.Date.today, required=True, track_visibility='always')
    total_deposit = fields.Float(string='Total Depo', store=True, compute='_compute_totals')
    total_wd = fields.Float(string='Total WD', store=True, compute='_compute_totals')
    website = fields.Many2one('bo.website', string='Website', required=True, track_visibility='always')
    bonustype_display = fields.Text(compute='_compute_bonustype_display', string="Bonus", store=True)
    shift = fields.Selection([('1', 'Pagi'), ('2', 'Malam')], string='Shift', track_visibility='always', required=True, store=True)
    uploadfile = fields.Binary(string='Upload File' )
    bo_bonusLine = fields.One2many('bo.bonus.line', 'bo_bonusheader_id', string='Bonus Line')
    active = fields.Boolean(default=True)

    # Open the wizard
    def fnOpenWizard(self):
        return {
            'name': _('Bonus Wizard'),
            'type': 'ir.actions.act_window',
            'res_model': 'bo.bonus.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_bo_bonusheader_id': self.id}
        }
    

    # Get nominal deposit and wd
    # @api.onchange('bo_bonusLine')
    # def _onchange_bo_bonusLine(self):
    #     for rec in self:
    #         rec.total_deposit = sum(rec.bo_bonusLine.filtered(lambda x: x.kat == 'DP').mapped('nominal'))
    #         rec.total_wd = sum(rec.bo_bonusLine.filtered(lambda x: x.kat == 'WD').mapped('nominal'))

    @api.depends('bo_bonusLine')
    def _compute_totals(self):
        for rec in self:
            rec.total_deposit = sum(rec.bo_bonusLine.filtered(lambda x: x.kat == 'DP').mapped('nominal'))
            rec.total_wd = sum(rec.bo_bonusLine.filtered(lambda x: x.kat == 'WD').mapped('nominal'))

    # Rename by date and website
    @api.onchange('website')
    def _onchange_website_bank(self):
        if self.website:
            self.name = self.date.strftime('%m%d%Y') + '/' + self.website.name

    # Check date and website
    @api.constrains('date', 'website')
    def _check_date_website(self):
        for rec in self:
            if rec.search_count([('date', '=', rec.date), ('website', '=', rec.website.id)]) > 1:
                raise ValidationError(_('Website only can be used for 1 date only!'))

    # Get total bonus type display
    @api.depends('bo_bonusLine.bonustype', 'bo_bonusLine.nominal')
    def _compute_bonustype_display(self):
        for header in self:
            bonustype_totals = {}
            for line in header.bo_bonusLine:
                if line.bonustype:
                    if line.bonustype.name not in bonustype_totals:
                        bonustype_totals[line.bonustype.name] = (line.nominal)
                    else:
                        bonustype_totals[line.bonustype.name] += (line.nominal)
            bonustype_display = []
            for bonustype_name, total in bonustype_totals.items():
                format_total = "{:,.2f}".format(total)
                bonustype_display.append(f"Total {bonustype_name} = {format_total} \r\n")
            header.bonustype_display = ''.join(bonustype_display)

    # 23/06/2023 - take out temporary
    # @api.model
    # def create(self, vals):
    #     res = super(bo_bonusHeader, self).create(vals)
    #     if res:
    #         bo_header = self.env['bo.header'].search([('date', '=', res.date), ('website', '=', res.website.id), ('shift', '=', res.shift)])
    #         if bo_header:
    #             bo_header.bonus_header = res.id
    #     return res
    

    def fnimportBonusLines(self):
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

                            self.env['bo.bonus.line'].create({
                                'bo_bonusheader_id': self.id,
                                'date': vals['date'],
                                'kat': vals['kat'],
                                'keterangan': vals['keterangan'],
                                'nama_rekening': vals['nama_rekening'],
                                'member_id': vals['member_id'],
                                'bonustype': vals['bonustype'],
                                'nominal': vals['nominal']
                            })
                    except IndexError:
                        pass

    def fnCreateBonusLineRec(self, record):
        bonustypename = str(record[5])
        bonustypeid = self.env['bo.bonus.type'].search([('name', '=', bonustypename)], limit=1)
        if not bonustypeid:
            raise UserError(_("There is no bonus with name %s.") % bonustypename)
        
        line_ids = {    
            'date': record[0],
            'kat' : record[1],
            'keterangan': record[2],      
            'nama_rekening': record[3],
            'member_id': record[4],
            'bonustype' : bonustypeid.id,
            'nominal': record[6]
        }
        return line_ids

   
class bo_bonusLine(models.Model):
    _name = 'bo.bonus.line'
    _description = 'Bonus Line Backoffice'

    bo_bonusheader_id = fields.Many2one('bo.bonus.header', string='Bonus Header', ondelete='cascade', readonly=True)
    # date = fields.Date(string='Date', related='bo_bonusheader_id.date', store=True, readonly=True)
    date = fields.Date(string='Date', store=True, readonly=True)
    pic = fields.Many2one('res.users', string='PIC', default=lambda self: self.env.user, readonly=True)
    keterangan = fields.Char(string='Keterangan')
    nama_rekening = fields.Char(string='Nama Rekening')
    member_id = fields.Char(string='Member ID')
    bonustype = fields.Many2one('bo.bonus.type', string='Bonus Type')
    nominal = fields.Float(string='Nominal')
    kat = fields.Selection([('DP', 'DP'), ('WD', 'WD')], string='Kategori')
    
    @api.onchange('pic')
    def _onchange_pic(self):
        if self.pic:
            self.date = fields.Date.today()


class bo_bonus_wizard(models.TransientModel):
    _name = 'bo.bonus.wizard'
    _description = 'Bonus Wizard Backoffice'

    uploadfile = fields.Binary(string='Upload Excel File')
    bo_bonusheader_id = fields.Many2one('bo.bonus.header', string='Bonus Header', ondelete='cascade', readonly=True)

    def fnimportBonusLines(self):
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

                            self.env['bo.bonus.line'].create({
                                'bo_bonusheader_id': self.bo_bonusheader_id.id,
                                'date': vals['date'],
                                'kat': vals['kat'],
                                'keterangan': vals['keterangan'],
                                'nama_rekening': vals['nama_rekening'],
                                'member_id': vals['member_id'],
                                'bonustype': vals['bonustype'],
                                'nominal': vals['nominal']
                            })
                    except IndexError:
                        pass

    def fnCreateBonusLineRec(self, record):
        bonustypename = str(record[5])
        bonustypeid = self.env['bo.bonus.type'].search([('name', '=', bonustypename)], limit=1)
        if not bonustypeid:
            raise UserError(_("There is no bonus with name %s.") % bonustypename)
        
        line_ids = {
            'date': record[0],
            'kat' : record[1],
            'keterangan': record[2],      
            'nama_rekening': record[3],
            'member_id': record[4],
            'bonustype' : bonustypeid.id,
            'nominal': record[6]
        }
        return line_ids