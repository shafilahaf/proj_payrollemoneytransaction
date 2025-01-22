from odoo import http
from odoo.http import request
from odoo.exceptions import UserError, AccessDenied
from odoo import _
class ResUsersPasswordController(http.Controller):
    @http.route('/my/security', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def security(self, **post):
        values = self._prepare_portal_layout_values()  # Prepares layout for the portal (UI elements)
        values['get_error'] = None
        if request.httprequest.method == 'POST':
            values.update(self._update_password(
                post.get('old', '').strip(),
                post.get('new1', '').strip(),
                post.get('new2', '').strip()
            ))
        return request.render('portal.portal_my_security', values, headers={
            'X-Frame-Options': 'DENY'  # Security header to prevent embedding in iframe
        })
    def _update_password(self, old, new1, new2):
        # Ensure no password fields are empty
        for k, v in [('old', old), ('new1', new1), ('new2', new2)]:
            if not v:
                return {'errors': {'password': {k: _("You cannot leave any password empty.")}}}
        # Ensure the new passwords match
        if new1 != new2:
            return {'errors': {'password': {'new2': _("The new password and its confirmation must be identical.")}}}
        # Try changing the password
        try:
            request.env['res.users'].change_password(old, new1)
        except UserError as e:
            return {'errors': {'password': e.name}}  # Handle password change error
        except AccessDenied as e:
            msg = e.args[0]
            if msg == AccessDenied().args[0]:
                msg = _('The old password you provided is incorrect, your password was not changed.')
            return {'errors': {'password': {'old': msg}}}  # Handle incorrect old password
        # Update session token to avoid logout after password change
        new_token = request.env.user._compute_session_token(request.session.sid)
        request.session.session_token = new_token
        return {'success': {'password': True}}  # Password successfully changed