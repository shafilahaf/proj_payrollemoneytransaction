from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import datetime
from lxml import etree
from collections import defaultdict

class bo_dashboard_report(models.Model):
    _name = 'bo.dashboard.report'
    _rec_name = 'name'

    name = fields.Char(string='Name', default='Dashboard Report')
    website = fields.Many2one('bo.website', string='Website')
    # date = fields.Date(string='Date')
    month = fields.Selection([
        ('01', 'Januari'),
        ('02', 'Februari'),
        ('03', 'Maret'),
        ('04', 'April'),
        ('05', 'Mei'),
        ('06', 'Juni'),
        ('07', 'Juli'),
        ('08', 'Agustus'),
        ('09', 'September'),
        ('10', 'Oktober'),
        ('11', 'November'),
        ('12', 'Desember'),
    ], string='Month')

    header_ids = fields.Many2many('bo.header', string='Headers', compute='_compute_header_ids')
    line_ids = fields.Many2many('bo.line', string='Lines', compute='_compute_line_ids')

    bonus_header_ids = fields.Many2many('bo.bonus.header', string='Bonus Header', compute='_compute_bonus_header_ids')
    bonus_line_ids = fields.Many2many('bo.bonus.line', string='Bonus Line', compute='_compute_bonus_line_ids')
    total_bonus = fields.Float(string='Total Bonus', store=True, compute='_compute_bonus') #sum of bonus_line_ids where bonustype kategori = 1
    total_rebate = fields.Float(string='Total Rebate', store=True, compuute='_compute_bonus') #sum of bonus_line_ids where bonustype kategori = 2

    total_deposit = fields.Float(string='Total Deposit', compute='_compute_totals')
    total_withdraw = fields.Float(string='Total Withdraw', compute='_compute_totals')
    total_admin_fee = fields.Float(string='Total Admin Fee', compute='_compute_totals')
    total_pulsa_fee = fields.Float(string='Total Pulsa Fee', compute='_compute_totals')
    total_pulsa_rate = fields.Float(string='Total Pulsa Rate', compute='_compute_totals')
    total_purchase_pulsa_credit = fields.Float(string='Total Purchase Pulsa Credit', compute='_compute_totals')
    total_saving = fields.Float(string='Total Saving', compute='_compute_totals')
    total_belom_lapor = fields.Float(string='Total Belum Lapor (BL)', compute='_compute_totals')
    total_salah_lapor = fields.Float(string='Total Salah Lapor', compute='_compute_totals')
    total_all_minus_nominal = fields.Float(string='Total All Minus Nominal', compute='_compute_totals')

    total_belom_transfer = fields.Float(string='Total Belom Transfer' , compute='_compute_totals') #mistaketype
    total_lp = fields.Float(string='Total LP' , compute='_compute_totals') #kategori
    total_pd = fields.Float(string='Total PD' , compute='_compute_totals') #kategori
    total_save = fields.Float(string='Total Save' , compute='_compute_totals') #kategori
    total_pinj = fields.Float(string='Total Pinjam' , compute='_compute_totals') #kategori

    # daily_summary = fields.Text(string='Daily Summary', compute='_compute_daily_summary')
    daily_summary = fields.Html(string='Daily Summary', compute='_compute_daily_summary')

    @api.model
    def _get_years(self):
        return [(str(num), str(num)) for num in range(2022, 2030)]

    year = fields.Selection(_get_years, string='Year', default='2023')

    @api.depends('website', 'month', 'year')
    def _compute_header_ids(self):
        for record in self:
            headers = self.env['bo.header'].search([
                ('website', '=', record.website.id),
                ('date', 'like', '{}-{}-%'.format(record.year, record.month))
            ])
            record.header_ids = headers

    @api.depends('header_ids')
    def _compute_line_ids(self):
        for record in self:
            lines = self.env['bo.line'].search([('bo_id', 'in', record.header_ids.ids)])
            record.line_ids = lines

    # Bonus
    @api.depends('website', 'month', 'year')
    def _compute_bonus_header_ids(self):
        for record in self:
            bonus_header = self.env['bo.bonus.header'].search([
                ('website', '=', record.website.id),
                ('date', 'like', '{}-{}-%'.format(record.year, record.month)),
            ])
            record.bonus_header_ids = bonus_header

    @api.depends('bonus_header_ids')
    def _compute_bonus_line_ids(self):
        for record in self:
            bonus_lines = self.env['bo.bonus.line'].search([('bo_bonusheader_id', 'in', record.bonus_header_ids.ids), ('bonustype.kategori', '=', '1')])
            record.bonus_line_ids = bonus_lines

    @api.depends('bonus_line_ids')
    def _compute_bonus(self):
        """
        Sum of bonus_line_ids where bonustype kategori = 1
        """
        for record in self:
            record.total_bonus = sum(record.bonus_line_ids.filtered(lambda line: line.bonustype.kategori == '1').mapped('nominal'))
            record.total_rebate = sum(record.bonus_line_ids.filtered(lambda line: line.bonustype.kategori == '2').mapped('nominal'))
            
    # Bonus

    @api.depends('line_ids')
    def _compute_totals(self):
        for record in self:
            record.total_deposit = sum([line.nominal for line in record.line_ids if line.kategori.name == 'DP'])
            record.total_withdraw = sum([line.nominal for line in record.line_ids if line.kategori.name == 'WD'])
            record.total_admin_fee = sum([line.nominal for line in record.line_ids if line.kategori.name == 'ADM'])
            record.total_pulsa_fee = sum([line.nominal for line in record.line_ids if line.kategori.name == 'UP'])
            record.total_pulsa_rate = sum([line.nominal for line in record.line_ids if line.kategori.name == 'RP'])
            record.total_purchase_pulsa_credit = sum([line.nominal for line in record.line_ids if line.kategori.name == 'PULSA'])
            record.total_saving = sum([line.nominal for line in record.line_ids if line.kategori.name == 'SAVE'])
            record.total_belom_lapor = sum([line.nominal for line in record.line_ids if line.mistaketype.name == 'BL'])
            record.total_salah_lapor = sum([line.nominal for line in record.line_ids if line.kategori.name == 'SALAH'])
            record.total_all_minus_nominal = sum([line.nominal for line in record.line_ids if line.nominal < 0 and line.kategori.name != 'ADM'])
            record.total_belom_transfer = sum([line.nominal for line in record.line_ids if line.mistaketype.name == 'BL'])
            record.total_lp = sum([line.nominal for line in record.line_ids if line.kategori.name == 'LP'])
            record.total_pd = sum([line.nominal for line in record.line_ids if line.kategori.name == 'PD'])
            record.total_save = sum([line.nominal for line in record.line_ids if line.kategori.name == 'SAVE'])
            record.total_pinj = sum([line.nominal for line in record.line_ids if line.kategori.name == 'PINJAM'])

    @api.depends('header_ids', 'line_ids', 'bonus_header_ids', 'bonus_line_ids')
    def _compute_daily_summary(self):
        for record in self:
            html_table = etree.Element('table')
            html_table.attrib['border'] = '2'  # Add border attribute

            # Create table header
            header_row = etree.SubElement(html_table, 'tr')
            header_row.extend(etree.Element('th') for _ in range(15))
            header_row[0].text = 'Date'
            header_row[1].text = 'DP'
            header_row[2].text = 'WD'
            header_row[3].text = 'ADM'
            header_row[4].text = 'UP'
            header_row[5].text = 'RP'
            header_row[6].text = 'PULSA'
            header_row[7].text = 'SAVE'
            header_row[8].text = 'BL'
            header_row[9].text = 'SALAH'
            # header_row[10].text = 'MINUS NOMINAL'
            header_row[10].text = 'BT'
            header_row[11].text = 'LP'
            header_row[12].text = 'PD'
            header_row[13].text = 'SAVE'
            header_row[14].text = 'PINJAM'
            # header_row[16].text = 'BONUS'
            # header_row[17].text = 'REBATE'

            for header_cell in header_row.iter('th'):
                header_cell.attrib['style'] = 'padding: 5px; text-align: center;'  # Adjust the padding value as desired

            totals_by_date = {}  # Dictionary to store totals for each date
            for header in record.header_ids:
                date = f"{header.date}"
                if date not in totals_by_date:
                    totals_by_date[date] = {
                        'deposits': 0.0,
                        'withdrawals': 0.0,
                        'admin_fee': 0.0,
                        'pulsa_fee': 0.0,
                        'pulsa_rate': 0.0,
                        'purchase_pulsa_credit': 0.0,
                        'saving': 0.0,
                        'belom_lapor': 0.0,
                        'salah_lapor': 0.0,
                        # 'all_minus_nominal': 0.0,
                        'belom_transfer': 0.0,
                        'lp': 0.0,
                        'pd': 0.0,
                        'save': 0.0,
                        'pinjam': 0.0,
                        # 'bonus': 0.0,
                        # 'rebate': 0.0,
                    }
                totals_by_date[date]['deposits'] += header.total_deposit
                totals_by_date[date]['withdrawals'] += header.total_withdraw
                totals_by_date[date]['admin_fee'] += header.total_admin_fee
                totals_by_date[date]['pulsa_fee'] += header.total_pulsa_fee
                totals_by_date[date]['pulsa_rate'] += header.total_pulsa_rate
                totals_by_date[date]['purchase_pulsa_credit'] += header.total_purchase_pulsa_credit
                totals_by_date[date]['saving'] += header.total_saving
                totals_by_date[date]['belom_lapor'] += header.total_belom_lapor
                totals_by_date[date]['salah_lapor'] += header.total_salah_lapor
                # totals_by_date[date]['all_minus_nominal'] += header.total_all_minus_nominal
                totals_by_date[date]['belom_transfer'] += header.total_belom_transfer
                totals_by_date[date]['lp'] += header.total_lp
                totals_by_date[date]['pd'] += header.total_pd
                totals_by_date[date]['save'] += header.total_save
                totals_by_date[date]['pinjam'] += header.total_pinj
                # totals_by_date[date]['bonus'] += header.total_bonus
                # totals_by_date[date]['rebate'] += header.total_rebate

            sorted_dates = sorted(totals_by_date.keys())
            for date in sorted_dates:
                totals = totals_by_date[date]
                row = etree.SubElement(html_table, 'tr')
                row.extend(etree.Element('td') for _ in range(15))
                row[0].text = date
                row[1].text = f"{totals['deposits']:,.2f}"
                row[2].text = f"{totals['withdrawals']:,.2f}"
                row[3].text = f"{totals['admin_fee']:,.2f}"
                row[4].text = f"{totals['pulsa_fee']:,.2f}"
                row[5].text = f"{totals['pulsa_rate']:,.2f}"
                row[6].text = f"{totals['purchase_pulsa_credit']:,.2f}"
                row[7].text = f"{totals['saving']:,.2f}"
                row[8].text = f"{totals['belom_lapor']:,.2f}"
                row[9].text = f"{totals['salah_lapor']:,.2f}"
                # row[10].text = f"{totals['all_minus_nominal']:,.2f}"
                row[10].text = f"{totals['belom_transfer']:,.2f}"
                row[11].text = f"{totals['lp']:,.2f}"
                row[12].text = f"{totals['pd']:,.2f}"
                row[13].text = f"{totals['save']:,.2f}"
                row[14].text = f"{totals['pinjam']:,.2f}"
                # row[16].text = f"{totals['bonus']:,.2f}"
                # row[17].text = f"{totals['rebate']:,.2f}"
            
            # Original    
            # for date, totals in totals_by_date.items():
            #     row = etree.SubElement(html_table, 'tr')
            #     row.extend(etree.Element('td') for _ in range(16))
            #     row[0].text = date
            #     row[1].text = f"{totals['deposits']:,.2f}"
            #     row[2].text = f"{totals['withdrawals']:,.2f}"
            #     row[3].text = f"{totals['admin_fee']:,.2f}"
            #     row[4].text = f"{totals['pulsa_fee']:,.2f}"
            #     row[5].text = f"{totals['pulsa_rate']:,.2f}"
            #     row[6].text = f"{totals['purchase_pulsa_credit']:,.2f}"
            #     row[7].text = f"{totals['saving']:,.2f}"
            #     row[8].text = f"{totals['belom_lapor']:,.2f}"
            #     row[9].text = f"{totals['salah_lapor']:,.2f}"
            #     row[10].text = f"{totals['all_minus_nominal']:,.2f}"
            #     row[11].text = f"{totals['belom_transfer']:,.2f}"
            #     row[12].text = f"{totals['lp']:,.2f}"
            #     row[13].text = f"{totals['pd']:,.2f}"
            #     row[14].text = f"{totals['save']:,.2f}"
            #     row[15].text = f"{totals['pinj']:,.2f}"
                # row[16].text = f"{totals['bonus']:,.2f}"
                # row[17].text = f"{totals['rebate']:,.2f}"
            # Original  
            # Apply padding to table cells
            for row in html_table.iter('tr'):
                for cell in row.iter('td'):
                    cell.attrib['style'] = 'padding: 10px; text-align: right'  # Adjust the padding value as desired

            # Convert the HTML table to a string
            record.daily_summary = etree.tostring(html_table, pretty_print=True, encoding='unicode')


