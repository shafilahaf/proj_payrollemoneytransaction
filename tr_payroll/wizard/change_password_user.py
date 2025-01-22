from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class ResUsersPasswordWizard(models.TransientModel):
    _name = "res.users.password.wizard"
    _description = "Wizard for Changing Password"

    new_password = fields.Char(string="New Password", required=True, password=True)
    confirm_password = fields.Char(string="Confirm Password", required=True, password=True)

    def action_change_password(self):
        _logger.debug("Action Change Password triggered.")
        self.ensure_one()
        user = self.env.user  # Current logged-in user  

        # Log input values for debugging
        _logger.debug("Attempting to change password for user %s", user.login)
        _logger.debug("New Password: %s", self.new_password)
        _logger.debug("Confirm Password: %s", self.confirm_password)

        # Check if new password and confirmation match
        if self.new_password != self.confirm_password:
            _logger.error("New password and confirmation do not match.")
            raise ValidationError("The new password and confirmation do not match.")
        
        try:
            _logger.debug("Attempting to update password for user %s", user.login)
            user.write({'password': self.new_password})  # Attempt to change the password
        except UserError as e:
            _logger.error("Error changing password: %s", e.name)
            raise ValidationError(e.name)
        except AccessDenied as e:
            _logger.error("Access denied error: %s", e.args[0])
            raise ValidationError(e.args[0])
        
        _logger.debug("Password updated successfully for user %s", user.login)
        return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': 'Success',
            'message': 'Password updated successfully for user %s.' % user.name,
            'sticky': False,
            'type': 'success',
        },
        'next': {
            'type': 'ir.actions.act_window_close',
        },
        }