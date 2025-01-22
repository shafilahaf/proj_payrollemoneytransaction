from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PayrollApprovalEntries(models.Model):
    _name = 'payroll.approval.entries'
    _description = 'Approval Entries'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, default='New', readonly=True)
    document_type = fields.Selection([
        ('1', 'Timeoff Request'),
        ('99', 'Others')
    ], string='Document Type')
    request_type = fields.Selection([
        ('1', 'Leave'),
        ('2', 'Sick'),
        ('3', 'Permission'),
        ('4', 'Day Off'),
        ('5', 'Device Error'),
        ('6', 'Not Taken Leave'),
        ('7', 'Medical Reimburment W/O Off'),
        ('99', 'Absence'),
    ], string='Request Type', related='document_id.request_type', store=True)
    document_id = fields.Many2one('payroll.time.off.request', string='Document')
    request_date = fields.Date(string='Request Date')
    request_by = fields.Many2one('res.users', string='Request By')
    request_by_employee = fields.Many2one('payroll.employees', string='Request By Employee')
    approver = fields.Many2one('payroll.employees', string='Approver')
    approved_date = fields.Date(string='Approved Date')
    approved_by = fields.Many2one('res.users', string='Approved By')
    status = fields.Selection([
        ('1', 'Open'),
        ('2', 'Pending Approval'),
        ('3', 'Rejected'),
        ('5', 'Approved')
    ], string='Status', readonly=True)
    reason = fields.Text(string='Reason')
    sequence = fields.Integer(string='Sequence')
    approval_id = fields.Many2one('payroll.time.off.request.approval', string='Approval')
    file = fields.Binary(string='File', related='document_id.file', store=True)
    internal_note = fields.Char(string="Note", readonly=True)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        user_groups = user.groups_id

        allowed_departments = []
        allowed_categories = []

        for group in user_groups:
            if group.is_active:
                allowed_departments += group.department_ids.ids
                allowed_categories += group.categories_ids.ids

        domain = []

        # Department and Category filter (existing logic)
        # if allowed_departments and allowed_categories:
        #     for dept in allowed_departments:
        #         for cat in allowed_categories:
        #             domain += ['|', ('request_by_employee.department_id', '=', dept), ('request_by_employee.category_id', '=', cat)]
        # elif allowed_departments:
        #     for dept in allowed_departments:
        #         domain += [('request_by_employee.department_id', '=', dept)]
        # elif allowed_categories:
        #     for cat in allowed_categories:
        #         domain += [('request_by_employee.category_id', '=', cat)]

        domain = []
        if allowed_departments and allowed_categories:
            domain = ['|', ('request_by_employee.department_id', 'in', allowed_departments), ('request_by_employee.category_id', 'in', allowed_categories)]
        elif allowed_departments:
            domain = [('request_by_employee.department_id', 'in', allowed_departments)]
        elif allowed_categories:
            domain = [('request_by_employee.category_id', 'in', allowed_categories)]

        if domain:
            args += domain

        # Position and Approver filter (from XML rule)
        domain += ['|', 
                ('approver.current_position.level', '>', user.payroll_positions_level),
                ('approver', '=', user.payroll_employee_id.id)]

        # Combine existing domain with the user-specific visibility logic
        if domain:
            args += domain

        return super(PayrollApprovalEntries, self).search(args, offset, limit, order, count)


    @api.model
    def create(self, vals):
        """
        This method is called when creating a new record."""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('payroll.approval.entries') or 'New'
        return super(PayrollApprovalEntries, self).create(vals)

    def _reject_all_entries(self, entries, reason=None):
        """
        This method will reject all entries in the given entries list."""
        for entry in entries:
            entry.approval_id.action_reject(reason)
            entry.write({
                'status': '3',
                'approved_by': self.env.user.id,
                'approved_date': fields.Date.today(),
                'reason': reason or entry.reason
            })

    def action_approve_entry(self):
        """
        This method will approve the entry. If the entry is the first entry in the sequence, it will approve all entries"""
        self.ensure_one()
        if self.status != '2':
            raise UserError(_('Only pending approval entries can be approved.'))

        self.env.cr.execute("""
            SELECT id 
            FROM payroll_approval_entries 
            WHERE document_id = %s
        """, (self.document_id.id,))

        # Extract IDs from the result
        record_ids = [row[0] for row in self.env.cr.fetchall()]

        # Retrieve records using those IDs
        similar_entries = self.env['payroll.approval.entries'].sudo().browse(record_ids)
        min_sequence = min(similar_entries.mapped('sequence'))
        max_sequence = max(similar_entries.mapped('sequence'))

        if self.sequence == min_sequence:
            similar_entries_to_approve = similar_entries.filtered(lambda e: e.sequence == self.sequence and e.status == '2')
            for entry in similar_entries_to_approve:
                entry.approval_id.action_approve()
                entry.write({
                    'status': '5',
                    'approved_by': self.env.user.id,
                    'approved_date': fields.Date.today()
                })
        else:
            similar_entries_to_approve = similar_entries.filtered(lambda e: e.sequence >= self.sequence and e.status == '2')
            for entry in similar_entries_to_approve:
                previous_approvals = similar_entries.filtered(lambda e: e.sequence < entry.sequence and e.status != '5')
                if previous_approvals:
                    raise UserError('Previous approvals are not yet completed for entry sequence %s.' % entry.sequence)
                else:
                    entry.approval_id.action_approve()
                    entry.write({
                        'status': '5',
                        'approved_by': self.env.user.id,
                        'approved_date': fields.Date.today()
                    })

    def action_reject_entry(self):
        """
        This method will reject the entry. If the entry is the first entry in the sequence, it will reject all entries"""
        self.ensure_one()
        if self.status != '2':
            raise UserError(_('Only pending approval entries can be rejected.'))

        # Query to get all entries related to the same document and their sequences
        self.env.cr.execute("""
            SELECT id, sequence, status 
            FROM payroll_approval_entries
            WHERE document_id = %s
            ORDER BY sequence
        """, (self.document_id.id,))

        record_data = self.env.cr.fetchall()

        if self.sequence == record_data[0][1]:
            for entry_id, _, _ in record_data:
                entry = self.env['payroll.approval.entries'].browse(entry_id)
                entry.approval_id.action_reject(self.reason)
                entry.write({
                    'status': '3',  # Rejected status
                    'approved_by': self.env.user.id,
                    'approved_date': fields.Date.today(),
                    'reason': self.reason or entry.reason
                })
        else:
            for entry_id, sequence, status in record_data:
                if sequence >= self.sequence:
                    entry = self.env['payroll.approval.entries'].browse(entry_id)
                    previous_approvals = [e for e in record_data if e[1] < sequence and e[2] != '5']  # Filter entries before the current one that are not approved
                    
                    if previous_approvals:
                        raise UserError(_('Previous approvals are not yet completed for entry sequence %s.' % sequence))
                    else:
                        entry.approval_id.action_reject(self.reason)
                        entry.write({
                            'status': '3',  # Rejected status
                            'approved_by': self.env.user.id,
                            'approved_date': fields.Date.today(),
                            'reason': self.reason or entry.reason
                        })