class vivi_dashboard_report(models.Model):
    _name = 'bo.vivi.dashboard.report'

    month = fields.Selection([
        ('01', 'Januari'),
        ('02', 'Februari'),
        ('03', 'Maret'),
        ('04', 'April'),
        ('05', 'Mei'),
        ('06', 'Juni'),
        ('07', 'Juli'),
        ('08', 'Agustus'),
        ('09', 'September'),
        ('10', 'Oktober'),
        ('11', 'November'),
        ('12', 'Desember'),
    ], string='Month')

    @api.model
    def _get_years(self):
        return [(str(num), str(num)) for num in range(2022, 2030)]

    year = fields.Selection(_get_years, string='Year', default='2023')

    header_ids = fields.Many2many('bo.header', string='Headers', compute='_compute_vivi_header_ids')
    line_ids = fields.Many2many('bo.line', string='Lines', compute='_compute_vivi_line_ids')
    bank_header_ids = fields.Many2many('res.bank', string='Bank Headers', compute='_compute_vivi_bank_header_ids')
    daily_summary = fields.Html(string='Daily Summary DP', compute='_compute_daily_summary')
    daily_summary_wd = fields.Html(string='Daily Summary WD', compute='_compute_daily_wd_summary')
    website = fields.Many2one('bo.website', string='Website', track_visibility='always', required=True)
    bank = fields.Many2one('res.bank', string='Bank', track_visibility='always', required=True, domain="[('websites', '=', website)]") 

    @api.depends('month', 'year')
    def _compute_vivi_header_ids(self):
        for record in self:
            # headers = self.env['bo.header'].search([
            #     ('date', 'like', '{}-{}-%'.format(record.year, record.month))
            # ], order='date')
            # record.header_ids = headers
            headers = self.env['bo.header'].search([
                ('date', 'like', '{}-{}-%'.format(record.year, record.month)),
                ('bank', '=', record.bank.id)
            ], order='date')
            record.header_ids = headers

    @api.depends('header_ids')
    def _compute_vivi_line_ids(self):
        for record in self:
            lines = self.env['bo.line'].search([
                ('bo_id', 'in', record.header_ids.ids)
            ])
            record.line_ids = lines

            banks = self.env['res.bank'].search([
                ('id', 'in', record.header_ids.mapped('bank').ids)
            ])
            record.bank_header_ids = banks

    # DP
    # Original
    # @api.depends('header_ids')
    # def _compute_daily_summary(self):
    #     for record in self:
    #         summary = defaultdict(dict)
    #         banks = set()  # Collect unique bank names

    #         for header in record.header_ids:
    #             date_str = header.date.strftime('%d %B %Y')
    #             bank_name = header.bank.name
    #             banks.add(bank_name)  # Add bank name to the set

    #             if bank_name in summary[date_str]:
    #                 summary[date_str][bank_name] += header.total_deposit
    #             else:
    #                 summary[date_str][bank_name] = header.total_deposit

    #         # Create the HTML table
    #         html_table = etree.Element('table')
    #         html_table.attrib['border'] = '2'  # Add border attribute
    #         header_row = etree.SubElement(html_table, 'tr')
    #         header_row.extend(etree.Element('th') for _ in range(len(banks) + 1))
    #         header_row[0].text = 'Date'
    #         header_row[0].attrib['style'] = 'text-align: center;padding: 15px;'

    #         for i, bank_name in enumerate(sorted(banks)):
    #             header_row[i + 1].text = bank_name
    #             header_row[i + 1].attrib['style'] = 'text-align: center;padding: 15px;'

    #         for date, bank_totals in summary.items():
    #             row = etree.SubElement(html_table, 'tr')
    #             row.extend(etree.Element('td') for _ in range(len(banks) + 1))
    #             row[0].text = date
    #             row[0].attrib['style'] = 'text-align: center;padding: 15px;'
    #             for i, bank_name in enumerate(sorted(banks)):
    #                 # row[i + 1].text = f"{bank_totals.get(bank_name, 0):,.2f}"
    #                 row[i + 1].text = f"{bank_totals.get(bank_name, 0):,.2f}"
    #                 row[i + 1].attrib['style'] = 'text-align: right;padding: 15px;'

    #         # Convert the HTML table to a string
    #         record.daily_summary = etree.tostring(html_table, pretty_print=True, encoding='unicode')
    # Original

    # DP
    @api.depends('header_ids')
    def _compute_daily_summary(self):
        for record in self:
            summary = defaultdict(dict)
            banks = set()  # Collect unique bank names

            for header in record.header_ids:
                date_str = header.date.strftime('%d %B %Y')
                # bank_name = header.bank_account.acc_number + ' - ' + header.bank_account.acc_holder_name
                acc_number_str = str(header.bank_account.acc_number) if header.bank_account.acc_number else ""
                holder_name_str = str(header.bank_account.acc_holder_name) if header.bank_account.acc_holder_name else ""
                bank_name = acc_number_str + ' - ' + holder_name_str
                banks.add(bank_name)  # Add bank name to the set

                if bank_name in summary[date_str]:
                    summary[date_str][bank_name] += header.total_deposit
                else:
                    summary[date_str][bank_name] = header.total_deposit

            # Create the HTML table
            html_table = etree.Element('table')
            html_table.attrib['border'] = '2'  # Add border attribute
            header_row = etree.SubElement(html_table, 'tr')
            header_row.extend(etree.Element('th') for _ in range(len(banks) + 1))
            header_row[0].text = 'Date'
            header_row[0].attrib['style'] = 'text-align: center;padding: 15px;'

            for i, bank_name in enumerate(sorted(banks)):
                header_row[i + 1].text = bank_name
                header_row[i + 1].attrib['style'] = 'text-align: center;padding: 15px;'

            for date, bank_totals in summary.items():
                row = etree.SubElement(html_table, 'tr')
                row.extend(etree.Element('td') for _ in range(len(banks) + 1))
                row[0].text = date
                row[0].attrib['style'] = 'text-align: center;padding: 15px;'
                for i, bank_name in enumerate(sorted(banks)):
                    # row[i + 1].text = f"{bank_totals.get(bank_name, 0):,.2f}"
                    row[i + 1].text = f"{bank_totals.get(bank_name, 0):,.2f}"
                    row[i + 1].attrib['style'] = 'text-align: right;padding: 15px;'

            # Convert the HTML table to a string
            record.daily_summary = etree.tostring(html_table, pretty_print=True, encoding='unicode')

    # WD
    # Original
    # @api.depends('header_ids')
    # def _compute_daily_wd_summary(self):
    #     for record in self:
    #         summary = defaultdict(dict)
    #         banks = set()

    #         for header in record.header_ids:
    #             date_str = header.date.strftime('%d %B %Y')
    #             bank_name = header.bank.name
    #             banks.add(bank_name)

    #             if bank_name in summary[date_str]:
    #                 summary[date_str][bank_name] += header.total_withdraw
    #             else:
    #                 summary[date_str][bank_name] = header.total_withdraw

    #         # Create the HTML table
    #         html_table = etree.Element('table')
    #         html_table.attrib['border'] = '2'  # Add border attribute
    #         header_row = etree.SubElement(html_table, 'tr')
    #         header_row.extend(etree.Element('th') for _ in range(len(banks) + 1))
    #         header_row[0].text = 'Date'
    #         header_row[0].attrib['style'] = 'text-align: center;padding: 15px;'
    #         for i, bank_name in enumerate(sorted(banks)):
    #             header_row[i + 1].text = bank_name
    #             header_row[i + 1].attrib['style'] = 'text-align: center;padding: 15px;'

    #         for date, bank_totals in summary.items():
    #             row = etree.SubElement(html_table, 'tr')
    #             row.extend(etree.Element('td') for _ in range(len(banks) + 1))
    #             row[0].text = date
    #             row[0].attrib['style'] = 'text-align: center;padding: 15px;'
    #             for i, bank_name in enumerate(sorted(banks)):
    #                 row[i + 1].text = f"{bank_totals.get(bank_name, 0):,.2f}"
    #                 row[i + 1].attrib['style'] = 'text-align: right;padding: 15px;'

    #         # Convert the HTML table to a string
    #         record.daily_summary_wd = etree.tostring(html_table, pretty_print=True, encoding='unicode')
    # Original

    # WD
    @api.depends('header_ids')
    def _compute_daily_wd_summary(self):
        for record in self:
            summary = defaultdict(dict)
            banks = set()

            for header in record.header_ids:
                date_str = header.date.strftime('%d %B %Y')
                # bank_name = header.bank_account.acc_number + ' - ' + header.bank_account.acc_holder_name
                acc_number_str = str(header.bank_account.acc_number) if header.bank_account.acc_number else ""
                holder_name_str = str(header.bank_account.acc_holder_name) if header.bank_account.acc_holder_name else ""
                bank_name = acc_number_str + ' - ' + holder_name_str
                banks.add(bank_name)

                if bank_name in summary[date_str]:
                    summary[date_str][bank_name] += header.total_withdraw
                else:
                    summary[date_str][bank_name] = header.total_withdraw

            # Create the HTML table
            html_table = etree.Element('table')
            html_table.attrib['border'] = '2'  # Add border attribute
            header_row = etree.SubElement(html_table, 'tr')
            header_row.extend(etree.Element('th') for _ in range(len(banks) + 1))
            header_row[0].text = 'Date'
            header_row[0].attrib['style'] = 'text-align: center;padding: 15px;'
            for i, bank_name in enumerate(sorted(banks)):
                header_row[i + 1].text = bank_name
                header_row[i + 1].attrib['style'] = 'text-align: center;padding: 15px;'

            for date, bank_totals in summary.items():
                row = etree.SubElement(html_table, 'tr')
                row.extend(etree.Element('td') for _ in range(len(banks) + 1))
                row[0].text = date
                row[0].attrib['style'] = 'text-align: center;padding: 15px;'
                for i, bank_name in enumerate(sorted(banks)):
                    row[i + 1].text = f"{bank_totals.get(bank_name, 0):,.2f}"
                    row[i + 1].attrib['style'] = 'text-align: right;padding: 15px;'

            # Convert the HTML table to a string
            record.daily_summary_wd = etree.tostring(html_table, pretty_print=True, encoding='unicode')



