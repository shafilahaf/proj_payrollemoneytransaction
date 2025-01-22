from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

class tampung_header(models.Model):
    _name = 'tampung.header'
    _description = 'Tampung Header'

    name = fields.Char(string='Name',readonly=True, default=lambda self: _('New'))
    tanggal = fields.Date(string='Tanggal', required=True, default=fields.Date.today())
    bank_tampung = fields.Many2one('res.bank', string='Bank Tampung', required=True)
    line_ids = fields.One2many('tampung.line', 'header_id', string='Tampung Line')
    
    total_nominal_bank_tampung_line_per_website = fields.Html(string='Total Nominal', compute='_compute_total_nominal_bank_tampung_line_per_website')

    @api.depends('line_ids')
    def _compute_total_nominal_bank_tampung_line_per_website(self):
        for header in self:
            if header.line_ids:
                table_html = '<table style="border-collapse: collapse;">'
                table_html += '<tr><th style="border: 1px solid black; padding: 5px; text-align: center;">Website</th><th style="border: 1px solid black; padding: 5px; text-align: center;">Total Nominal</th></tr>'
                
                website_totals = {}  # Dictionary to store totals per website
                
                for line in header.line_ids:
                    website = line.website.name
                    nominal = line.nominal
                    
                    # Update the total for the website
                    if website in website_totals:
                        website_totals[website] += nominal
                    else:
                        website_totals[website] = nominal
                
                # Add rows for each website and its total
                for website, total in website_totals.items():
                    # Format nominal without decimal places and add thousands separator
                    formatted_total = '{:,.0f}'.format(total)
                    
                    table_html += f'<tr><td style="border: 1px solid black; padding: 5px; text-align: left;">TOTAL HUTANG {website}</td><td style="border: 1px solid black; padding: 5px; text-align: right;">{formatted_total}</td></tr>'
                
                table_html += '</table>'
                header.total_nominal_bank_tampung_line_per_website = table_html
            else:
                header.total_nominal_bank_tampung_line_per_website = False

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = 'Tampung/' + str(fields.Date.today().month) + '/' + str(fields.Date.today().year)
            vals['bank_tampung'] = self.env['res.bank'].search([('name','=','TAMPUNG')]).id
        return super(tampung_header, self).create(vals)

    @api.constrains('tanggal')
    def _check_tanggal(self):
        month = self.tanggal.month
        year = self.tanggal.year
        tampung = self.env['tampung.header'].search([('tanggal','>=',str(year)+'-'+str(month)+'-01'),('tanggal','<=',str(year)+'-'+str(month)+'-31')])
        if len(tampung) > 1:
            raise ValidationError(_('Tampung already exist in this month'))
        
class tampung_line(models.Model):
    _name = 'tampung.line'
    _description = 'Tampung Line'

    header_id = fields.Many2one('tampung.header', string='Header ID')
    bank_tampung_header = fields.Many2one('res.bank', string='Bank Tampung', related='header_id.bank_tampung')
    tanggal = fields.Date(string='Tanggal', required=True, default=fields.Date.today())
    kategori = fields.Selection([('1','IN'),('2','OUT')], string='Kategori', required=True)
    website = fields.Many2one('bo.website', string='Website', required=True)
    nama_bank = fields.Char(string='Nama Bank')
    keterangan = fields.Char(string='Keterangan')
    bank_tampung = fields.Many2one('res.partner.bank', string='Bank Tampung', required=True, domain="[('bank_id','=',bank_tampung_header)]")
    nominal = fields.Float(string='Nominal', required=True)

    @api.model
    def create_tampung_line_log(self, header_id, tanggal, kategori, website, nama_bank, keterangan, bank_tampung, nominal):
        log = self.create({
            'header_id': header_id,
            'tanggal': tanggal,
            'kategori': kategori,
            'website': website,
            'nama_bank': nama_bank,
            'keterangan': keterangan,
            'bank_tampung': bank_tampung,
            'nominal': nominal,
        })

        return log