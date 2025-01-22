from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

class bo_bonusType(models.Model):
    _name = 'bo.bonus.type'
    _description = 'Bonus Type Backoffice'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Bonus Type', required=True, track_visibility='always')
    kategori = fields.Selection([('1', 'Bonus'), ('2', 'Rebate'), ('3', 'Cashback')], string='Kategori', required=True, track_visibility='always')