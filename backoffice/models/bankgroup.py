from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

class bankgroup_bo(models.Model):
    _name = 'bankgroup.bo'
    _description = 'Bank Group Backoffice'
    _rec_name = 'bankgroup'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    bankgroup = fields.Char(string='Bank Group', required=True)

    def _creation_message(self):
        """Return the default creation message for this model.
        """
        return _('The %s created') % self.bankgroup

    def _write_message(self, vals):
        """Return the default write message for this model.
        """
        return _('The %s updated') % self.bankgroup