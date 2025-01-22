from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

# Variabel Set Selections Fields --START
setSelectionType = [("1", "LH"), ("2", "SH")]
# Variabel Set Selections Fields --END


class PayrollHoliday(models.Model):
    _name = "payroll.holiday"
    _description = "Payroll Holiday"
    _rec_name = 'event'

    event = fields.Char(string="Event", required=True)
    type = fields.Selection(setSelectionType, string="Type", required=True)
    day = fields.Integer(string="Day")
    month = fields.Selection([
        ("1", "January"), ("2", "February"), ("3", "March"), ("4", "April"),
        ("5", "May"), ("6", "June"), ("7", "July"), ("8", "August"),
        ("9", "September"), ("10", "October"), ("11", "November"), ("12", "December")], string="Month")
    year = fields.Char(string="Year")
    date = fields.Date(string="Date", compute='_compute_date', store=True)
    
    @api.depends('day', 'month', 'year')
    def _compute_date(self):
        for record in self:
            if record.day and record.month and record.year:
                try:
                    # Create a datetime object and convert it to a date
                    date_str = f"{record.year}-{record.month.zfill(2)}-{record.day:02d}"
                    record.date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    record.date = False
            else:
                record.date = False
