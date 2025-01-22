from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

class bo_website(models.Model):
    _name = 'bo.website'
    _description = 'Website Backoffice'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Website Name', required=True)
    bank_tampung = fields.Many2one('res.partner.bank', string='Bank Tampung') # Bank Tampung (pending dulu)
    bank_wd = fields.Many2one('res.partner.bank', string='Bank WD') # Bank WD
    bank_save = fields.Many2one('res.partner.bank', string='Bank SAVE') # Bank SAVE
    
    is_automatic_transactionid = fields.Boolean(string='Automatic Transaction ID', track_visibility='always', default=False)
    initial_website = fields.Char(string='Initial Website', track_visibility='always')

    def _creation_message(self):
        """
        Return the message to notify at the creation of a record"""
        return _('The %s created') % self.name

    def _write_message(self, vals):
        """
        Return the message to notify at the update of a record"""
        return _('The %s updated') % self.name