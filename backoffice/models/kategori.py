from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

class kategori_bo(models.Model):
    _name = 'kategori.bo'
    _description = 'Kategori Backoffice'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Kategori', required=True, track_visibility='always')

    def _creation_message(self):
        """
        Return the message to notify at the creation of a record"""
        return _('The %s created') % self.name

    def _write_message(self, vals):
        """
        Return the message to notify at the update of a record"""
        return _('The %s updated') % self.name