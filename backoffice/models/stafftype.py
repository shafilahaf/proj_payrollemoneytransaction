from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

class StaffType(models.Model):
    _name = 'bo.staff.type'
    _description = 'TR Staff Type'

    name = fields.Char(string='Name', required=True)
    # website = fields.Many2many('bo.website', string='Website')