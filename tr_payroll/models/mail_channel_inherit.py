from odoo import api, fields, models
from odoo.exceptions import ValidationError

class MailChannelInherit(models.Model):
    _inherit = 'mail.channel'

    prevent_edit_delete_message = fields.Boolean(string="Prevent Editing and Deleting Chat")

class MailMessageInherit(models.Model):
    _inherit = 'mail.message'

    @api.model
    def _check_channel_prevent_edit_delete(self, message, vals):
        """Check if the channel prevents editing or deleting messages."""
        if message.model == 'mail.channel' and message.res_id:
            channel = self.env['mail.channel'].browse(message.res_id)
            if channel.prevent_edit_delete_message:
                if 'body' in vals and message.body != vals['body']:
                    if '@' in vals['body'] and len(vals['body']) > len(message.body):
                        return  # Skip validation for mention updates.
                    raise ValidationError("Editing or deleting messages is not allowed in this channel.")

    def write(self, vals):
        """Override to prevent editing messages in channels with restrictions."""
        for record in self:
            record._check_channel_prevent_edit_delete(record, vals)
        return super(MailMessageInherit, self).write(vals)

    def unlink(self):
        """Override to prevent deleting messages in channels with restrictions."""
        for record in self:
            record._check_channel_prevent_edit_delete(record, {})
        return super(MailMessageInherit, self).unlink()
